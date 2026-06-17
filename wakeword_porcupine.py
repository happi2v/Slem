# wakeword_porcupine.py
import struct
import threading
import time
import pvporcupine
from pvrecorder import PvRecorder

class PorcupineWakeWord:
    def __init__(self, access_key=None, keywords=None, sensitivities=None):
        """
        Детектор ключевых фраз на основе Porcupine.
        
        Параметры:
        - access_key: ключ доступа с console.picovoice.ai (бесплатный)
        - keywords: список ключевых слов (можно использовать встроенные или кастомные)
        - sensitivities: чувствительность для каждого слова (0.0 - 1.0)
        """
        self.access_key = access_key or self._get_access_key()
        self.keywords = keywords or ["jarvis"]
        self.sensitivities = sensitivities or [0.7]
        
        # Создаём экземпляр Porcupine
        self.porcupine = pvporcupine.create(
            access_key=self.access_key,
            keywords=self.keywords,
            sensitivities=self.sensitivities
        )
        
        # Создаём рекордер
        self.recorder = PvRecorder(
            device_index=-1,
            frame_length=self.porcupine.frame_length
        )
        
        self.running = False
        self.detection_callbacks = []
        self.listen_thread = None
        
        print(f"Porcupine Wake Word готов. Слушаю: {self.keywords}")
        
    @staticmethod
    def _get_access_key():
        """Получает ключ доступа. Можно хранить в переменной окружения."""
        import os
        key = os.environ.get("PICOVOICE_ACCESS_KEY", "")
        if not key:
            print("=" * 50)
            print("ВНИМАНИЕ: Требуется бесплатный Access Key от Picovoice!")
            print("1. Зайдите на https://console.picovoice.ai/")
            print("2. Зарегистрируйтесь (бесплатно)")
            print("3. Скопируйте ваш Access Key")
            print("4. Установите переменную окружения:")
            print("   export PICOVOICE_ACCESS_KEY='ваш_ключ'")
            print("=" * 50)
            # Временно используем демо-ключ (может не работать)
            key = input("Введите ваш Access Key (или Enter для пропуска): ").strip()
        return key
        
    def on_detected(self, callback):
        """Регистрирует функцию обратного вызова."""
        self.detection_callbacks.append(callback)
        
    def _trigger_callbacks(self):
        """Вызывает все зарегистрированные колбэки."""
        for callback in self.detection_callbacks:
            callback()
            
    def start_listening(self):
        """Запускает фоновый поток прослушивания."""
        self.running = True
        self.recorder.start()
        
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        print("Жду фразу 'Джарвис'...")
        
    def _listen_loop(self):
        """Основной цикл прослушивания."""
        while self.running:
            try:
                pcm = self.recorder.read()
                result = self.porcupine.process(pcm)
                
                if result >= 0:
                    print(f"Wake Word обнаружен! (индекс: {result})")
                    self._trigger_callbacks()
                    time.sleep(0.5)  # Защита от повторных срабатываний
                    
            except Exception as e:
                print(f"Ошибка в Wake Word: {e}")
                
    def stop(self):
        """Останавливает детектор."""
        self.running = False
        if self.recorder:
            self.recorder.stop()
        if self.porcupine:
            self.porcupine.delete()
        print("Wake Word детектор остановлен.")