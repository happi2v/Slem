# volume.py
"""
Управление системной громкостью Windows.
"""
import sys
import os

# Пробуем pycaw (Windows)
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    import comtypes
    comtypes.CoInitialize()
    
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)
    VOLUME_OK = True
except:
    VOLUME_OK = False


class VolumeControl:
    """Управление громкостью."""
    
    def __init__(self):
        if not VOLUME_OK:
            print("  ⚠ pycaw не установлен. Использую клавиши.")
    
    def get_volume(self):
        """Получить текущую громкость (0-100)."""
        if VOLUME_OK:
            try:
                return int(volume.GetMasterVolumeLevelScalar() * 100)
            except:
                pass
        return -1
    
    def set_volume(self, level):
        """
        Установить громкость.
        level: 0-100
        """
        level = max(0, min(100, level))
        
        if VOLUME_OK:
            try:
                volume.SetMasterVolumeLevelScalar(level / 100, None)
                print(f"  🔊 Громкость: {level}%")
                return level
            except:
                pass
        
        # Fallback: клавиши
        self._press_volume_keys(level)
        return level
    
    def volume_up(self, step=10):
        """Увеличить громкость."""
        if VOLUME_OK:
            current = self.get_volume()
            return self.set_volume(current + step)
        
        # Клавиши
        for _ in range(step // 2):
            self._press_key("volume_up")
        return self.get_volume()
    
    def volume_down(self, step=10):
        """Уменьшить громкость."""
        if VOLUME_OK:
            current = self.get_volume()
            return self.set_volume(current - step)
        
        for _ in range(step // 2):
            self._press_key("volume_down")
        return self.get_volume()
    
    def mute(self):
        """Включить/выключить звук."""
        if VOLUME_OK:
            try:
                muted = volume.GetMute()
                volume.SetMute(not muted, None)
                print(f"  {'🔇 Mute' if not muted else '🔊 Звук включён'}")
                return not muted
            except:
                pass
        
        self._press_key("volume_mute")
        return None
    
    def is_muted(self):
        """Проверяет, выключен ли звук."""
        if VOLUME_OK:
            try:
                return volume.GetMute()
            except:
                pass
        return False
    
    def _press_volume_keys(self, target_level):
        """Устанавливает громкость клавишами (приблизительно)."""
        try:
            import keyboard
            
            # Сначала в 0
            for _ in range(50):
                keyboard.press_and_release("volume_down")
            
            # Потом вверх до нужного
            for _ in range(target_level // 2):
                keyboard.press_and_release("volume_up")
        except:
            pass
    
    def _press_key(self, key):
        """Нажимает клавишу."""
        try:
            import keyboard
            keyboard.press_and_release(key)
        except:
            pass


# ============================================================
# ТЕСТ
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  ТЕСТ УПРАВЛЕНИЯ ГРОМКОСТЬЮ")
    print("=" * 50)
    
    vc = VolumeControl()
    
    print(f"\n  Текущая громкость: {vc.get_volume()}%")
    print(f"  Звук выключен: {vc.is_muted()}")
    print()
    print("  Команды:")
    print("  up — громче")
    print("  down — тише")
    print("  50 — установить 50%")
    print("  mute — переключить звук")
    print("  exit — выход\n")
    
    while True:
        cmd = input("  > ").strip().lower()
        
        if cmd == "exit":
            break
        elif cmd == "up":
            vc.volume_up()
            print(f"  Громкость: {vc.get_volume()}%")
        elif cmd == "down":
            vc.volume_down()
            print(f"  Громкость: {vc.get_volume()}%")
        elif cmd == "mute":
            vc.mute()
        elif cmd.isdigit():
            vc.set_volume(int(cmd))
        else:
            print("  Неизвестно")