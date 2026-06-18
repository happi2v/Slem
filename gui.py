# gui.py
"""
Графический интерфейс Джарвиса с иконкой в трее.
"""
import threading
import time
import os
import sys

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_OK = True
except ImportError:
    TRAY_OK = False
    print("⚠ pystray или pillow не установлены")


class JarvisGUI:
    """Управляет иконкой в трее."""
    
    def __init__(self, jarvis_core=None):
        self.jarvis = jarvis_core
        self.tray_icon = None
        self.tray_thread = None
        
        if TRAY_OK:
            self._create_icon_image()
    
    def _create_icon_image(self):
        """Создаёт изображение для иконки."""
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Синий круг
        draw.ellipse([6, 6, 58, 58], fill=(30, 100, 220), outline=(20, 80, 200), width=2)
        
        # Белая буква J
        draw.text((22, 12), "J", fill=(255, 255, 255))
        
        self.icon_image = img
    
    def _create_menu(self):
        """Создаёт меню для иконки."""
        menu_items = []
        
        if self.jarvis:
            # Статус
            status = "🟢 Активен" if self.jarvis.running else "🔴 Остановлен"
            menu_items.append(pystray.MenuItem(status, None, enabled=False))
            menu_items.append(pystray.Menu.SEPARATOR)
            
            # Команды
            menu_items.append(pystray.MenuItem(
                "Сказать время", 
                lambda: self._run_in_thread(self._say_time)
            ))
            menu_items.append(pystray.MenuItem(
                "Открыть браузер", 
                lambda: self._run_in_thread(self._open_browser)
            ))
            menu_items.append(pystray.Menu.SEPARATOR)
            
            # Управление
            if self.jarvis.use_wake and self.jarvis.wakeword:
                if self.jarvis.wakeword.running:
                    menu_items.append(pystray.MenuItem(
                        "⏸ Пауза Wake Word",
                        lambda: self._toggle_wake_word()
                    ))
                else:
                    menu_items.append(pystray.MenuItem(
                        "▶ Запустить Wake Word",
                        lambda: self._toggle_wake_word()
                    ))
                menu_items.append(pystray.Menu.SEPARATOR)
            
            # Статистика
            menu_items.append(pystray.MenuItem(
                "Статистика",
                lambda: self._run_in_thread(self._show_stats)
            ))
            menu_items.append(pystray.Menu.SEPARATOR)
        
        # Выход
        menu_items.append(pystray.MenuItem(
            "Выход",
            lambda: self._quit()
        ))
        
        return pystray.Menu(*menu_items)
    
    def _run_in_thread(self, func):
        """Запускает функцию в отдельном потоке."""
        t = threading.Thread(target=func, daemon=True)
        t.start()
    
    def _say_time(self):
        """Произносит время."""
        if self.jarvis:
            self.jarvis._tell_time()
    
    def _open_browser(self):
        """Открывает браузер."""
        import webbrowser
        webbrowser.open("https://google.com")
    
    def _toggle_wake_word(self):
        """Включает/выключает Wake Word."""
        if not self.jarvis or not self.jarvis.wakeword:
            return
        
        if self.jarvis.wakeword.running:
            self.jarvis.wakeword.stop()
            print("Wake Word остановлен")
        else:
            self.jarvis.wakeword.start_listening()
            print("Wake Word запущен")
        
        # Обновляем меню
        if self.tray_icon:
            self.tray_icon.menu = self._create_menu()
    
    def _show_stats(self):
        """Показывает статистику."""
        if self.jarvis:
            self.jarvis._tell_stats()
    
    def _quit(self):
        """Выход из программы."""
        print("\nВыход через трей...")
        if self.jarvis:
            self.jarvis.running = False
            self.jarvis._say("Завершаю работу.")
            time.sleep(1)
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        os._exit(0)
    
    def run(self):
        """Запускает иконку в трее."""
        if not TRAY_OK:
            print("Трей недоступен. Установите: pip install pystray pillow")
            return
        
        self.tray_icon = pystray.Icon(
            "jarvis",
            self.icon_image,
            "Джарвис",
            self._create_menu()
        )
        
        print("Иконка в трее запущена")
        self.tray_icon.run()
    
    def run_async(self):
        """Запускает иконку в отдельном потоке."""
        if not TRAY_OK:
            return
        
        self.tray_thread = threading.Thread(target=self.run, daemon=True)
        self.tray_thread.start()
        time.sleep(0.5)  # Даём время на инициализацию


# ============================================================
# ТЕСТ
# ============================================================
if __name__ == "__main__":
    print("Запуск иконки в трее...")
    gui = JarvisGUI()
    gui.run()