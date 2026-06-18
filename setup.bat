@echo off
chcp 65001 >nul
title Установка Джарвиса

echo ================================================
echo   УСТАНОВКА ДЖАРВИСА
echo ================================================
echo.

:: Проверка Python
echo [1/7] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ✗ Python не найден!
    echo   Скачайте: https://python.org/downloads
    pause
    exit /b
)
echo   ✓ Python найден

:: Обновление pip
echo [2/7] Обновление pip...
python -m pip install --upgrade pip --quiet
echo   ✓ pip обновлён

:: Основные зависимости
echo [3/7] Установка основных библиотек...
pip install pyaudio faster-whisper edge-tts pygame numpy --quiet
echo   ✓ Основные библиотеки

:: Wake Word и GUI
echo [4/7] Установка GUI и трея...
pip install pystray pillow --quiet
echo   ✓ GUI и трей

:: Управление системой
echo [5/7] Установка системных библиотек...
pip install keyboard pyautogui pyperclip pycaw comtypes --quiet
echo   ✓ Системные библиотеки

:: Ollama
echo [6/7] Проверка Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo   ! Ollama не установлена!
    echo   Скачайте: https://ollama.com/download
    echo   После установки запустите: ollama pull llama3.2:3b
) else (
    echo   ✓ Ollama найдена
    echo   Загрузка LLM модели...
    ollama pull llama3.2:3b
)

:: Иконка
echo [7/7] Создание иконки...
python generate_icon.py >nul 2>&1
echo   ✓ Иконка создана

echo.
echo ================================================
echo   УСТАНОВКА ЗАВЕРШЕНА!
echo.
echo   Запуск Джарвиса: run_jarvis.bat
echo   Обучение: python train_wakeword.py
echo ================================================
pause