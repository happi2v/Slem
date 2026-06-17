# mic_test.py
"""Проверка уровня сигнала с микрофона."""
import pyaudio
import numpy as np

CHUNK = 1024
RATE = 16000

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, 
                input=True, frames_per_buffer=CHUNK)

print("=" * 50)
print("  ТЕСТ МИКРОФОНА")
print("=" * 50)
print("  Говорите что-нибудь. Ctrl+C для выхода.")
print("  Смотрите на числа — они должны расти при речи.\n")

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio = np.frombuffer(data, dtype=np.int16)
        volume = np.abs(audio).mean()
        
        # Визуальный индикатор
        bars = int(volume / 50)
        bar_str = "█" * min(bars, 40)
        
        status = ""
        if volume < 100:
            status = "тишина"
        elif volume < 300:
            status = "шёпот"
        elif volume < 800:
            status = "речь"
        elif volume < 2000:
            status = "громко"
        else:
            status = "ОЧЕНЬ ГРОМКО"
        
        print(f"\r  Уровень: {volume:6.0f} |{bar_str:<40}| {status}", end="")
        
except KeyboardInterrupt:
    print("\n\n  Выход.")

stream.close()
p.terminate()