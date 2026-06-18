# stt.py
"""
Распознавание речи (Speech-to-Text)
Улучшенная версия: автоусиление, шумоподавление, VAD
"""
import pyaudio
import numpy as np
import sys
import time
import os


class VoiceRecognizer:
    """Распознаватель речи с улучшенным качеством."""
    
    def __init__(self, model_size="medium", device="auto", compute_type="auto"):
        self.model_size = model_size
        
        # Автоопределение GPU
        if device == "auto":
            self.device = self._detect_gpu()
        else:
            self.device = device
        
        if compute_type == "auto":
            self.compute_type = "float16" if self.device == "cuda" else "int8"
        else:
            self.compute_type = compute_type
        
        # Параметры аудио — 16 кГц для Whisper
        self.RATE = 16000
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        # VAD — автонастройка под микрофон
        self.silence_threshold = 200      # Начальный порог (автонастройка)
        self.silence_frames_stop = 20     # 1.3 сек тишины = конец
        self.max_record_frames = 250      # ~16 сек макс
        self.min_speech_frames = 5        # 0.3 сек минимум
        self.padding_frames = 10          # Захват до речи
        
        # Автонастройка уровня шума
        self.noise_level = 100
        self.noise_samples = []
        self.calibrated = False
        
        # Загружаем модель
        self.model = None
        self._load_model()
        
        # Аудио
        self.audio = pyaudio.PyAudio()
    
    def _detect_gpu(self):
        """Определяет наличие видеокарты."""
        try:
            import torch
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                print(f"  ✓ GPU: {name} ({mem:.1f} ГБ)")
                return "cuda"
        except:
            pass
        print("  ℹ CPU")
        return "cpu"
    
    def _load_model(self):
        """Загружает модель Whisper."""
        print(f"  Загрузка «{self.model_size}» на {self.device.upper()}...")
        
        try:
            from faster_whisper import WhisperModel
            
            if self.device == "cuda":
                self.model = WhisperModel(
                    self.model_size, device="cuda", compute_type=self.compute_type
                )
            else:
                self.model = WhisperModel(
                    self.model_size, device="cpu", compute_type="int8",
                    cpu_threads=os.cpu_count() or 4, num_workers=2
                )
            print(f"  ✓ Готово")
            
        except ImportError:
            print("  ✗ pip install faster-whisper")
            sys.exit(1)
        except Exception as e:
            print(f"  ✗ Ошибка: {e}")
            fallbacks = {"large-v3": "medium", "medium": "small", "small": "base", "base": "tiny"}
            if self.model_size in fallbacks:
                fallback = fallbacks[self.model_size]
                print(f"  Пробую «{fallback}»...")
                try:
                    from faster_whisper import WhisperModel
                    self.model = WhisperModel(fallback, device=self.device, compute_type=self.compute_type)
                    self.model_size = fallback
                    print(f"  ✓ «{fallback}»")
                except:
                    sys.exit(1)
    
    def _calibrate_noise(self, audio_chunk):
        """Автонастройка уровня шума."""
        if not self.calibrated:
            self.noise_samples.append(audio_chunk)
            if len(self.noise_samples) >= 30:  # 2 секунды
                all_noise = np.concatenate(self.noise_samples)
                self.noise_level = np.mean(np.abs(all_noise))
                self.silence_threshold = self.noise_level * 3.0
                self.calibrated = True
                print(f"  ✓ Микрофон откалиброван (шум: {self.noise_level:.0f}, порог: {self.silence_threshold:.0f})")
    
    def _normalize_audio(self, audio):
        """Нормализация и усиление тихого аудио."""
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < 0.001:
            return audio
        
        # Целевой уровень
        target_rms = 0.2
        gain = target_rms / rms
        
        # Ограничиваем усиление
        gain = min(gain, 10.0)
        
        audio = audio * gain
        audio = np.clip(audio, -1.0, 1.0)
        
        return audio
    
    def _reduce_noise(self, audio):
        """Простое шумоподавление: спектральное вычитание."""
        if len(audio) < 1024:
            return audio
        
        # Берём первые 100 мс как шум
        noise_len = min(len(audio) // 4, int(0.1 * self.RATE))
        noise = audio[:noise_len]
        
        if len(noise) < 256:
            return audio
        
        # Спектр шума
        noise_spec = np.abs(np.fft.rfft(noise * np.hanning(len(noise))))
        noise_mean = np.mean(noise_spec)
        
        # Обрабатываем сигнал окнами
        window_size = 1024
        hop = 512
        result = np.zeros_like(audio)
        weights = np.zeros_like(audio)
        
        for i in range(0, len(audio) - window_size, hop):
            window = audio[i:i+window_size] * np.hanning(window_size)
            spec = np.fft.rfft(window)
            mag = np.abs(spec)
            phase = np.angle(spec)
            
            # Вычитание шума
            mag = np.maximum(mag - noise_mean * 0.5, 0)
            
            # Восстановление
            new_spec = mag * np.exp(1j * phase)
            new_window = np.fft.irfft(new_spec)
            
            result[i:i+window_size] += new_window
            weights[i:i+window_size] += 1
        
        # Нормализация перекрытия
        weights = np.maximum(weights, 1)
        result = result / weights
        
        return result
    
    def listen(self, timeout=8):
        """Слушает и распознаёт речь."""
        stream = self.audio.open(
            format=self.FORMAT, channels=self.CHANNELS,
            rate=self.RATE, input=True, frames_per_buffer=self.CHUNK
        )
        
        print("🎤 Слушаю...", end="", flush=True)
        
        frames = []
        speaking = False
        silence_count = 0
        speech_count = 0
        max_volume = 0
        
        pre_buffer = []
        
        try:
            while len(frames) < self.max_record_frames:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                
                chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                volume = np.abs(chunk).mean()
                max_volume = max(max_volume, volume)
                
                # Калибровка
                self._calibrate_noise(chunk)
                
                if volume > self.silence_threshold:
                    if not speaking:
                        frames.extend(pre_buffer)
                        pre_buffer.clear()
                        speaking = True
                        print(" ▼", end="", flush=True)
                    
                    speech_count += 1
                    silence_count = 0
                    frames.append(data)
                else:
                    if not speaking:
                        pre_buffer.append(data)
                        if len(pre_buffer) > self.padding_frames:
                            pre_buffer.pop(0)
                    else:
                        silence_count += 1
                        frames.append(data)
                        
                        if speech_count >= self.min_speech_frames and silence_count >= self.silence_frames_stop:
                            print(" ■", end="", flush=True)
                            break
        except Exception as e:
            print(f" ⚠", flush=True)
        finally:
            stream.stop_stream()
            stream.close()
        
        if speaking and silence_count > 0:
            frames = frames[:-silence_count]
        
        dur = len(frames) * self.CHUNK / self.RATE
        
        if not frames or speech_count < self.min_speech_frames:
            print(f" ✗", flush=True)
            return ""
        
        print(f" {dur:.1f}с", flush=True)
        
        # Декодируем
        audio_bytes = b''.join(frames)
        audio_float = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Улучшение качества
        audio_float = self._reduce_noise(audio_float)     # Шумоподавление
        audio_float = self._normalize_audio(audio_float)   # Нормализация
        
        return self._transcribe(audio_float)
    
    def _transcribe(self, audio):
        """Распознаёт речь с улучшенными параметрами."""
        try:
            print("🧠 ...", end="", flush=True)
            start = time.time()
            
            # Параметры для лучшего качества
            segments, info = self.model.transcribe(
                audio,
                language="ru",
                beam_size=5,                    # Ширина поиска
                best_of=5,                      # Количество гипотез
                temperature=[0.0, 0.2, 0.4],   # Несколько температур
                compression_ratio_threshold=2.4, # Фильтр мусора
                log_prob_threshold=-1.0,         # Порог вероятности
                no_speech_threshold=0.6,         # Порог тишины
                condition_on_previous_text=True,  # Контекст
                word_timestamps=False,           # Быстрее без меток
                vad_filter=True,                 # Фильтр тишины
                vad_parameters={
                    "threshold": 0.4,
                    "min_speech_duration_ms": 150,
                    "min_silence_duration_ms": 400,
                    "speech_pad_ms": 200
                }
            )
            
            words = []
            for seg in segments:
                text = seg.text.strip()
                if text:
                    words.append(text)
            
            result = " ".join(words).strip()
            elapsed = time.time() - start
            
            if result:
                print(f" ✓ «{result}» ({elapsed:.1f}с)", flush=True)
            else:
                # Повторная попытка с другими параметрами
                print(" ↻", end="", flush=True)
                segments, _ = self.model.transcribe(
                    audio,
                    language="ru",
                    beam_size=5,
                    temperature=0.0,
                    compression_ratio_threshold=1.8,
                    log_prob_threshold=-2.0,
                    no_speech_threshold=0.4,
                    condition_on_previous_text=False
                )
                
                words = []
                for seg in segments:
                    if seg.text.strip():
                        words.append(seg.text.strip())
                
                result = " ".join(words).strip()
                elapsed = time.time() - start
                
                if result:
                    print(f" ✓ «{result}» ({elapsed:.1f}с)", flush=True)
                else:
                    print(f" ✗ ({elapsed:.1f}с)", flush=True)
            
            return result
            
        except Exception as e:
            print(f" ✗ {e}", flush=True)
            return ""
    
    def info(self):
        return {
            "model": self.model_size,
            "device": self.device.upper(),
            "compute": self.compute_type
        }
    
    def close(self):
        try:
            self.audio.terminate()
        except:
            pass
        
        if self.device == "cuda":
            try:
                import torch
                torch.cuda.empty_cache()
            except:
                pass


# ============================================================
# ТЕСТ
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  ТЕСТ РАСПОЗНАВАНИЯ")
    print("=" * 50)
    
    rec = VoiceRecognizer(model_size="small")
    print(f"  {rec.info()}\n")
    
    try:
        while True:
            input("▶ ")
            text = rec.listen()
            if text:
                print(f"  ➤ {text}\n")
    except KeyboardInterrupt:
        print("\n  Выход.")
    
    rec.close()