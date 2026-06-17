# stt.py (обновлённая версия)
import pyaudio
import numpy as np
from faster_whisper import WhisperModel
from sounds import play_listen_signal

class VoiceRecognizer:
    def __init__(self, model_size="small"):
        print(f"Загружаю модель Whisper ({model_size})...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("Модель готова.")
        
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.p = pyaudio.PyAudio()
        
        self.SILENCE_THRESHOLD = 500
        self.SILENCE_DURATION = 0.8
        
    def listen_for_command(self, play_signal=True):
        """Слушает микрофон и возвращает распознанный текст."""
        if play_signal:
            play_listen_signal()  # Звуковой сигнал "начало записи"
        
        print("Слушаю...")
        
        stream = self.p.open(format=self.FORMAT,
                             channels=self.CHANNELS,
                             rate=self.RATE,
                             input=True,
                             frames_per_buffer=self.CHUNK)
        
        frames = []
        is_speaking = False
        silence_counter = 0
        silence_threshold_frames = int(self.SILENCE_DURATION * self.RATE / self.CHUNK)
        
        while True:
            data = stream.read(self.CHUNK, exception_on_overflow=False)
            frames.append(data)
            
            audio_chunk = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_chunk).mean()
            
            if volume > self.SILENCE_THRESHOLD:
                is_speaking = True
                silence_counter = 0
            elif is_speaking:
                silence_counter += 1
                if silence_counter > silence_threshold_frames:
                    break
        
        stream.stop_stream()
        stream.close()
        
        print("Обрабатываю...")
        audio_data = b''.join(frames)
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        segments, _ = self.model.transcribe(audio_np, language="ru", beam_size=5)
        full_text = " ".join([segment.text for segment in segments])
        
        return full_text.strip()
    
    def close(self):
        self.p.terminate()