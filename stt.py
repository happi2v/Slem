# stt.py
"""
Модуль распознавания речи (Speech-to-Text)
С поддержкой GPU (CUDA) и CPU
"""
import pyaudio
import numpy as np
import sys
import time
import os


class VoiceRecognizer:
    """Распознаватель речи. Автоопределение GPU."""
    
    def __init__(self, model_size="medium", device="auto", compute_type="auto"):
        """
        Инициализация.
        
        Параметры:
        - model_size: tiny, base, small, medium, large-v3
        - device: auto, cuda, cpu
        - compute_type: auto, float16, int8, int8_float16
        """
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
        
        # Параметры аудио
        self.RATE = 16000
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        # VAD
        self.silence_threshold = 150
        self.silence_frames_stop = 25
        self.max_record_frames = 200
        self.min_speech_frames = 3
        self.padding_frames = 8
        
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
                print(f"  ✓ GPU найдена: {name} ({mem:.1f} ГБ)")
                return "cuda"
            else:
                print("  ℹ CUDA не доступна, использую CPU")
                return "cpu"
        except ImportError:
            print("  ℹ PyTorch не установлен, использую CPU")
            print("  Для GPU: pip install torch --index-url https://download.pytorch.org/whl/cu121")
            return "cpu"
        except Exception as e:
            print(f"  ℹ Ошибка: {e}, использую CPU")
            return "cpu"
    
    def _load_model(self):
        """Загружает модель Whisper."""
        print(f"  Загрузка «{self.model_size}» на {self.device.upper()}...")
        
        try:
            from faster_whisper import WhisperModel
            
            if self.device == "cuda":
                # GPU: float16 для скорости, можно int8_float16 для экономии VRAM
                self.model = WhisperModel(
                    self.model_size,
                    device="cuda",
                    compute_type=self.compute_type
                )
                print(f"  ✓ GPU режим ({self.compute_type})")
            else:
                # CPU
                self.model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=os.cpu_count() or 4,
                    num_workers=2
                )
                print(f"  ✓ CPU режим")
            
        except ImportError:
            print("  ✗ pip install faster-whisper")
            sys.exit(1)
        except Exception as e:
            print(f"  ✗ Ошибка загрузки: {e}")
            
            # Пробуем модель поменьше
            fallbacks = {"large-v3": "medium", "medium": "small", "small": "base", "base": "tiny"}
            if self.model_size in fallbacks:
                fallback = fallbacks[self.model_size]
                print(f"  Пробую «{fallback}»...")
                try:
                    from faster_whisper import WhisperModel
                    self.model = WhisperModel(fallback, device=self.device, compute_type=self.compute_type)
                    self.model_size = fallback
                    print(f"  ✓ Загружена «{fallback}»")
                except:
                    sys.exit(1)
    
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
                
                chunk = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(chunk).mean()
                max_volume = max(max_volume, volume)
                
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
            print(f" ✗ (речь: {speech_count}, громкость: {max_volume:.0f})", flush=True)
            return ""
        
        print(f" {dur:.1f}с", flush=True)
        
        audio_bytes = b''.join(frames)
        audio_float = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Нормализация
        rms = np.sqrt(np.mean(audio_float ** 2))
        if rms > 0.001:
            audio_float = audio_float * (0.15 / rms)
            audio_float = np.clip(audio_float, -1.0, 1.0)
        
        return self._transcribe(audio_float)
    
    def _transcribe(self, audio):
        """Распознаёт речь."""
        try:
            print("🧠 ...", end="", flush=True)
            start = time.time()
            
            segments, info = self.model.transcribe(
                audio,
                language="ru",
                beam_size=5,
                temperature=[0.0, 0.2],
                no_speech_threshold=0.6,
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
    
    def close(self):
        """Очистка."""
        try:
            self.audio.terminate()
        except:
            pass
        
        # Очистка VRAM
        if self.device == "cuda":
            try:
                import torch
                torch.cuda.empty_cache()
            except:
                pass
    
    def info(self):
        """Информация о конфигурации."""
        return {
            "model": self.model_size,
            "device": self.device.upper(),
            "compute": self.compute_type
        }


# ============================================================
# ТЕСТ
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  ТЕСТ STT с авто-GPU")
    print("=" * 50)
    
    rec = VoiceRecognizer(model_size="small")
    print(f"  {rec.info()}\n")
    
    try:
        while True:
            input("▶ ")
            text = rec.listen()
            print()
    except KeyboardInterrupt:
        print("\n  Выход.")
    
    rec.close()