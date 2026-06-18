# music.py
"""
Управление Яндекс Музыкой через браузер.
"""
import webbrowser
import time
import os
import subprocess

try:
    import keyboard
    CONTROLS_OK = True
except:
    CONTROLS_OK = False


class YandexMusic:
    """Управление Яндекс Музыкой."""
    
    YANDEX_MUSIC_URL = "https://music.yandex.ru/home"
    
    def __init__(self):
        self.is_open = False
        
        if not CONTROLS_OK:
            print("  ⚠ keyboard не установлен")
    
    def open(self):
        """Открывает Яндекс Музыку."""
        print("  Открываю Яндекс Музыку...")
        
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        
        opened = False
        for path in chrome_paths:
            if os.path.exists(path):
                subprocess.Popen([path, "--new-window", self.YANDEX_MUSIC_URL])
                opened = True
                break
        
        if not opened:
            webbrowser.open(self.YANDEX_MUSIC_URL)
        
        self.is_open = True
        print("  ✓ Яндекс Музыка открыта")
    
    def play_pause(self):
        """Play / Pause через медиа-клавишу."""
        if not self.is_open:
            self.open()
            return
        
        print("  ▶⏸ Play/Pause")
        try:
            keyboard.press_and_release("play/pause")
        except:
            pass
    
    def next_track(self):
        """Следующий трек."""
        if not self.is_open:
            return
        
        print("  ⏭ Следующий")
        try:
            keyboard.press_and_release("media_next_track")
        except:
            pass
    
    def prev_track(self):
        """Предыдущий трек."""
        if not self.is_open:
            return
        
        print("  ⏮ Предыдущий")
        try:
            keyboard.press_and_release("media_prev_track")
        except:
            pass
    
    def like(self):
        """Лайк."""
        if not self.is_open:
            return
        
        print("  ❤️ Лайк")
        try:
            keyboard.press_and_release("ctrl+l")
        except:
            pass
    
    def search(self, query):
        """Поиск трека."""
        if not self.is_open:
            self.open()
            time.sleep(5)
        
        print(f"  🔍 Ищу: {query}")
        
        try:
            keyboard.press_and_release("ctrl+f")
            time.sleep(0.5)
            keyboard.write(query)
            time.sleep(0.5)
            keyboard.press_and_release("enter")
            time.sleep(2)
            keyboard.press_and_release("enter")
            print(f"  ✓ Найдено: {query}")
        except:
            print("  ✗ Ошибка поиска")
    
    def close(self):
        """Закрыть вкладку."""
        print("  Закрываю музыку")
        try:
            keyboard.press_and_release("ctrl+w")
        except:
            pass
        self.is_open = False