# stt.py
"""
Модуль распознавания речи — исправленный VAD
"""
import pyaudio
import numpy as np
import sys
import time


class VoiceRecognizer:
    def __init__(self, model_size="medium", device="cpu", compute_type="int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        
        self.RATE = 16000
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        # VAD — МЯГКИЕ НАСТРОЙКИ
        self.silence_threshold = 150      # ОЧЕНЬ низкий порог
        self.silence_frames_stop = 25     # 1.6 секунды тишины (было 15)
        self.max_record_frames = 200      # ~13 секунд
        self.min_speech_frames = 3        # ВСЕГО 3 кадра (было 6)
        self.padding_frames = 8           # Больше контекста
        
        self.model = None
        self._load_model()
        self.audio = pyaudio.PyAudio()
    
    def _load_model(self):
        print(f"  Загрузка «{self.model_size}»...")
        try:
            from faster_whisper import WhisperModel
            
            if self.device == "cuda":
                self.model = WhisperModel(self.model_size, device="cuda", compute_type="float16")
            else:
                self.model = WhisperModel(
                    self.model_size, device="cpu", compute_type="int8",
                    cpu_threads=4, num_workers=2
                )
            print(f"  ✓ Готово")
        except ImportError:
            print("  ✗ pip install faster-whisper")
            sys.exit(1)
        except Exception as e:
            print(f"  ✗ {e}")
            try:
                from faster_whisper import WhisperModel
                self.model = WhisperModel("small", device="cpu", compute_type="int8")
                self.model_size = "small"
                print("  ✓ «small»")
            except:
                sys.exit(1)
    
    def listen(self, timeout=8):
        """Слушает и распознаёт."""
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
                        # Начало речи
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
                        
                        # Заканчиваем ТОЛЬКО если была речь И достаточно тишины
                        if speech_count >= self.min_speech_frames and silence_count >= self.silence_frames_stop:
                            print(" ■", end="", flush=True)
                            break
        except Exception as e:
            print(f" ⚠", flush=True)
        finally:
            stream.stop_stream()
            stream.close()
        
        # Убираем хвост тишины
        if speaking and silence_count > 0:
            frames = frames[:-silence_count]
        
        # Диагностика
        dur = len(frames) * self.CHUNK / self.RATE
        print(f" {dur:.1f}с | речь: {speech_count} | громкость: {max_volume:.0f}", flush=True)
        
        if not frames or speech_count < self.min_speech_frames:
            print(f"  ✗ Слишком коротко")
            return ""
        
        # Декодируем
        audio_bytes = b''.join(frames)
        audio_float = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        # НОРМАЛИЗАЦИЯ
        rms = np.sqrt(np.mean(audio_float**2))
        if rms > 0.001:
            audio_float = audio_float * (0.15 / rms)
            audio_float = np.clip(audio_float, -1.0, 1.0)
        
        return self._transcribe(audio_float)
    
    def _transcribe(self, audio):
        """Распознаёт."""
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
                print(f" ✗ Пусто ({elapsed:.1f}с)", flush=True)
            
            return result
            
        except Exception as e:
            print(f" ✗ {e}", flush=True)
            return ""
    
    def close(self):
        try:
            self.audio.terminate()
        except:
            pass


# ============================================================
# ТЕСТ
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  ТЕСТ STT (исправленный VAD)")
    print("=" * 50)
    
    try:
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        comp = "float16" if dev == "cuda" else "int8"
    except:
        dev = "cpu"
        comp = "int8"
    
    rec = VoiceRecognizer(model_size="small", device=dev, compute_type=comp)
    
    print("\n  Говорите ГРОМКО и ЧЁТКО")
    print("  Enter — команда, Ctrl+C — выход\n")
    
    try:
        while True:
            input("▶ ")
            text = rec.listen()
            print()
    except KeyboardInterrupt:
        print("\n  Выход.")
    
    rec.close()