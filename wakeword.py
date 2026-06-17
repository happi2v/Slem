# wakeword.py
import pyaudio
import numpy as np
import threading
import time
import os
import json
from collections import deque

class VoiceWakeWord:
    """
    Детектор голосовой активации с защитой от ложных срабатываний.
    """
    
    def __init__(self, wake_word="джарвис", sensitivity=0.7, debug=False):
        self.wake_word = wake_word.lower()
        self.sensitivity = sensitivity
        self.debug = debug
        
        # Параметры аудио
        self.RATE = 16000
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        # Модель
        self.custom_model = None
        self.custom_threshold = 0.75  # ВЫСОКИЙ порог по умолчанию
        self.load_custom_model()
        
        # Если модель загружена, но порог низкий — поднимаем
        if self.custom_model and self.custom_threshold < 0.7:
            self.custom_threshold = 0.75
        
        # Буферы
        self.audio_buffer = deque(maxlen=int(self.RATE / self.CHUNK * 2.0))
        self.energy_history = deque(maxlen=100)
        
        # ЖЁСТКИЕ ПАРАМЕТРЫ VAD
        self.MIN_VOICE_FRAMES = 12      # Минимум 0.75 сек речи (было 5)
        self.MAX_SILENCE_FRAMES = 15    # Максимум 0.9 сек тишины (было 20)
        self.SPEECH_ENERGY_MULTIPLIER = 3.5  # Выше порог речи (было 2.5)
        
        # Защита от ложных срабатываний
        self.MIN_SEGMENT_LENGTH = 8000   # Минимум 0.5 сек аудио
        self.MAX_SEGMENT_LENGTH = 48000  # Максимум 3 сек аудио
        
        # Состояние
        self.voice_segment = []
        self.running = False
        self.audio = None
        self.stream = None
        self.listen_thread = None
        self.detection_callbacks = []
        
        # Кулдаун
        self.last_detection_time = 0
        self.cooldown_period = 2.5  # 2.5 секунды между срабатываниями
        
        # Счётчик последовательных обнаружений для фильтрации
        self.consecutive_detections = 0
        self.REQUIRED_CONSECUTIVE = 1  # Сколько раз подряд нужно обнаружить
        
        if self.debug:
            print("=" * 50)
            print("РЕЖИМ ОТЛАДКИ АКТИВИРОВАН")
            print(f"Порог: {self.custom_threshold:.3f}")
            print("=" * 50)
        
        if self.custom_model:
            print(f"✓ Модель для '{self.wake_word}' загружена (порог: {self.custom_threshold:.3f})")
        else:
            print(f"! Модель не найдена. Запустите train_wakeword.py")
    
    def load_custom_model(self):
        """Загружает модель."""
        model_path = f"models/{self.wake_word}_model.json"
        if os.path.exists(model_path):
            try:
                with open(model_path, 'r', encoding='utf-8') as f:
                    self.custom_model = json.load(f)
                # Загружаем сохранённый порог если есть
                if 'threshold' in self.custom_model:
                    self.custom_threshold = self.custom_model['threshold']
                return True
            except Exception as e:
                print(f"Ошибка загрузки: {e}")
        return False
    
    def save_custom_model(self):
        """Сохраняет модель с порогом."""
        os.makedirs("models", exist_ok=True)
        model_path = f"models/{self.wake_word}_model.json"
        try:
            # Сохраняем порог вместе с моделью
            self.custom_model['threshold'] = self.custom_threshold
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_model, f, indent=2, ensure_ascii=False)
            print(f"Модель сохранена: {model_path}")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
    
    def extract_features(self, audio_segment):
        """Извлекает признаки из аудио."""
        if len(audio_segment) < 512:
            return None
        
        audio = audio_segment.astype(np.float32)
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
        
        features = {}
        
        # Энергетические характеристики
        features['rms_energy'] = float(np.sqrt(np.mean(audio**2)))
        features['peak_energy'] = float(np.max(np.abs(audio)))
        features['energy_std'] = float(np.std(audio**2))
        
        # Zero-crossing rate
        zcr = np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio))
        features['zcr'] = float(zcr)
        
        # Длительность (важный признак!)
        features['duration'] = len(audio) / self.RATE
        
        # Спектральные характеристики
        n_fft = min(1024, len(audio))
        fft = np.abs(np.fft.rfft(audio[:n_fft] * np.hanning(n_fft)))
        freqs = np.fft.rfftfreq(n_fft, 1/self.RATE)
        
        if np.sum(fft) > 0:
            features['spectral_centroid'] = float(np.sum(freqs * fft) / np.sum(fft))
        else:
            features['spectral_centroid'] = 0.0
        
        cumsum = np.cumsum(fft)
        if cumsum[-1] > 0:
            rolloff_idx = np.where(cumsum >= 0.85 * cumsum[-1])[0]
            features['spectral_rolloff'] = float(freqs[rolloff_idx[0]]) if len(rolloff_idx) > 0 else 0.0
        else:
            features['spectral_rolloff'] = 0.0
        
        features['spectral_flux'] = float(np.sum(np.diff(fft)**2))
        
        # Мел-полосные энергии
        n_mels = 16
        
        def hz_to_mel(hz):
            return 2595 * np.log10(1 + hz / 700)
        
        def mel_to_hz(mel):
            return 700 * (10**(mel / 2595) - 1)
        
        min_mel = hz_to_mel(0)
        max_mel = hz_to_mel(self.RATE / 2)
        mel_points = np.linspace(min_mel, max_mel, n_mels + 2)
        hz_points = mel_to_hz(mel_points)
        bin_indices = np.floor((n_fft + 1) * hz_points / self.RATE).astype(int)
        bin_indices = np.clip(bin_indices, 0, len(fft) - 1)
        
        for i in range(n_mels):
            start = bin_indices[i]
            end = bin_indices[i + 2]
            if start < end:
                features[f'mel_band_{i}'] = float(np.sum(fft[start:end]))
        
        # Пики спектра (топ-3)
        peak_indices = np.argsort(fft)[-3:]
        for i, idx in enumerate(peak_indices):
            if idx < len(freqs):
                features[f'peak_{i}_freq'] = float(freqs[idx])
                features[f'peak_{i}_mag'] = float(fft[idx])
        
        return features
    
    def compare_features(self, test_features, model_features):
        """
        Сравнивает признаки с моделью.
        Возвращает оценку схожести от 0 до 1.
        """
        if not test_features or not model_features:
            return 0.0
        
        # Игнорируем служебные ключи
        ignore_keys = {'threshold', 'count', 'min', 'max'}
        common_keys = (set(test_features.keys()) & set(model_features.keys())) - ignore_keys
        
        if len(common_keys) < 5:
            return 0.0
        
        scores = []
        weights = []
        
        # Ключевые признаки с повышенным весом
        important_features = ['rms_energy', 'zcr', 'spectral_centroid', 'duration', 
                              'mel_band_2', 'mel_band_5', 'mel_band_8', 'peak_0_freq']
        
        for key in common_keys:
            test_val = test_features[key]
            model_stats = model_features[key]
            
            if isinstance(model_stats, dict) and 'mean' in model_stats:
                mean = model_stats['mean']
                std = model_stats.get('std', 1.0)
                
                if std > 0:
                    deviation = abs(test_val - mean) / (std + 1e-6)
                    score = np.exp(-deviation * 1.5)  # Более строгое наказание за отклонение
                    
                    # Повышенный вес для важных признаков
                    weight = 2.0 if key in important_features else 1.0
                    weight = weight / (std + 0.1)
                    
                    scores.append(score)
                    weights.append(weight)
        
        if not scores:
            return 0.0
        
        total_weight = sum(weights)
        if total_weight > 0:
            final_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        else:
            final_score = np.mean(scores)
        
        return float(final_score)
    
    def record_samples(self, num_samples=10):
        """Записывает образцы голоса для обучения."""
        print(f"\n{'='*50}")
        print(f"ЗАПИСЬ ОБРАЗЦОВ ДЛЯ СЛОВА '{self.wake_word}'")
        print(f"{'='*50}")
        print(f"\n⚡ ВАЖНО ДЛЯ ТОЧНОЙ МОДЕЛИ:")
        print("  1. Полная тишина в помещении")
        print("  2. Говорите ТОЛЬКО слово, без лишних звуков")
        print("  3. Одинаковая громкость и интонация ВСЕГДА")
        print("  4. Микрофон на расстоянии 15-20 см")
        print(f"  5. Не меняйте положение относительно микрофона")
        print(f"\nБудет записано {num_samples} образцов")
        
        input("\nНажмите Enter для начала...")
        
        self.audio = pyaudio.PyAudio()
        samples = []
        
        for i in range(num_samples):
            print(f"\n--- Образец {i+1}/{num_samples} ---")
            
            for countdown in [3, 2, 1]:
                print(f"  {countdown}...")
                time.sleep(0.8)
            
            print("  ▶ ГОВОРИТЕ!")
            
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            frames = []
            for _ in range(0, int(self.RATE / self.CHUNK * 2.5)):
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)
                except:
                    break
            
            stream.stop_stream()
            stream.close()
            
            if frames:
                audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
                
                # Удаляем тишину
                energy = np.abs(audio_data)
                threshold = np.mean(energy) * 2.0
                voice_mask = energy > threshold
                
                if np.any(voice_mask):
                    voice_indices = np.where(voice_mask)[0]
                    margin = int(0.15 * self.RATE)
                    start_idx = max(0, voice_indices[0] - margin)
                    end_idx = min(len(audio_data), voice_indices[-1] + margin)
                    audio_data = audio_data[start_idx:end_idx]
                
                # Проверяем длительность
                duration = len(audio_data) / self.RATE
                if 0.3 < duration < 2.0:  # Слово должно быть от 0.3 до 2 сек
                    features = self.extract_features(audio_data)
                    if features:
                        samples.append(features)
                        print(f"  ✓ Записан ({duration:.1f} сек)")
                    else:
                        print(f"  ✗ Не удалось извлечь признаки")
                else:
                    print(f"  ✗ Неверная длительность: {duration:.1f} сек (нужно 0.3-2.0)")
            else:
                print(f"  ✗ Нет данных")
            
            time.sleep(0.3)
        
        self.audio.terminate()
        self.audio = None
        
        if len(samples) < 5:
            print(f"\n✗ Мало образцов: {len(samples)}. Нужно минимум 5.")
            return False
        
        # Создаём модель
        print(f"\nСоздание модели из {len(samples)} образцов...")
        
        self.custom_model = {}
        all_keys = set()
        for sample in samples:
            all_keys.update(sample.keys())
        
        for key in all_keys:
            values = []
            for sample in samples:
                if key in sample:
                    values.append(sample[key])
            if len(values) >= 3:
                self.custom_model[key] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values))
                }
        
        print(f"  Создано признаков: {len(self.custom_model)}")
        
        # Проверяем качество
        print("\nПроверка на обучающих образцах:")
        scores = []
        for i, sample in enumerate(samples):
            score = self.compare_features(sample, self.custom_model)
            scores.append(score)
            status = "✓" if score > 0.75 else "⚠" if score > 0.6 else "✗"
            print(f"  {status} Образец {i+1}: score = {score:.4f}")
        
        avg_score = np.mean(scores)
        min_score = np.min(scores)
        
        print(f"\nСредний score: {avg_score:.4f}")
        print(f"Минимальный score: {min_score:.4f}")
        
        # Устанавливаем ВЫСОКИЙ порог
        self.custom_threshold = max(0.75, min_score * 0.85)
        print(f"Установлен порог: {self.custom_threshold:.4f}")
        
        self.save_custom_model()
        
        if avg_score < 0.6:
            print("\n⚠ Низкое качество! Обязательно:")
            print("  - Записывайте в полной тишине")
            print("  - Не двигайтесь во время записи")
            print("  - Произносите слово одинаково ВСЕ образцы")
        else:
            print("\n✓ Модель хорошего качества!")
        
        return True
    
    def on_detected(self, callback):
        """Регистрирует callback."""
        self.detection_callbacks.append(callback)
    
    def _trigger(self):
        """Вызывает callback при обнаружении с защитой от повторов."""
        current_time = time.time()
        
        # Проверяем кулдаун
        if current_time - self.last_detection_time < self.cooldown_period:
            if self.debug:
                print(f"  ⏳ Кулдаун, пропускаю ({(current_time - self.last_detection_time):.1f}с)")
            return
        
        self.last_detection_time = current_time
        print("\n🔔 АКТИВАЦИЯ! Обнаружено ключевое слово!")
        
        for callback in self.detection_callbacks:
            callback()
    
    def _get_energy(self, audio_chunk):
        """RMS энергия."""
        return np.sqrt(np.mean(audio_chunk.astype(np.float32)**2))
    
    def _listen_loop(self):
        """Основной цикл с улучшенной фильтрацией."""
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        voice_detected = False
        voice_frames_count = 0
        silence_after_voice = 0
        voice_buffer = []
        
        # Для фильтрации шумов
        noise_spike_count = 0
        
        if self.debug:
            print(f"🔍 Слушаю... (порог: {self.custom_threshold:.3f})")
        else:
            print(f"Слушаю... (порог: {self.custom_threshold:.3f})")
        
        while self.running:
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                
                self.audio_buffer.append(audio_chunk)
                
                energy = self._get_energy(audio_chunk)
                self.energy_history.append(energy)
                
                # Адаптивный порог речи
                if len(self.energy_history) > 30:
                    noise_level = np.percentile(list(self.energy_history), 15)  # 15 перцентиль для лучшей оценки шума
                    speech_threshold = noise_level * self.SPEECH_ENERGY_MULTIPLIER
                else:
                    speech_threshold = 200.0
                
                is_speech = energy > speech_threshold
                
                # Фильтрация коротких шумовых всплесков
                if is_speech and not voice_detected:
                    noise_spike_count += 1
                    if noise_spike_count < 4:  # Игнорируем всплески короче 4 чанков
                        continue
                
                if is_speech:
                    if not voice_detected:
                        voice_detected = True
                        context = list(self.audio_buffer)[-8:]  # Больше контекста
                        voice_buffer = context.copy()
                        if self.debug:
                            print(f"\n🎤 Речь (energy={energy:.0f}, threshold={speech_threshold:.0f})")
                    
                    voice_frames_count += 1
                    silence_after_voice = 0
                    voice_buffer.append(audio_chunk)
                    noise_spike_count = 0
                    
                elif voice_detected:
                    silence_after_voice += 1
                    voice_buffer.append(audio_chunk)
                    
                    if (voice_frames_count >= self.MIN_VOICE_FRAMES and 
                        silence_after_voice >= self.MAX_SILENCE_FRAMES):
                        
                        if len(voice_buffer) > self.MIN_VOICE_FRAMES:
                            segment = np.concatenate(voice_buffer)
                            
                            # Проверяем длительность сегмента
                            segment_duration = len(segment) / self.RATE
                            
                            # Фильтруем по длительности (слово обычно 0.3-1.5 сек)
                            if 0.3 < segment_duration < 2.0:
                                if self.custom_model:
                                    features = self.extract_features(segment)
                                    if features:
                                        similarity = self.compare_features(features, self.custom_model)
                                        
                                        if self.debug:
                                            marker = " ← АКТИВАЦИЯ!" if similarity > self.custom_threshold else ""
                                            print(f"  Анализ: score={similarity:.4f} (порог={self.custom_threshold:.3f}, длит={segment_duration:.1f}с){marker}")
                                        
                                        if similarity > self.custom_threshold:
                                            self._trigger()
                                else:
                                    print("  ⚠ Модель не обучена!")
                            elif self.debug:
                                print(f"  Пропущено: длительность {segment_duration:.1f}с (вне диапазона 0.3-2.0)")
                        
                        # Сброс
                        voice_detected = False
                        voice_frames_count = 0
                        silence_after_voice = 0
                        voice_buffer = []
                        noise_spike_count = 0
                        
            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(0.1)
    
    def start_listening(self):
        """Запускает прослушивание."""
        if self.running:
            return
        
        self.running = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
    
    def stop(self):
        """Останавливает."""
        self.running = False
        time.sleep(0.3)
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass