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
    Детектор голосовой активации.
    Исправленная версия с нормальным VAD.
    """
    
    def __init__(self, wake_word="джарвис", sensitivity=0.6, debug=False):
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
        self.custom_threshold = 0.6
        self.load_custom_model()
        
        # Буферы
        self.audio_buffer = deque(maxlen=int(self.RATE / self.CHUNK * 2.0))
        self.energy_history = deque(maxlen=100)
        
        # Параметры VAD — ИСПРАВЛЕНО
        self.speech_energy_multiplier = 4.0  # Порог речи = шум * 4 (было 3.5)
        self.min_speech_frames = 8           # Минимум 0.5 сек речи
        self.max_speech_frames = 50          # Максимум 3 сек речи (отсекаем длинное)
        self.silence_frames_stop = 15        # 1 сек тишины = конец слова
        
        # Состояние
        self.running = False
        self.audio = None
        self.stream = None
        self.listen_thread = None
        self.detection_callbacks = []
        
        self.last_detection_time = 0
        self.cooldown_period = 2.0
        
        if self.custom_model:
            print(f"✓ Модель загружена (порог: {self.custom_threshold:.3f})")
        else:
            print("! Модель не найдена. Запустите train_wakeword.py")
    
    def load_custom_model(self):
        model_path = f"models/{self.wake_word}_model.json"
        if os.path.exists(model_path):
            try:
                with open(model_path, 'r', encoding='utf-8') as f:
                    self.custom_model = json.load(f)
                if 'threshold' in self.custom_model:
                    self.custom_threshold = self.custom_model['threshold']
                return True
            except:
                pass
        return False
    
    def save_custom_model(self):
        os.makedirs("models", exist_ok=True)
        model_path = f"models/{self.wake_word}_model.json"
        try:
            self.custom_model['threshold'] = self.custom_threshold
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(self.custom_model, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def extract_features(self, audio_segment):
        if len(audio_segment) < 512:
            return None
        
        audio = audio_segment.astype(np.float32)
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
        
        features = {}
        
        # Базовые
        features['duration'] = len(audio) / self.RATE
        features['rms_energy'] = float(np.sqrt(np.mean(audio**2)))
        features['peak_energy'] = float(np.max(np.abs(audio)))
        features['zcr'] = float(np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio)))
        
        # Спектр
        n_fft = min(1024, len(audio))
        fft = np.abs(np.fft.rfft(audio[:n_fft] * np.hanning(n_fft)))
        freqs = np.fft.rfftfreq(n_fft, 1/self.RATE)
        
        if np.sum(fft) > 0:
            features['spectral_centroid'] = float(np.sum(freqs * fft) / np.sum(fft))
        else:
            features['spectral_centroid'] = 0.0
        
        cumsum = np.cumsum(fft)
        if cumsum[-1] > 0:
            idx = np.where(cumsum >= 0.85 * cumsum[-1])[0]
            features['spectral_rolloff'] = float(freqs[idx[0]]) if len(idx) > 0 else 0.0
        else:
            features['spectral_rolloff'] = 0.0
        
        # Мел-полосы
        n_mels = 16
        def hz_to_mel(hz): return 2595 * np.log10(1 + hz/700)
        def mel_to_hz(mel): return 700 * (10**(mel/2595) - 1)
        
        min_mel = hz_to_mel(0)
        max_mel = hz_to_mel(self.RATE/2)
        mel_points = np.linspace(min_mel, max_mel, n_mels+2)
        hz_points = mel_to_hz(mel_points)
        bin_idx = np.clip(np.floor((n_fft+1) * hz_points / self.RATE).astype(int), 0, len(fft)-1)
        
        for i in range(n_mels):
            if bin_idx[i] < bin_idx[i+2]:
                features[f'mel_{i}'] = float(np.sum(fft[bin_idx[i]:bin_idx[i+2]]))
        
        # Пики
        peaks = np.argsort(fft)[-3:]
        for i, p in enumerate(peaks):
            if p < len(freqs):
                features[f'peak_{i}_freq'] = float(freqs[p])
        
        return features
    
    def compare_features(self, test, model):
        if not test or not model:
            return 0.0
        
        ignore = {'threshold', 'count', 'min', 'max'}
        common = (set(test.keys()) & set(model.keys())) - ignore
        
        if len(common) < 5:
            return 0.0
        
        scores = []
        for key in common:
            tv = test[key]
            ms = model[key]
            if isinstance(ms, dict) and 'mean' in ms:
                mean = ms['mean']
                std = ms.get('std', 1.0)
                if std > 0:
                    dev = abs(tv - mean) / (std + 1e-6)
                    scores.append(np.exp(-dev * 2.0))  # Строже
        
        return float(np.mean(scores)) if scores else 0.0
    
    def record_samples(self, num_samples=8):
        print(f"\n{'='*50}")
        print(f"  ЗАПИСЬ ОБРАЗЦОВ: «{self.wake_word}»")
        print(f"{'='*50}")
        print("\n  ВАЖНО:")
        print("  • Полная тишина")
        print("  • Говорите ТОЛЬКО слово, без пауз до и после")
        print("  • Одинаковая громкость и интонация")
        print(f"\n  Будет записано {num_samples} образцов")
        input("\n  Нажмите Enter...")
        
        self.audio = pyaudio.PyAudio()
        samples = []
        
        for i in range(num_samples):
            print(f"\n  Образец {i+1}/{num_samples}")
            for c in [2, 1]:
                print(f"  {c}...")
                time.sleep(0.7)
            print("  ▶ ГОВОРИТЕ!")
            
            stream = self.audio.open(
                format=self.FORMAT, channels=self.CHANNELS,
                rate=self.RATE, input=True, frames_per_buffer=self.CHUNK
            )
            
            frames = []
            # Записываем 2 секунды
            for _ in range(int(self.RATE / self.CHUNK * 2.0)):
                try:
                    frames.append(stream.read(self.CHUNK, exception_on_overflow=False))
                except:
                    break
            stream.stop_stream()
            stream.close()
            
            if frames:
                audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
                
                # Обрезаем тишину
                energy = np.abs(audio_data)
                thresh = np.mean(energy) * 2.0
                mask = energy > thresh
                
                if np.any(mask):
                    idx = np.where(mask)[0]
                    margin = int(0.1 * self.RATE)
                    start = max(0, idx[0] - margin)
                    end = min(len(audio_data), idx[-1] + margin)
                    audio_data = audio_data[start:end]
                
                dur = len(audio_data) / self.RATE
                if 0.2 < dur < 2.0:
                    features = self.extract_features(audio_data)
                    if features:
                        samples.append(features)
                        print(f"  ✓ Записано ({dur:.1f}с)")
                    else:
                        print(f"  ✗ Нет признаков")
                else:
                    print(f"  ✗ Длительность {dur:.1f}с (нужно 0.2-2.0)")
            
            time.sleep(0.3)
        
        self.audio.terminate()
        self.audio = None
        
        if len(samples) < 4:
            print(f"\n  ✗ Мало образцов: {len(samples)}")
            return False
        
        # Создаём модель
        self.custom_model = {}
        all_keys = set()
        for s in samples:
            all_keys.update(s.keys())
        
        for key in all_keys:
            vals = [s[key] for s in samples if key in s]
            if len(vals) >= 3:
                self.custom_model[key] = {
                    'mean': float(np.mean(vals)),
                    'std': float(np.std(vals))
                }
        
        # Проверка
        scores = []
        for s in samples:
            sc = self.compare_features(s, self.custom_model)
            scores.append(sc)
            print(f"  Score: {sc:.4f}")
        
        avg = np.mean(scores)
        self.custom_threshold = max(0.5, min(0.8, avg * 0.85))
        print(f"\n  Средний score: {avg:.4f}")
        print(f"  Порог: {self.custom_threshold:.4f}")
        
        self.save_custom_model()
        return True
    
    def on_detected(self, callback):
        self.detection_callbacks.append(callback)
    
    def _trigger(self):
        now = time.time()
        if now - self.last_detection_time < self.cooldown_period:
            return
        self.last_detection_time = now
        print("\n🔔 АКТИВАЦИЯ!")
        for cb in self.detection_callbacks:
            cb()
    
    def start_listening(self):
        self.audio = pyaudio.PyAudio()
        self.running = True
        
        self.stream = self.audio.open(
            format=self.FORMAT, channels=self.CHANNELS,
            rate=self.RATE, input=True, frames_per_buffer=self.CHUNK
        )
        
        self.listen_thread = threading.Thread(target=self._loop, daemon=True)
        self.listen_thread.start()
        print(f"Слушаю... (порог: {self.custom_threshold:.3f})")
    
    def _loop(self):
        # VAD состояние
        speaking = False
        speech_frames = 0
        silence_frames = 0
        buffer = []
        
        while self.running:
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                chunk = np.frombuffer(data, dtype=np.int16)
                self.audio_buffer.append(chunk)
                
                energy = np.sqrt(np.mean(chunk.astype(np.float32)**2))
                self.energy_history.append(energy)
                
                # Адаптивный порог: медиана шума * множитель
                if len(self.energy_history) > 30:
                    noise_level = np.median(list(self.energy_history))
                    threshold = max(100, noise_level * self.speech_energy_multiplier)
                else:
                    threshold = 150
                
                is_speech = energy > threshold
                
                if is_speech:
                    if not speaking:
                        speaking = True
                        # Берём контекст до речи
                        buffer = list(self.audio_buffer)[-5:]
                        if self.debug:
                            print(f"\n🎤 Речь (e={energy:.0f}, thr={threshold:.0f})")
                    
                    speech_frames += 1
                    silence_frames = 0
                    buffer.append(chunk)
                    
                    # Слишком длинный сегмент — сбрасываем
                    if speech_frames > self.max_speech_frames:
                        if self.debug:
                            print(f"  ⏭ Слишком длинно ({speech_frames*self.CHUNK/self.RATE:.1f}с), сброс")
                        speaking = False
                        speech_frames = 0
                        silence_frames = 0
                        buffer = []
                        
                elif speaking:
                    silence_frames += 1
                    buffer.append(chunk)
                    
                    # Достаточно тишины — анализируем
                    if silence_frames >= self.silence_frames_stop:
                        dur = len(buffer) * self.CHUNK / self.RATE
                        
                        # Проверяем длительность
                        if self.min_speech_frames <= speech_frames <= self.max_speech_frames:
                            segment = np.concatenate(buffer)
                            
                            if self.custom_model:
                                features = self.extract_features(segment)
                                if features:
                                    score = self.compare_features(features, self.custom_model)
                                    
                                    if self.debug:
                                        marker = " ✓АКТИВАЦИЯ!" if score > self.custom_threshold else ""
                                        print(f"  Анализ: score={score:.4f} (порог={self.custom_threshold:.3f}, dur={dur:.1f}с){marker}")
                                    
                                    if score > self.custom_threshold:
                                        self._trigger()
                            elif self.debug:
                                print(f"  Голос обнаружен (dur={dur:.1f}с), но нет модели")
                        elif self.debug:
                            print(f"  Пропущено: длительность {dur:.1f}с (диапазон 0.5-3.0с)")
                        
                        # Сброс
                        speaking = False
                        speech_frames = 0
                        silence_frames = 0
                        buffer = []
                        
            except Exception as e:
                if self.debug:
                    print(f"Ошибка: {e}")
                time.sleep(0.1)
    
    def stop(self):
        self.running = False
        time.sleep(0.3)
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()