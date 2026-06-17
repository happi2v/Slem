# train_wakeword.py
"""
Обучение голосовой активации Джарвиса.
Записывает образцы голоса и создаёт модель для распознавания ключевого слова.
"""
import os
import sys
import time

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wakeword import VoiceWakeWord


def print_title(text):
    """Выводит заголовок."""
    print("\n" + "=" * 55)
    print(f"  {text}")
    print("=" * 55)


def main():
    print_title("ОБУЧЕНИЕ ГОЛОСОВОЙ АКТИВАЦИИ")
    
    print("\nЭтот скрипт запишет образцы вашего голоса")
    print("и создаст модель для активации Джарвиса по ключевому слову.")
    
    # Выбор слова
    print("\nКакое слово будем использовать для активации?")
    word = input("  [По умолчанию: джарвис]: ").strip().lower()
    if not word:
        word = "джарвис"
    
    # Количество образцов
    print(f"\nСколько образцов записать?")
    print("  • 5 — минимум")
    print("  • 8 — рекомендуется")
    print("  • 10+ — максимальная точность")
    
    try:
        num = int(input("  [По умолчанию: 8]: ").strip() or "8")
    except ValueError:
        num = 8
    
    print(f"\n  Ключевое слово: «{word}»")
    print(f"  Образцов: {num}")
    print(f"  Модель сохранится в: models/{word}_model.json")
    
    # Инструкция
    print_title("ИНСТРУКЦИЯ")
    
    print("""
  ✓ Находитесь в ТИХОМ помещении
  ✓ Микрофон на расстоянии 15-25 см ото рта
  ✓ Говорите ТОЛЬКО ключевое слово
  ✓ НЕ двигайтесь во время записи
  ✓ Произносите ОДИНАКОВО каждый раз
  ✓ НЕ меняйте громкость и интонацию
  ✓ Между сигналом и словом — пауза 0.5 сек
  
  ✗ НЕ говорите лишних слов
  ✗ НЕ шумите во время записи
  ✗ НЕ меняйте положение относительно микрофона
    """)
    
    input("Нажмите Enter когда будете готовы...")
    
    # Создаём детектор и записываем
    detector = VoiceWakeWord(wake_word=word)
    
    try:
        success = detector.record_samples(num_samples=num)
        
        if success:
            print_title("✓ ОБУЧЕНИЕ ЗАВЕРШЕНО!")
            
            print(f"""
  Модель сохранена: models/{word}_model.json
  Порог активации: {detector.custom_threshold:.3f}
  
  Теперь можно запустить Джарвиса:
    python jarvis_core.py
  
  И выбрать режим голосовой активации.
  При запуске можно изменить порог (рекомендуется {detector.custom_threshold:.1f})
            """)
        else:
            print_title("✗ ОБУЧЕНИЕ НЕ УДАЛОСЬ")
            
            print("""
  Возможные причины:
  • Слишком шумно в помещении
  • Микрофон не работает или тихий
  • Слово произносится по-разному
  • Слишком мало образцов
  
  Попробуйте:
  • Перейти в тихое место
  • Проверить микрофон: python mic_test.py
  • Записать больше образцов (8-10)
  • Произносить слово максимально одинаково
            """)
            
    except KeyboardInterrupt:
        print("\n\n  Обучение прервано.")
    except Exception as e:
        print(f"\n  ✗ Ошибка: {e}")
        print("  Проверьте работу микрофона: python mic_test.py")
    finally:
        detector.stop()
        print("\n  Для повторного обучения: python train_wakeword.py")


if __name__ == "__main__":
    main()