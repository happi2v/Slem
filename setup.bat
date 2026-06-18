:: setup.bat — запустить ОДИН раз для установки
@echo off
chcp 65001 >nul
title Установка Джарвиса

echo ================================================
echo   УСТАНОВКА ДЖАРВИСА
echo ================================================
echo.

echo [1/5] Установка Python-зависимостей...
pip install pyaudio faster-whisper edge-tts pygame numpy pystray pillow ollama
echo   ✓ Готово

echo [2/5] Проверка Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo   ! Ollama не установлена!
    echo   Скачайте: https://ollama.com/download
    pause
    exit /b
)

echo [3/5] Загрузка LLM модели...
ollama pull llama3.2:3b
echo   ✓ Готово

echo [4/5] Создание иконки...
python generate_icon.py
echo   ✓ Готово

echo [5/5] Обучение Wake Word...
echo   Запустите позже: python train_wakeword.py
echo.

echo ================================================
echo   УСТАНОВКА ЗАВЕРШЕНА!
echo   Запуск: run_jarvis.bat
echo ================================================
pause