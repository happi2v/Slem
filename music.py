# music.py
"""
Управление Яндекс Музыкой через браузер.
"""
import webbrowser
import time
import os
import subprocess

try:
    import pyautogui
    import keyboard
    CONTROLS_OK = True
except ImportError:
    CONTROLS_OK = False
    print("⚠ pyautogui или keyboard не установлены")


class YandexMusic:
    """Управление Яндекс Музыкой."""
    
    YANDEX_MUSIC_URL = "https://music.yandex.ru/home"
    
    def __init__(self):
        self.is_open = False
        self.browser_process = None
        
        if not CONTROLS_OK:
            print("⚠ Управление клавишами недоступно")
    
    def open(self):
        """Открывает Яндекс Музыку в браузере."""
        print("  Открываю Яндекс Музыку...")
        
        # Пробуем открыть в Chrome
        try:
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    subprocess.Popen([
                        path,
                        "--new-window",
                        self.YANDEX_MUSIC_URL
                    ])
                    self.is_open = True
                    time.sleep(3)  # Ждём загрузку
                    print("  ✓ Яндекс Музыка открыта в Chrome")
                    return
        except:
            pass
        
        # Fallback: стандартный браузер
        webbrowser.open(self.YANDEX_MUSIC_URL)
        self.is_open = True
        time.sleep(3)
        print("  ✓ Яндекс Музыка открыта")
    
    def play_pause(self):
        """Play / Pause."""
        if not self._check_open():
            return
        
        print("  ▶⏸ Play/Pause")
        self._press_key("space")
    
    def next_track(self):
        """Следующий трек."""
        if not self._check_open():
            return
        
        print("  ⏭ Следующий трек")
        self._press_key("media_next_track")
    
    def prev_track(self):
        """Предыдущий трек."""
        if not self._check_open():
            return
        
        print("  ⏮ Предыдущий трек")
        self._press_key("media_prev_track")
    
    def volume_up(self):
        """Громче."""
        if not self._check_open():
            return
        
        print("  🔊 Громче")
        for _ in range(5):
            self._press_key("volume_up")
            time.sleep(0.05)
    
    def volume_down(self):
        """Тише."""
        if not self._check_open():
            return
        
        print("  🔉 Тише")
        for _ in range(5):
            self._press_key("volume_down")
            time.sleep(0.05)
    
    def mute(self):
        """Выключить звук."""
        if not self._check_open():
            return
        
        print("  🔇 Mute")
        self._press_key("volume_mute")
    
    def like(self):
        """Лайк трека."""
        if not self._check_open():
            return
        
        print("  ❤️ Лайк")
        # В Яндекс Музыке лайк по Ctrl+L
        keyboard.press_and_release("ctrl+l")
    
    def search(self, query):
        """Поиск трека."""
        if not self._check_open():
            self.open()
            time.sleep(3)
        
        print(f"  🔍 Поиск: {query}")
        
        # Ctrl+F для поиска в Яндекс Музыке
        keyboard.press_and_release("ctrl+f")
        time.sleep(0.3)
        
        # Вводим запрос
        keyboard.write(query)
        time.sleep(0.3)
        keyboard.press_and_release("enter")
        time.sleep(2)
        
        # Запускаем первый результат
        keyboard.press_and_release("enter")
        print(f"  ✓ Запускаю: {query}")
    
    def close(self):
        """Закрывает вкладку."""
        print("  Закрываю музыку")
        keyboard.press_and_release("ctrl+w")
        self.is_open = False
    
    def _check_open(self):
        """Проверяет, открыта ли музыка."""
        if not self.is_open:
            print("  ! Сначала откройте музыку: «включи музыку»")
            return False
        return True
    
    def _press_key(self, key):
        """Нажимает клавишу."""
        if not CONTROLS_OK:
            print(f"  ! Не могу нажать {key}")
            return
        
        try:
            if key.startswith("media_"):
                keyboard.press_and_release(key)
            elif key.startswith("volume_"):
                keyboard.press_and_release(key)
            else:
                keyboard.press_and_release(key)
            time.sleep(0.2)
        except Exception as e:
            print(f"  ✗ Ошибка клавиши: {e}")


# ============================================================
# ТЕСТ
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  ТЕСТ ЯНДЕКС МУЗЫКИ")
    print("=" * 50)
    
    music = YandexMusic()
    
    print("\n  Команды:")
    print("  open — открыть")
    print("  play — play/pause")
    print("  next — следующий")
    print("  prev — предыдущий")
    print("  volup — громче")
    print("  voldown — тише")
    print("  mute — без звука")
    print("  like — лайк")
    print("  search ТРЕК — поиск")
    print("  close — закрыть")
    print("  exit — выход\n")
    
    while True:
        cmd = input("  > ").strip().lower()
        
        if cmd == "exit":
            break
        elif cmd == "open":
            music.open()
        elif cmd == "play":
            music.play_pause()
        elif cmd == "next":
            music.next_track()
        elif cmd == "prev":
            music.prev_track()
        elif cmd == "volup":
            music.volume_up()
        elif cmd == "voldown":
            music.volume_down()
        elif cmd == "mute":
            music.mute()
        elif cmd == "like":
            music.like()
        elif cmd.startswith("search "):
            music.search(cmd[7:])
        elif cmd == "close":
            music.close()
        else:
            print("  Неизвестная команда")