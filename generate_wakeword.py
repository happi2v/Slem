# generate_wakeword.py
"""
Скрипт для создания кастомной Wake Word модели.
Запустите один раз, чтобы создать модель для слова "джарвис".
"""
import os
import sys

def generate_jarvis_model():
    print("Генерация модели для Wake Word 'джарвис'...")
    print("Этот процесс требует установки дополнительных зависимостей.")
    print()
    
    # Проверяем наличие необходимых библиотек
    try:
        import openwakeword
        import tensorflow as tf
    except ImportError:
        print("ОШИБКА: Необходимые библиотеки не установлены.")
        print("Выполните: pip install openwakeword tensorflow")
        return
    
    # Путь для сохранения модели
    model_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(model_dir, exist_ok=True)
    
    print("К сожалению, автоматическая генерация модели требует")
    print("сложного процесса обучения с большим количеством примеров.")
    print()
    print("АЛЬТЕРНАТИВНЫЙ ПЛАН:")
    print("1. Скачайте готовую модель 'jarvis' из интернета")
    print("2. Или используйте модель 'alexa' с низким порогом чувствительности")
    print("3. Или перейдите на Porcupine (библиотека, которая уже знает слово 'jarvis')")
    print()
    print("Рекомендую вариант 3. Porcupine имеет встроенную поддержку")
    print("слова 'Jarvis' из коробки и работает офлайн.")
    
if __name__ == "__main__":
    generate_jarvis_model()