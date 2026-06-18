# Slem
Нууу типо джарвиса пытаюсь сделать
# Библиотеки которые надо скачать)) 
 

Скачайте и установите: https://ollama.com/download
1.  Установите необходимые библиотеки:
    ```bash
    После установки скачайте модель:
    ollama pull llama3.2:3b
    pip install ollama
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
    
    
    pip install pystray pillow
    ```
2.  Обучите модель:
    ```bash
    Запустите файл и сделайте от 10 до 30 записей
    train_wakeword.py
    ```

## Запуск:
1.  перед этим обязательно установите необходимые библиотеки:
    ```bash
    Первый запуск — установка:

    Двойной клик на setup.bat

    Установит все зависимости и скачает LLM

    Обучение Wake Word:

    Двойной клик на train_wakeword.py

    Или в консоли: python train_wakeword.py

    Каждый день — запуск:

    Двойной клик на run_jarvis.bat

    Джарвис запускается, иконка в трее
    ```
git add .
git commit -m ""
git push origin "checkpoint name"
git checkout master
