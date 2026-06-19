@echo off
chcp 65001 >nul
title Установка Джарвиса

echo ================================================
echo   УСТАНОВКА ДЖАРВИСА
echo ================================================
echo.

:: Проверка Python
echo [1/6] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ✗ Python не найден!
    echo   Скачайте: https://python.org/downloads
    pause
    exit /b
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo   ✓ Python %PYVER%

:: Обновление pip
echo [2/6] Обновление pip...
python -m pip install --upgrade pip --quiet
echo   ✓ pip обновлён

:: Основные зависимости
echo [3/6] Установка основных библиотек...
pip install pyaudio faster-whisper edge-tts numpy --quiet
if errorlevel 1 (
    echo   ✗ Ошибка установки
    pause
    exit /b
)
echo   ✓ Основные библиотеки

:: Системные библиотеки
echo [4/6] Установка системных библиотек...
pip install keyboard pyautogui pyperclip --quiet
pip install psutil gputil --quiet
echo   ✓ Системные библиотеки

:: GUI
echo [5/6] Установка GUI...
pip install pillow --quiet
echo   ✓ GUI

:: Ollama
echo [6/6] Проверка Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo   ! Ollama не установлена
    echo   Скачайте: https://ollama.com/download
    echo   После установки: ollama pull llama3.2:3b
) else (
    echo   ✓ Ollama найдена
    echo   Загрузка LLM модели...
    ollama pull llama3.2:3b
)

:: Готово
echo.
echo ================================================
echo   УСТАНОВКА ЗАВЕРШЕНА!
echo.
echo   Обучение: python train_wakeword.py
echo   Запуск:   python jarvis_core.py
echo             run_jarvis.bat
echo ================================================
pause