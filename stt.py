# stt.py
import pyaudio
import numpy as np
import os
import sys

class VoiceRecognizer:
    """Распознаватель речи на базе Faster-Whisper с поддержкой GPU."""
    
    def __init__(self, model_size="medium", device="cpu", compute_type="int8"):
        """
        Инициализация распознавателя.
        
        Параметры:
        - model_size: "tiny", "base", "small", "medium", "large-v3"
        - device: "cpu" или "cuda"
        - compute_type: "int8" (CPU), "float16" (GPU), "int8_float16" (гибрид)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        
        # Параметры аудиозахвата
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        
        # Настройки VAD
        self.SILENCE_THRESHOLD = 500
        self.SILENCE_DURATION = 0.8
        self.MAX_RECORDING_TIME = 15.0
        
        # Загружаем модель
        self._load_model()
        
        # Инициализируем PyAudio
        self.p = pyaudio.PyAudio()
    
    def _load_model(self):
        """Загружает модель Whisper."""
        print(f"Загружаю Faster-Whisper '{self.model_size}'...")
        print(f"  Устройство: {self.device}")
        print(f"  Тип вычислений: {self.compute_type}")
        
        try:
            from faster_whisper import WhisperModel
            
            # Для CUDA используем float16
            if self.device == "cuda":
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
            else:
                # Для CPU
                self.model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=4,
                    num_workers=2
                )
            
            print(f"  ✓ Модель '{self.model_size}' загружена")
            
        except ImportError:
            print("  ✗ faster-whisper не установлен!")
            print("  Выполните: pip install faster-whisper")
            sys.exit(1)
        except Exception as e:
            print(f"  ✗ Ошибка загрузки модели: {e}")
            
            # Fallback на small
            if self.model_size != "small":
                print("  Пробую загрузить 'small'...")
                try:
                    from faster_whisper import WhisperModel
                    self.model = WhisperModel("small", device="cpu", compute_type="int8")
                    self.model_size = "small"
                    print("  ✓ Модель 'small' загружена (запасной вариант)")
                except Exception as e2:
                    print(f"  ✗ Критическая ошибка: {e2}")
                    sys.exit(1)
            else:
                sys.exit(1)
    
    def listen_for_command(self, play_signal=True, timeout=None):
        """
        Слушает микрофон и возвращает распознанный текст.
        
        Возвращает:
        - Распознанный текст или пустую строку
        """
        if play_signal:
            try:
                from sounds import play_listen_signal
                play_listen_signal()
            except:
                pass
        
        print("🎤 Слушаю...")
        
        # Открываем поток
        stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        frames = []
        is_speaking = False
        silence_counter = 0
        total_frames = 0
        max_frames = int(self.MAX_RECORDING_TIME * self.RATE / self.CHUNK)
        
        silence_threshold_frames = int(self.SILENCE_DURATION * self.RATE / self.CHUNK)
        
        if timeout:
            max_frames = min(max_frames, int(timeout * self.RATE / self.CHUNK))
        
        try:
            while total_frames < max_frames:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(data)
                total_frames += 1
                
                # Вычисляем громкость
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(audio_chunk).mean()
                
                if volume > self.SILENCE_THRESHOLD:
                    if not is_speaking:
                        print("  ▼ Речь обнаружена")
                    is_speaking = True
                    silence_counter = 0
                elif is_speaking:
                    silence_counter += 1
                    if silence_counter > silence_threshold_frames:
                        print("  ■ Конец речи")
                        break
        except Exception as e:
            print(f"  Ошибка записи: {e}")
        finally:
            stream.stop_stream()
            stream.close()
        
        if not frames:
            print("  ✗ Нет аудиоданных")
            return ""
        
        print("🧠 Распознаю речь...")
        
        # Объединяем кадры и нормализуем
        audio_data = b''.join(frames)
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Параметры транскрибации
        transcribe_options = {
            "language": "ru",
            "beam_size": 5,
            "best_of": 5,
            "temperature": 0.0,
            "vad_filter": True,
            "vad_parameters": {
                "threshold": 0.5,
                "min_speech_duration_ms": 250,
                "min_silence_duration_ms": 500
            }
        }
        
        try:
            segments, info = self.model.transcribe(audio_np, **transcribe_options)
            
            # Показываем информацию
            lang_prob = getattr(info, 'language_probability', 0)
            print(f"  Язык: {info.language} (вероятность: {lang_prob:.2f})")
            
            # Собираем текст
            full_text = ""
            for segment in segments:
                full_text += segment.text + " "
            
            result = full_text.strip()
            
            if result:
                print(f"  ✓ Распознано: \"{result}\"")
            else:
                print("  ✗ Ничего не распознано")
            
            return result
            
        except Exception as e:
            print(f"  ✗ Ошибка распознавания: {e}")
            return ""
    
    def close(self):
        """Освобождает ресурсы."""
        try:
            self.p.terminate()
        except:
            pass
        print("  Микрофон отключён.")