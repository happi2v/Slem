# gui.py
"""
Графический интерфейс Джарвиса — Steam оверлей, правый верхний угол.
"""
import threading
import time
import os
import sys

try:
    import tkinter as tk
    from tkinter import Canvas, Label, Frame
    GUI_OK = True
except ImportError:
    GUI_OK = False

try:
    import psutil
    PSUTIL_OK = True
except:
    PSUTIL_OK = False

try:
    import GPUtil
    GPUTIL_OK = True
except:
    GPUTIL_OK = False

INTERVAL = 1000


class Monitor:
    def __init__(self):
        self.ok = PSUTIL_OK
        self.gpu_ok = GPUTIL_OK
    
    def stats(self):
        cpu = ram = gpu = 0
        if self.ok:
            try:
                cpu = psutil.cpu_percent(interval=0.0)
                ram = psutil.virtual_memory().percent
            except: pass
        if self.gpu_ok:
            try:
                gpus = GPUtil.getGPUs()
                if gpus: gpu = gpus[0].load * 100
            except: pass
        return cpu, ram, gpu


class GUI:
    def __init__(self, core=None):
        self.core = core
        self.root = None
        self.running = True
        self.listening = False
        self.speaking = False
        self.monitor = Monitor()
        
        if GUI_OK:
            # Запускаем в ОТДЕЛЬНОМ ПОТОКЕ
            t = threading.Thread(target=self._run, daemon=True)
            t.start()
            time.sleep(0.3)
    
    def _run(self):
        self.root = tk.Tk()
        self.root.title("JARVIS")
        self.root.geometry("200x130")
        self.root.configure(bg="#0d1117")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)
        self.root.overrideredirect(True)
        
        sw = self.root.winfo_screenwidth()
        self.root.geometry(f"200x130+{sw - 210}+10")
        
        f = Frame(self.root, bg="#0d1117", padx=8, pady=5)
        f.pack(fill="both", expand=True)
        
        h = Frame(f, bg="#0d1117")
        h.pack(fill="x")
        Label(h, text="J.A.R.V.I.S.", font=("Segoe UI", 8, "bold"),
              fg="#58a6ff", bg="#0d1117").pack(side="left")
        x = Label(h, text="×", font=("Segoe UI", 8), fg="#f85149",
                   bg="#0d1117", cursor="hand2")
        x.pack(side="right")
        x.bind("<Button-1>", lambda e: self._stop())
        
        Canvas(f, height=1, bg="#21262d", highlightthickness=0).pack(fill="x", pady=3)
        
        self.status = Label(f, text="● Ожидание", font=("Segoe UI", 7),
                            fg="#8b949e", bg="#0d1117")
        self.status.pack(anchor="w")
        
        self.vol = Label(f, text="🔊 --", font=("Segoe UI", 6),
                          fg="#484f58", bg="#0d1117")
        self.vol.pack(anchor="w")
        
        self.cpu_txt, self.cpu_bar = self._bar(f, "CPU", "#f0883e")
        self.ram_txt, self.ram_bar = self._bar(f, "RAM", "#58a6ff")
        self.gpu_txt, self.gpu_bar = self._bar(f, "GPU", "#a371f7")
        
        self._tick()
        self.root.mainloop()
    
    def _bar(self, parent, label, color):
        f = Frame(parent, bg="#0d1117")
        f.pack(fill="x", pady=1)
        lbl = Label(f, text=f"{label}  0%", font=("Segoe UI", 7),
                     fg="#8b949e", bg="#0d1117", width=7, anchor="w")
        lbl.pack(side="left")
        bar = Canvas(f, height=5, bg="#21262d", highlightthickness=0)
        bar.pack(side="left", fill="x", expand=True, padx=4)
        return lbl, bar
    
    def _tick(self):
        if not self.running: return
        try:
            if self.listening: t, c = "● Слушаю...", "#58a6ff"
            elif self.speaking: t, c = "● Говорю...", "#3fb950"
            else: t, c = "● Ожидание", "#8b949e"
            self.status.config(text=t, fg=c)
            
            if self.core and self.core.volume:
                try: self.vol.config(text=f"🔊 {self.core.volume.get_volume()}%")
                except: pass
            
            cpu, ram, gpu = self.monitor.stats()
            self.cpu_txt.config(text=f"CPU {cpu:3.0f}%")
            self._draw(self.cpu_bar, cpu, "#f0883e")
            self.ram_txt.config(text=f"RAM {ram:3.0f}%")
            self._draw(self.ram_bar, ram, "#58a6ff")
            self.gpu_txt.config(text=f"GPU {gpu:3.0f}%" if gpu > 0 else "GPU  --")
            self._draw(self.gpu_bar, gpu, "#a371f7")
        except tk.TclError: return
        self.root.after(INTERVAL, self._tick)
    
    def _draw(self, canvas, pct, color):
        try:
            canvas.delete("all")
            w = max(canvas.winfo_width(), 1)
            canvas.create_rectangle(0, 0, w, 5, fill="#21262d", outline="")
            canvas.create_rectangle(0, 0, w * min(pct, 100) / 100, 5, fill=color, outline="")
        except: pass
    
    def _stop(self):
        self.running = False
        if self.core: self.core.running = False
        try: self.root.destroy()
        except: pass
    
    def set_listening(self, v=True): self.listening = v
    def set_speaking(self, v=True): self.speaking = v