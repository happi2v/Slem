# volume.py
"""
Управление системной громкостью Windows.
Использует Win32 API напрямую.
"""
import ctypes
import time


class VolumeControl:
    """Управление громкостью через Win32 API."""
    
    def __init__(self):
        self.ok = True
        print("  ✓ Громкость (Win32 API)")
    
    def get_volume(self):
        """Получить текущую громкость (0-100)."""
        try:
            # Используем ctypes для вызова WinMM
            winmm = ctypes.windll.winmm
            volume = ctypes.c_uint()
            winmm.waveOutGetVolume(0, ctypes.byref(volume))
            
            # Расшифровываем значение (младшие 16 бит — левый канал)
            left = volume.value & 0xFFFF
            right = (volume.value >> 16) & 0xFFFF
            
            # Конвертируем в проценты (0x0000-0xFFFF)
            return int((left + right) / 2 / 0xFFFF * 100)
        except:
            return 50
    
    def set_volume(self, level):
        """Установить громкость (0-100)."""
        level = max(0, min(100, level))
        
        try:
            winmm = ctypes.windll.winmm
            
            # Конвертируем проценты в значение WinMM
            value = int(level / 100 * 0xFFFF)
            # Оба канала
            volume_value = value | (value << 16)
            
            winmm.waveOutSetVolume(0, volume_value)
            print(f"  🔊 Громкость: {level}%")
            return level
        except:
            pass
        
        # Fallback: клавиши
        self._press_volume_keys(level)
        return level
    
    def volume_up(self, step=10):
        """Увеличить громкость."""
        current = self.get_volume()
        return self.set_volume(current + step)
    
    def volume_down(self, step=10):
        """Уменьшить громкость."""
        current = self.get_volume()
        return self.set_volume(current - step)
    
    def mute(self):
        """Переключить mute."""
        try:
            import keyboard
            keyboard.press_and_release("volume_mute")
            time.sleep(0.1)
            return None
        except:
            pass
    
    def is_muted(self):
        """Проверяет, выключен ли звук."""
        return False  # WinMM не показывает mute
    
    def _press_volume_keys(self, target_level):
        """Устанавливает громкость клавишами."""
        try:
            import keyboard
            
            # Опускаем в 0
            for _ in range(50):
                keyboard.press_and_release("volume_down")
                time.sleep(0.005)
            
            time.sleep(0.1)
            
            # Поднимаем до нужного
            presses = target_level // 2
            for _ in range(presses):
                keyboard.press_and_release("volume_up")
                time.sleep(0.005)
        except:
            pass


# ============================================================
# ТЕСТ
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  ТЕСТ ГРОМКОСТИ")
    print("=" * 50)
    
    vc = VolumeControl()
    
    vol = vc.get_volume()
    print(f"\n  Текущая громкость: {vol}%")
    print(f"  Метод: Win32 API")
    
    print("\n  Команды: up, down, 50, mute, exit\n")
    
    while True:
        cmd = input("  > ").strip().lower()
        
        if cmd == "exit":
            break
        elif cmd == "up":
            vc.volume_up(10)
            print(f"  Громкость: {vc.get_volume()}%")
        elif cmd == "down":
            vc.volume_down(10)
            print(f"  Громкость: {vc.get_volume()}%")
        elif cmd == "mute":
            vc.mute()
        elif cmd.isdigit():
            vc.set_volume(int(cmd))
        else:
            print("  ?")