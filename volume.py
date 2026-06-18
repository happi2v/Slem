# volume.py
"""
Управление системной громкостью Windows.
Быстрая версия без зависимостей.
"""
import ctypes
import time
import subprocess


class VolumeControl:
    """Управление громкостью."""
    
    def __init__(self):
        self.ok = False
        
        # Пробуем WinMM
        try:
            self.winmm = ctypes.windll.winmm
            vol = ctypes.c_uint()
            result = self.winmm.waveOutGetVolume(0, ctypes.byref(vol))
            if result == 0:
                self.ok = True
                current = int((vol.value & 0xFFFF) / 0xFFFF * 100)
                print(f"  ✓ Громкость: {current}%")
                return
        except:
            pass
        
        print("  ✓ Громкость: клавиши")
    
    def get_volume(self):
        if self.ok:
            try:
                vol = ctypes.c_uint()
                self.winmm.waveOutGetVolume(0, ctypes.byref(vol))
                return int((vol.value & 0xFFFF) / 0xFFFF * 100)
            except:
                self.ok = False
        return 50
    
    def set_volume(self, level):
        level = max(0, min(100, level))
        
        if self.ok:
            try:
                val = int(level / 100.0 * 0xFFFF)
                both = val | (val << 16)
                self.winmm.waveOutSetVolume(0, both)
                return level
            except:
                self.ok = False
        
        # Fallback: PowerShell + SendKeys (без keyboard!)
        try:
            presses = level // 2
            # Вниз до 0
            ps_down = '''Add-Type -AssemblyName System.Windows.Forms; for($i=0;$i<50;$i++){[System.Windows.Forms.SendKeys]::SendWait("{DOWN}")}'''
            subprocess.run(["powershell", "-Command", ps_down], capture_output=True, shell=True, timeout=3)
            time.sleep(0.1)
            # Вверх до уровня
            ps_up = f'Add-Type -AssemblyName System.Windows.Forms; for($i=0;$i<{presses};$i++){{[System.Windows.Forms.SendKeys]::SendWait("{{UP}}")}}'
            subprocess.run(["powershell", "-Command", ps_up], capture_output=True, shell=True, timeout=3)
        except:
            pass
        
        return level
    
    def volume_up(self, step=10):
        return self.set_volume(self.get_volume() + step)
    
    def volume_down(self, step=10):
        return self.set_volume(self.get_volume() - step)
    
    def mute(self):
        try:
            ps = 'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait("{VOLUME_MUTE}")'
            subprocess.run(["powershell", "-Command", ps], capture_output=True, shell=True, timeout=2)
        except:
            pass
    
    def is_muted(self):
        return False