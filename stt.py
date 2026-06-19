# stt.py
"""
Распознавание речи — оптимизировано под large-v3 на GPU.
Быстрый отклик.
"""
import pyaudio
import numpy as np
import sys
import time
import os


class VoiceRecognizer:
    """Распознаватель речи — large-v3 GPU."""
    
    def __init__(self, model_size="large-v3", device="auto", compute_type="auto"):
        self.model_size = model_size
        
        if device == "auto":
            self.device = self._detect_gpu()
        else:
            self.device = device
        
        if compute_type == "auto":
            self.compute_type = "int8_float16" if self.device == "cuda" else "int8"
        else:
            self.compute_type = compute_type
        
        self.RATE = 16000
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        # VAD — БЫСТРЫЙ
        self.silence_threshold = 400
        self.silence_frames_stop = 8      # 0.5 сек (было 15)
        self.max_record_frames = 120      # ~7 сек (было 200)
        self.min_speech_frames = 3        # 0.2 сек (было 4)
        self.padding_frames = 5
        
        self.model = None
        self._load_model()
        self.audio = pyaudio.PyAudio()
    
    def _detect_gpu(self):
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
        print(f"  Загрузка «{self.model_size}» на {self.device.upper()}...")
        try:
            from faster_whisper import WhisperModel
            
            if self.device == "cuda":
                self.model = WhisperModel(
                    self.model_size, device="cuda",
                    compute_type=self.compute_type,
                    num_workers=2, cpu_threads=2
                )
            else:
                self.model = WhisperModel(
                    self.model_size, device="cpu",
                    compute_type="int8",
                    cpu_threads=os.cpu_count() or 4, num_workers=2
                )
            print(f"  ✓ Готово")
        except:
            print("  Пробую medium...")
            from faster_whisper import WhisperModel
            self.model = WhisperModel("medium", device=self.device, compute_type=self.compute_type)
            self.model_size = "medium"
            print(f"  ✓ medium")
    
    def listen(self, timeout=5):
        """Слушает и распознаёт — быстро."""
        stream = self.audio.open(
            format=self.FORMAT, channels=self.CHANNELS,
            rate=self.RATE, input=True, frames_per_buffer=self.CHUNK
        )
        
        print("🎤 Слушаю...", end="", flush=True)
        
        frames = []
        speaking = False
        silence_count = 0
        speech_count = 0
        
        pre_buffer = []
        
        try:
            while len(frames) < self.max_record_frames:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                chunk = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(chunk).mean()
                
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
        finally:
            stream.stop_stream()
            stream.close()
        
        if not frames or speech_count < self.min_speech_frames:
            print(" ✗", flush=True)
            return ""
        
        dur = len(frames) * self.CHUNK / self.RATE
        print(f" {dur:.1f}с", flush=True)
        
        audio_bytes = b''.join(frames)
        audio_float = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Нормализация громкости
        rms = np.sqrt(np.mean(audio_float**2))
        if rms > 0.001:
            audio_float = audio_float * (0.2 / rms)
            audio_float = np.clip(audio_float, -1.0, 1.0)
        
        return self._transcribe(audio_float)
    
    def _transcribe(self, audio):
        """Распознавание — быстро."""
        try:
            print("🧠 ...", end="", flush=True)
            start = time.time()
            
            segments, _ = self.model.transcribe(
                audio,
                language="ru",
                beam_size=3,
                best_of=3,
                temperature=0.0,
                vad_filter=True,
                condition_on_previous_text=False,
                no_speech_threshold=0.6
            )
            
            words = [seg.text.strip() for seg in segments if seg.text.strip()]
            text = " ".join(words).strip()
            elapsed = time.time() - start
            
            if text:
                print(f" ✓ «{text}» ({elapsed:.1f}с)", flush=True)
            else:
                print(f" ✗ ({elapsed:.1f}с)", flush=True)
            
            return text
        except Exception as e:
            print(f" ✗ {e}", flush=True)
            return ""
    
    def info(self):
        return {"model": self.model_size, "device": self.device.upper(), "compute": self.compute_type}
    
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