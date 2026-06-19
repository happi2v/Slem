# tts.py
"""
Синтез речи — Edge-TTS, мужской голос Дмитрий.
"""
import os
import time
import subprocess
import threading


class VoiceSpeaker:
    """Синтезатор речи."""
    
    def __init__(self, voice="ru-RU-DmitryNeural", speed="+10%", pitch="-10Hz"):
        """
        voice: ru-RU-DmitryNeural — мужской голос
        speed: +10% — быстрее
        pitch: -10Hz — ниже тоном
        """
        self.voice = voice
        self.speed = speed
        self.pitch = pitch
        print(f"Синтезатор речи готов. Голос: {self.voice} (speed: {self.speed})")
    
    def speak(self, text):
        """Произносит текст."""
        if not text:
            return
        
        print(f"Джарвис: {text}")
        
        try:
            mp3_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_speech.mp3")
            
            try: os.remove(mp3_path)
            except: pass
            
            safe_text = text.replace('"', '')
            
            cmd = f'edge-tts --voice {self.voice} --rate={self.speed} --pitch={self.pitch} --text "{safe_text}" --write-media "{mp3_path}"'
            subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=15)
            
            time.sleep(0.3)
            
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                os.system(f'start "" "{mp3_path}"')
                
        except Exception as e:
            print(f"  ⚠ Ошибка: {e}")
    
    def speak_async(self, text):
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()
    
    def greet(self): self.speak_async("К вашим услугам, сэр.")
    def confirm(self): self.speak_async("Выполняю.")
    def farewell(self): self.speak_async("До свидания, сэр.")


if __name__ == "__main__":
    print("=" * 50)
    print("  ТЕСТ TTS")
    print("=" * 50)
    
    speaker = VoiceSpeaker()
    
    print("\n  Говорю приветствие...")
    speaker.greet()
    
    print("  Жду 3 секунды...")
    time.sleep(3)
    
    print("\n  ✓ Тест завершён")