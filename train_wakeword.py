# train_wakeword.py
"""
Скрипт для обучения Wake Word.
Запускается отдельно перед первым использованием Джарвиса.
"""
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wakeword import VoiceWakeWord

def main():
    print("=" * 55)
    print("  ОБУЧЕНИЕ ГОЛОСОВОЙ АКТИВАЦИИ ДЖАРВИСА")
    print("=" * 55)
    print()
    print("Этот скрипт запишет образцы вашего голоса")
    print("и создаст модель для распознавания ключевого слова.")
    print()
    
    # Выбор слова
    word = input("Ключевое слово (по умолчанию 'джарвис'): ").strip().lower()
    if not word:
        word = "джарвис"
        
    # Количество образцов
    num_str = input("Количество образцов (рекомендуется 5-8): ").strip()
    try:
        num = int(num_str) if num_str else 5
    except ValueError:
        num = 5
        
    print(f"\nБудет записано {num} образцов для слова '{word}'")
    
    # Создаём детектор и записываем
    detector = VoiceWakeWord(wake_word=word)
    
    try:
        success = detector.record_samples(num_samples=num)
        
        if success:
            print("\n✅ Обучение успешно завершено!")
            print(f"Модель сохранена в: models/{word}_model.json")
            print("\nТеперь можно запускать Джарвиса:")
            print("  python jarvis_core.py")
        else:
            print("\n❌ Обучение не удалось.")
            print("Попробуйте:")
            print("  1. Уменьшить фоновый шум")
            print("  2. Говорить чётче и громче")
            print("  3. Записать больше образцов")
            
    except KeyboardInterrupt:
        print("\n\nОбучение прервано пользователем.")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    finally:
        detector.stop()
        
if __name__ == "__main__":
    main()