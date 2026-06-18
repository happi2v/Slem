@echo off
chcp 65001 >nul
title Джарвис - Голосовой ассистент

echo ================================================
echo   ДЖАРВИС - ЗАПУСК
echo ================================================
echo.

:: Проверяем, запущен ли Ollama
echo [1/4] Проверка Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo   ✓ Ollama уже запущена
) else (
    echo   Запускаю Ollama...
    start "" "ollama" serve
    timeout /t 3 /nobreak >nul
    echo   ✓ Ollama запущена
)

:: Активируем виртуальное окружение если есть
echo [2/4] Проверка окружения...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo   ✓ Виртуальное окружение активировано
) else (
    echo   • Системный Python
)

:: Проверяем наличие модели
echo [3/4] Проверка модели Wake Word...
if exist "models\джарвис_model.json" (
    echo   ✓ Модель найдена
) else (
    echo   ! Модель не найдена!
    echo   Запустите обучение: python train_wakeword.py
)

:: Запуск Джарвиса
echo [4/4] Запуск Джарвиса...
echo.
echo ================================================
echo   Джарвис запускается...
echo   Для выхода скажите "пока" или закройте окно
echo ================================================
echo.

python jarvis_core.py

:: Если упал с ошибкой
if errorlevel 1 (
    echo.
    echo ================================================
    echo   ОШИБКА! Что-то пошло не так.
    echo ================================================
    pause
)