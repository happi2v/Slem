# wakeword.py
import pyaudio
import numpy as np
import threading
import time
import queue
from openwakeword.model import Model

class WakeWordDetector:
    def __init__(self, wake_word_models=None, sensitivity=0.5):
        """
        Детектор ключевых фраз.
        
        Параметры:
        - wake_word_models: список путей к моделям .tflite 
          (если None, использует встроенную "alexa")
        - sensitivity: чувствительность (0.0 - 1.0)
        """
        self.sensitivity = sensitivity
        self.CHUNK = 1280  # Размер буфера для OpenWakeWord
        self.RATE = 16000
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        # Загружаем модель
        if wake_word_models is None:
            # Используем встроенные модели
            # Они активируются на "Alexa", но мы можем добавить свои
            self.model = Model(wakeword_models=["alexa"], inference_framework="tflite")
            print("Wake Word модель загружена (встроенная 'alexa').")
            print("ВНИМАНИЕ: Для русского 'Джарвис' нужна кастомная модель.")
            print("Пока реагирует на любое слово, похожее на активацию.")
        else:
            self.model = Model(wakeword_models=wake_word_models, inference_framework="tflite")
        
        self.audio = pyaudio.PyAudio()
        self.detected = False
        self.running = False
        self.stream = None
        self.detection_callbacks = []
        
    def on_detected(self, callback):
        """Регистрирует функцию обратного вызова при обнаружении."""
        self.detection_callbacks.append(callback)
        
    def _trigger_callbacks(self):
        """Вызывает все зарегистрированные колбэки."""
        for callback in self.detection_callbacks:
            callback()
            
    def start_listening(self):
        """Запускает фоновый поток для постоянного прослушивания."""
        self.running = True
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        # Запускаем в отдельном потоке
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        print("Wake Word детектор запущен. Жду ключевую фразу...")
        
    def _listen_loop(self):
        """Основной цикл прослушивания."""
        while self.running:
            try:
                # Читаем аудиоданные
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                audio_array = np.frombuffer(data, dtype=np.int16)
                
                # Передаем в модель для предсказания
                prediction = self.model.predict(audio_array)
                
                # Проверяем все модели на превышение порога
                for model_name, score in prediction.items():
                    if score > self.sensitivity:
                        print(f"Wake Word обнаружен! ({model_name}: {score:.3f})")
                        self._trigger_callbacks()
                        # Небольшая пауза, чтобы избежать множественных срабатываний
                        time.sleep(0.5)
                        
            except Exception as e:
                print(f"Ошибка в Wake Word детекторе: {e}")
                
    def stop(self):
        """Останавливает детектор."""
        self.running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        print("Wake Word детектор остановлен.")