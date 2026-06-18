# volume.py
"""
Управление системной громкостью Windows.
"""
import ctypes
import time


class VolumeControl:
    """Управление громкостью."""
    
    def __init__(self):
        self.ok = False
        
        try:
            self.winmm = ctypes.windll.winmm
            # Проверяем чтение
            vol = ctypes.c_uint()
            result = self.winmm.waveOutGetVolume(0, ctypes.byref(vol))
            if result == 0:
                self.ok = True
                current = int((vol.value & 0xFFFF) / 0xFFFF * 100)
                print(f"  ✓ Громкость: {current}%")
            else:
                print(f"  ⚠ WinMM ошибка чтения, использую клавиши")
        except Exception as e:
            print(f"  ⚠ WinMM: {e}, использую клавиши")
    
    def get_volume(self):
        """Получить громкость 0-100."""
        if self.ok:
            try:
                vol = ctypes.c_uint()
                self.winmm.waveOutGetVolume(0, ctypes.byref(vol))
                left = vol.value & 0xFFFF
                return int(left / 0xFFFF * 100)
            except:
                self.ok = False
        return 50
    
    def set_volume(self, level):
        """Установить громкость 0-100."""
        level = max(0, min(100, level))
        
        if self.ok:
            try:
                # Конвертируем 0-100 в 0-65535
                val = int(level / 100.0 * 0xFFFF)
                # Оба канала
                both = val | (val << 16)
                
                print(f"  DEBUG: level={level}, val={val}, both={both}")
                
                result = self.winmm.waveOutSetVolume(0, both)
                
                if result == 0:
                    print(f"  🔊 Громкость: {level}%")
                    return level
                else:
                    print(f"  ⚠ WinMM set error: {result}")
                    self.ok = False
            except Exception as e:
                print(f"  ⚠ WinMM set exception: {e}")
                self.ok = False
        
        # Fallback
        if not self.ok:
            print(f"  ⌨ Клавиши -> {level}%")
            self._set_via_keys(level)
        
        return level
    
    def volume_up(self, step=10):
        return self.set_volume(self.get_volume() + step)
    
    def volume_down(self, step=10):
        return self.set_volume(self.get_volume() - step)
    
    def mute(self):
        try:
            import keyboard
            keyboard.press_and_release("volume_mute")
            time.sleep(0.1)
        except:
            pass
    
    def is_muted(self):
        return False
    
    def _set_via_keys(self, target):
        """Установка громкости клавишами."""
        try:
            import keyboard
            
            # В 0
            for _ in range(50):
                keyboard.press_and_release("volume_down")
                time.sleep(0.003)
            
            time.sleep(0.05)
            
            # Вверх
            for _ in range(target // 2):
                keyboard.press_and_release("volume_up")
                time.sleep(0.003)
            
            print(f"  ⌨ Громкость: ~{target}%")
        except:
            print("  ⚠ Клавиши не работают")


# Тест
if __name__ == "__main__":
    vc = VolumeControl()
    print(f"\nТекущая: {vc.get_volume()}%")
    
    print("\nТест 50%:")
    vc.set_volume(50)
    time.sleep(0.5)
    print(f"Стало: {vc.get_volume()}%")
    
    print("\nТест 30%:")
    vc.set_volume(30)
    time.sleep(0.5)
    print(f"Стало: {vc.get_volume()}%")