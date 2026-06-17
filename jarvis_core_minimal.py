# jarvis_core_minimal.py
"""Минимальная версия для проверки."""
import datetime
import webbrowser
import os

print("Загрузка модулей...")

from stt import VoiceRecognizer
print("  STT загружен")

from tts import VoiceSpeaker
print("  TTS загружен")

# Минимальная версия без wake word
class JarvisCore:
    def __init__(self):
        self.recognizer = VoiceRecognizer(model_size="small")  # small для скорости
        self.speaker = VoiceSpeaker(voice="ru-RU-DmitryNeural")
        self.running = True
        
    def execute_command(self, command):
        command = command.lower().strip()
        print(f"Команда: '{command}'")
        
        if not command:
            self.speaker.speak_async("Не расслышал.")
            return True
            
        if "браузер" in command:
            self.speaker.speak_async("Запускаю браузер")
            webbrowser.open("https://google.com")
        elif "калькулятор" in command:
            self.speaker.speak_async("Калькулятор")
            os.system("calc")
        elif "время" in command:
            now = datetime.datetime.now()
            self.speaker.speak_async(f"Сейчас {now.hour} {now.minute}")
        elif "привет" in command:
            self.speaker.speak_async("Здравствуйте!")
        elif "выход" in command or "пока" in command:
            self.speaker.speak_async("До свидания")
            return False
        else:
            self.speaker.speak_async("Неизвестная команда")
        return True
        
    def run(self):
        self.speaker.speak("Джарвис запущен")
        print("\nНажмите Enter для команды, Ctrl+C для выхода\n")
        
        while self.running:
            try:
                input(">> ")
                print("Слушаю...")
                cmd = self.recognizer.listen_for_command(play_signal=False)
                if cmd:
                    self.running = self.execute_command(cmd)
            except KeyboardInterrupt:
                break
                
        self.recognizer.close()

if __name__ == "__main__":
    jarvis = JarvisCore()
    jarvis.run()