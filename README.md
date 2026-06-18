# Slem
# Библиотеки которые надо скачать)) 
  ●pip install pyaudio faster-whisper openwakeword numpy  
  **PyAudio — для захвата звука с микрофона**  
  *Faster-Whisper — для распознавания речи*  
  *OpenWakeWord — для обнаружения ключевой фразы (чтобы не распознавать всё подряд)*  

Скачайте и установите: https://ollama.com/download
1.  Установите необходимые библиотеки:
    ```bash
    После установки скачайте модель:
    ollama pull llama3.2:3b
    ```



## Установка
1.  Установите необходимые библиотеки:
    ```bash
    pip install pyaudio faster-whisper openwakeword numpy
    pip install edge-tts pygame
    pip install openwakeword pydub
    pip install pvporcupine pvrecorder
    pip install openwakeword
    pip install pyaudio numpy
    pip install torch
    pip install torch --index-url https://download.pytorch.org/whl/cu121
    # Для CUDA 12.1
    pip install torch --index-url https://download.pytorch.org/whl/cu121
    # Для CUDA 11.8
    pip install torch --index-url https://download.pytorch.org/whl/cu118
    ```
2.  Обучите модель:
    ```bash
    Запустите файл и сделайте от 10 до 30 записей
    train_wakeword.py
    ```
    pip install ollama
