# test_wakeword.py
"""Тест только Wake Word с подробным выводом."""
import time
import sys
import os

# Добавляем путь
sys.path.insert(0, os.path.dirname(__file__))

from wakeword import VoiceWakeWord

def on_detect():
    print("\n" + "!" * 50)
    print("!!! ОБНАРУЖЕНО !!!")
    print("!" * 50 + "\n")

print("=" * 50)
print("  ТЕСТ WAKE WORD (подробный)")
print("=" * 50)

# Проверяем модель
model_path = "models/джарвис_model.json"
if not os.path.exists(model_path):
    print("\n❌ Модель не найдена!")
    print("Сначала запустите: python train_wakeword.py")
    sys.exit(1)

# Создаём детектор с ОТЛАДКОЙ
detector = VoiceWakeWord(
    wake_word="джарвис",
    sensitivity=0.5,  # Пониженный порог для теста
    debug=True         # Включаем отладку
)

# Принудительно занижаем порог
detector.custom_threshold = 0.35  # Очень низкий порог для теста

print(f"Модель загружена")
print(f"Порог: {detector.custom_threshold}")
print(f"Признаков в модели: {len(detector.custom_model) if detector.custom_model else 0}")
print()

# Показываем ожидаемые параметры
if detector.custom_model:
    print("Ожидаемые параметры голоса:")
    for key in ['duration', 'rms_energy', 'zcr', 'spectral_centroid']:
        if key in detector.custom_model:
            stats = detector.custom_model[key]
            print(f"  {key}: mean={stats['mean']:.4f}, std={stats['std']:.4f}")

detector.on_detected(on_detect)
detector.start_listening()

print("\nГоворите «Джарвис» громко и чётко...")
print("Смотрите на вывод — появятся ли строки «Анализ»?")
print("Ctrl+C для выхода\n")

try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nТест завершён.")

detector.stop()