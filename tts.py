# tts.py
"""
Синтез речи через Windows SAPI — мгновенно, без файлов.
"""
import threading

try:
    import comtypes.client
    SAPI_OK = True
except ImportError:
    SAPI_OK = False
    print("  ⚠ pip install comtypes")


class VoiceSpeaker:
    """Синтезатор речи через Windows TTS — мгновенно."""
    
    def __init__(self, voice="ru-RU-DmitryNeural", speed="+10%", pitch="-10Hz"):
        self.engine = None
        
        if not SAPI_OK:
            print("  ⚠ comtypes не установлен")
            return
        
        try:
            self.engine = comtypes.client.CreateObject("SAPI.SpVoice")
            self.engine.Rate = 3      # Скорость (-10 до 10)
            self.engine.Volume = 100  # Громкость (0-100)
            
            # Мужской голос
            voices = self.engine.GetVoices()
            for v in voices:
                if "dmitry" in v.GetDescription().lower():
                    self.engine.Voice = v
                    print(f"Синтезатор речи готов. SAPI: {v.GetDescription()}")
                    return
            
            print("Синтезатор речи готов. SAPI (голос по умолчанию)")
            
        except Exception as e:
            print(f"  ⚠ SAPI ошибка: {e}")
            self.engine = None
    
    def speak(self, text):
        """Произносит текст мгновенно."""
        if not text or not self.engine:
            return
        
        print(f"Джарвис: {text}")
        
        def _run():
            try:
                self.engine.Speak(text, 1)  # 1 = асинхронно
            except:
                pass
        
        t = threading.Thread(target=_run, daemon=True)
        t.start()
    
    def speak_async(self, text):
        self.speak(text)
    
    def greet(self): self.speak("К вашим услугам, сэр.")
    def confirm(self): self.speak("Выполняю.")
    def farewell(self): self.speak("До свидания, сэр.")


if __name__ == "__main__":
    import time
    print("=" * 50)
    print("  ТЕСТ SAPI (МГНОВЕННО)")
    print("=" * 50)
    
    speaker = VoiceSpeaker()
    speaker.greet()
    time.sleep(3)
    print("  ✓ Готово")