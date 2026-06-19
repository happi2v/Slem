@echo off
chcp 65001 >nul
title Установка Джарвиса

echo ================================================
echo   УСТАНОВКА ДЖАРВИСА v42.0
echo ================================================
echo.

:: Проверка Python
echo [1/5] Проверка Python...
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
echo [2/5] Обновление pip...
python -m pip install --upgrade pip --quiet
echo   ✓ pip обновлён

:: Основные зависимости
echo [3/5] Установка зависимостей...
echo   • faster-whisper (распознавание)...
pip install faster-whisper --quiet
echo   • edge-tts (синтез речи)...
pip install edge-tts --quiet
echo   • pyaudio (микрофон)...
pip install pyaudio --quiet
echo   • numpy (обработка)...
pip install numpy --quiet
echo   • comtypes (Windows SAPI)...
pip install comtypes --quiet
echo   • keyboard (клавиши)...
pip install keyboard --quiet
echo   • pyautogui (автоматизация)...
pip install pyautogui --quiet
echo   • pyperclip (буфер обмена)...
pip install pyperclip --quiet
echo   • psutil (мониторинг)...
pip install psutil --quiet
echo   • gputil (GPU монитор)...
pip install gputil --quiet
echo   • pillow (изображения)...
pip install pillow --quiet
echo   ✓ Все зависимости установлены

:: Проверка Ollama
echo [4/5] Проверка Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo   ! Ollama не установлена
    echo   Скачайте: https://ollama.com/download
    echo   После установки выполните: ollama pull llama3.2:3b
) else (
    echo   ✓ Ollama найдена
    echo   Загрузка модели llama3.2:3b...
    ollama pull llama3.2:3b
)

:: Генерация иконки
echo [5/5] Генерация иконки...
python -c "from PIL import Image,ImageDraw;img=Image.new('RGBA',(64,64),(0,0,0,0));d=ImageDraw.Draw(img);d.ellipse([6,6,58,58],fill=(30,100,220),outline=(60,140,255),width=2);d.text((22,12),'J',fill=(255,255,255));img.save('jarvis_icon.png')" 2>nul
if exist "jarvis_icon.png" (
    echo   ✓ Иконка создана
) else (
    echo   • Иконка не создана
)

:: Готово
echo.
echo ================================================
echo   УСТАНОВКА ЗАВЕРШЕНА!
echo.
echo   Обучение Wake Word:
echo     python train_wakeword.py
echo.
echo   Запуск Джарвиса:
echo     python jarvis_core.py
echo     run_jarvis.bat
echo ================================================
echo.
echo   ! Для LLM нужна Ollama
echo.
pause