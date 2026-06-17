# check_imports.py
"""Проверка всех импортов по очереди."""

print("1. Проверка базовых модулей...")
import os
import sys
import time
import json
import threading
import struct
import wave
from collections import deque
print("   ✓ Базовые модули OK")

print("2. Проверка numpy...")
try:
    import numpy as np
    print(f"   ✓ numpy {np.__version__}")
except Exception as e:
    print(f"   ✗ numpy: {e}")

print("3. Проверка pyaudio...")
try:
    import pyaudio
    print(f"   ✓ pyaudio {pyaudio.__version__}")
except Exception as e:
    print(f"   ✗ pyaudio: {e}")

print("4. Проверка faster-whisper...")
try:
    from faster_whisper import WhisperModel
    print("   ✓ faster-whisper OK")
except Exception as e:
    print(f"   ✗ faster-whisper: {e}")

print("5. Проверка edge-tts...")
try:
    import edge_tts
    print("   ✓ edge-tts OK")
except Exception as e:
    print(f"   ✗ edge-tts: {e}")

print("6. Проверка pygame...")
try:
    import pygame
    print(f"   ✓ pygame {pygame.version.ver}")
except Exception as e:
    print(f"   ✗ pygame: {e}")

print("\n7. Проверка sounds.py...")
try:
    from sounds import play_listen_signal
    print("   ✓ sounds.py OK")
except Exception as e:
    print(f"   ✗ sounds.py: {e}")

print("\n8. Проверка stt.py...")
try:
    from stt import VoiceRecognizer
    print("   ✓ stt.py OK (без загрузки модели)")
except Exception as e:
    print(f"   ✗ stt.py: {e}")

print("\n9. Проверка tts.py...")
try:
    from tts import VoiceSpeaker
    print("   ✓ tts.py OK")
except Exception as e:
    print(f"   ✗ tts.py: {e}")

print("\n10. Проверка wakeword.py...")
try:
    from wakeword import VoiceWakeWord
    print("   ✓ wakeword.py OK")
except Exception as e:
    print(f"   ✗ wakeword.py: {e}")

print("\n" + "=" * 50)
print("Диагностика завершена.")