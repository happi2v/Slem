# sounds.py
import numpy as np
import pygame
import io
import wave

def generate_beep(frequency=800, duration=0.15, volume=0.5, sample_rate=22050):
    """
    Генерирует звуковой сигнал (бип) и возвращает как bytes.
    frequency: частота в Гц
    duration: длительность в секундах
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(frequency * 2 * np.pi * t) * volume
    
    # Плавное затухание, чтобы не было щелчка
    fade_len = int(sample_rate * 0.01)  # 10 мс фейд
    if fade_len > 0 and len(tone) > fade_len * 2:
        tone[:fade_len] *= np.linspace(0, 1, fade_len)
        tone[-fade_len:] *= np.linspace(1, 0, fade_len)
    
    # Конвертируем в 16-битный PCM
    audio = (tone * 32767).astype(np.int16)
    
    # Сохраняем в WAV в памяти
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())
    
    return buffer.getvalue()

# Предзагрузим звуки
pygame.mixer.init()
SOUND_LISTEN = pygame.mixer.Sound(io.BytesIO(generate_beep(800, 0.1)))
SOUND_CONFIRM = pygame.mixer.Sound(io.BytesIO(generate_beep(1200, 0.2)))
SOUND_ERROR = pygame.mixer.Sound(io.BytesIO(generate_beep(300, 0.3)))

def play_listen_signal():
    SOUND_LISTEN.play()

def play_confirm_signal():
    SOUND_CONFIRM.play()
    
def play_error_signal():
    SOUND_ERROR.play()