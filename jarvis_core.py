# jarvis_core.py
import webbrowser
import os
import datetime
import time
import threading
from stt import VoiceRecognizer
from tts import VoiceSpeaker
from sounds import play_listen_signal, play_confirm_signal, play_error_signal

# Пробуем импортировать Porcupine, если нет — используем простой ввод
try:
    from wakeword_porcupine import PorcupineWakeWord
    WAKE_WORD_AVAILABLE = True
except ImportError:
    print("Porcupine не установлен. Выполните: pip install pvporcupine pvrecorder")
    print("Пока используем активацию по нажатию Enter.")
    WAKE_WORD_AVAILABLE = False

class JarvisCore:
    def __init__(self):
        self.recognizer = VoiceRecognizer(model_size="small")
        self.speaker = VoiceSpeaker(voice="ru-RU-DmitryNeural")
        self.is_active = False
        self.running = True
        
        if WAKE_WORD_AVAILABLE:
            try:
                self.wakeword = PorcupineWakeWord()
                self.wakeword.on_detected(self.activate)
                self.wake_word_enabled = True
            except Exception as e:
                print(f"Не удалось инициализировать Wake Word: {e}")
                print("Будет использоваться активация по Enter.")
                self.wake_word_enabled = False
        else:
            self.wake_word_enabled = False
            
    def activate(self):
        """Активирует Джарвиса после Wake Word."""
        if not self.is_active:
            self.is_active = True
            play_listen_signal()
            print("Активирован! Слушаю команду...")
            
    def deactivate(self):
        """Деактивирует Джарвиса."""
        self.is_active = False
        print("Деактивирован. Жду фразу 'Джарвис'...")
        
    def execute_command(self, command):
        """Выполняет команду и возвращает ответ голосом."""
        command = command.lower()
        print(f"Распознано: '{command}'")
        
        if not command:
            self.speaker.speak_async("Я ничего не услышал.")
            return True
            
        if "браузер" in command or "интернет" in command:
            self.speaker.speak_async("Запускаю браузер")
            webbrowser.open("https://google.com")
            play_confirm_signal()
            
        elif "калькулятор" in command:
            self.speaker.speak_async("Открываю калькулятор")
            os.system("calc")
            play_confirm_signal()
            
        elif "блокнот" in command or "notepad" in command:
            self.speaker.speak_async("Запускаю блокнот")
            os.system("notepad")
            play_confirm_signal()
            
        elif "время" in command or "который час" in command:
            now = datetime.datetime.now()
            self.speaker.speak_async(f"Сейчас {now.strftime('%H:%M')}")
            
        elif "дата" in command or "число" in command:
            now = datetime.datetime.now()
            months = ["января", "февраля", "марта", "апреля", "мая", "июня",
                      "июля", "августа", "сентября", "октября", "ноября", "декабря"]
            date_str = f"{now.day} {months[now.month - 1]} {now.year} года"
            self.speaker.speak_async(f"Сегодня {date_str}")
            
        elif "привет" in command or "здравствуй" in command:
            hour = datetime.datetime.now().hour
            if 6 <= hour < 12:
                greeting = "Доброе утро"
            elif 12 <= hour < 18:
                greeting = "Добрый день"
            elif 18 <= hour < 23:
                greeting = "Добрый вечер"
            else:
                greeting = "Доброй ночи"
            self.speaker.speak_async(f"{greeting}. Я Джарвис, к вашим услугам.")
            
        elif "как дела" in command:
            self.speaker.speak_async("Все системы работают в штатном режиме. Готов выполнять ваши указания.")
            
        elif "спасибо" in command:
            self.speaker.speak_async("Всегда к вашим услугам.")
            
        elif "выход" in command or "пока" in command or "отключ" in command:
            self.speaker.speak_async("Завершаю работу. До свидания.")
            return False
            
        else:
            self.speaker.speak_async("Извините, я не знаю такой команды. Попробуйте другую.")
            play_error_signal()
            
        return True
        
    def run_with_wake_word(self):
        """Основной цикл с Wake Word активацией."""
        self.wakeword.start_listening()
        self.speaker.speak("Джарвис активирован. Скажите 'Джарвис' для вызова.")
        print("=" * 50)
        print("Джарвис в режиме ожидания. Скажите 'Джарвис' для активации.")
        print("Для экстренного выхода нажмите Ctrl+C")
        print("=" * 50)
        
        while self.running:
            try:
                if self.is_active:
                    # Активен — слушаем команду
                    user_command = self.recognizer.listen_for_command(play_signal=False)
                    if user_command:
                        self.running = self.execute_command(user_command)
                    self.deactivate()
                else:
                    # Неактивен — ждём wake word
                    time.sleep(0.1)
                    
            except KeyboardInterrupt:
                print("\nЗавершение...")
                self.speaker.speak("Принудительное завершение.")
                break
            except Exception as e:
                print(f"Ошибка: {e}")
                if self.is_active:
                    self.deactivate()
                    
        self.cleanup()
        
    def run_simple(self):
        """Упрощённый режим без Wake Word (активация по Enter)."""
        self.speaker.speak("Джарвис активирован в упрощённом режиме.")
        print("=" * 50)
        print("Нажмите Enter для активации, затем говорите команду.")
        print("Для выхода скажите 'пока' или нажмите Ctrl+C")
        print("=" * 50)
        
        while self.running:
            try:
                input("\nНажмите Enter для активации...")
                self.activate()
                user_command = self.recognizer.listen_for_command(play_signal=False)
                if user_command:
                    self.running = self.execute_command(user_command)
                self.deactivate()
                
            except KeyboardInterrupt:
                print("\nЗавершение...")
                self.speaker.speak("Принудительное завершение.")
                break
            except Exception as e:
                print(f"Ошибка: {e}")
                if self.is_active:
                    self.deactivate()
                    
        self.cleanup()
        
    def cleanup(self):
        """Очистка ресурсов."""
        self.recognizer.close()
        if hasattr(self, 'wakeword') and self.wake_word_ENABLED:
            self.wakeword.stop()
        print("Джарвис отключён.")
        
    def run(self):
        """Запускает соответствующий режим."""
        if self.wake_word_enabled:
            self.run_with_wake_word()
        else:
            self.run_simple()

if __name__ == "__main__":
    jarvis = JarvisCore()
    jarvis.run()