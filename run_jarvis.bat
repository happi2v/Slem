@echo off
chcp 65001 >nul
title Джарвис - Голосовой ассистент

echo ================================================
echo   ДЖАРВИС - ЗАПУСК
echo ================================================
echo.

:: Проверка Ollama
echo [1/3] Проверка Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo   ✓ Ollama работает
) else (
    echo   Запускаю Ollama...
    start "" "ollama" serve
    timeout /t 3 /nobreak >nul
    echo   ✓ Ollama запущена
)

:: Виртуальное окружение
echo [2/3] Проверка окружения...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo   ✓ Виртуальное окружение
) else (
    echo   • Системный Python
)

:: Модель Wake Word
if exist "models\джарвис_model.json" (
    echo   ✓ Модель Wake Word найдена
) else (
    echo   ! Модель не найдена!
    echo   Запустите: python train_wakeword.py
)

:: Запуск
echo [3/3] Запуск Джарвиса...
echo.
echo ================================================
echo   Джарвис запускается...
echo   Для выхода скажите "пока"
echo ================================================
echo.

python jarvis_core.py

if errorlevel 1 (
    echo.
    echo ================================================
    echo   ОШИБКА! Нажмите любую клавишу...
    echo ================================================
    pause
)