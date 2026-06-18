# test_wakeword.py
import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from wakeword import VoiceWakeWord

def on_detect():
    print("\n" + "!" * 50)
    print("!!! ОБНАРУЖЕНО !!!")
    print("!" * 50 + "\n")

model_path = "models/джарвис_model.json"
if not os.path.exists(model_path):
    print("Модель не найдена!")
    sys.exit(1)

detector = VoiceWakeWord(wake_word="джарвис", sensitivity=0.3, debug=True)
detector.custom_threshold = 0.3  # Очень низкий порог для теста
detector.on_detected(on_detect)
detector.start_listening()

print(f"Порог: {detector.custom_threshold}")
print("Говорите «Джарвис». Ctrl+C — выход.\n")

try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nВыход.")
detector.stop()