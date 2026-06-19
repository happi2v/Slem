@echo off
chcp 65001 >nul
title Удаление Джарвиса

echo ================================================
echo   УДАЛЕНИЕ ДЖАРВИСА v42.0
echo ================================================
echo.
echo   Это удалит:
echo   - Python-зависимости Джарвиса
echo   - Папку models (обученные модели)
echo   - Временные файлы (.mp3, .wav)
echo   - Ярлык с рабочего стола
echo.
echo   Файлы проекта останутся.
echo.

choice /c YN /m "  Продолжить? (Y - да, N - нет)"
if errorlevel 2 goto :cancel
if errorlevel 1 goto :uninstall

:uninstall
echo.
echo   Удаление...

:: Зависимости
echo [1/4] Удаление Python-зависимостей...
pip uninstall faster-whisper pyaudio edge-tts numpy -y >nul 2>&1
pip uninstall keyboard pyautogui pyperclip -y >nul 2>&1
pip uninstall comtypes psutil gputil pillow -y >nul 2>&1
pip uninstall ollama -y >nul 2>&1
echo   ✓ Зависимости удалены

:: Модели
echo [2/4] Удаление моделей...
if exist "models" (
    rmdir /s /q "models"
    echo   ✓ Папка models удалена
) else (
    echo   • Папка models не найдена
)

:: Временные файлы
echo [3/4] Очистка временных файлов...
if exist "*.mp3" del /q "*.mp3" >nul 2>&1
if exist "*.wav" del /q "*.wav" >nul 2>&1
if exist "*.pt"  del /q "*.pt"  >nul 2>&1
if exist "jarvis_speech.mp3" del /q "jarvis_speech.mp3" >nul 2>&1
if exist "jarvis_fast.mp3"   del /q "jarvis_fast.mp3"   >nul 2>&1
if exist "test_tts.mp3"      del /q "test_tts.mp3"      >nul 2>&1
if exist "jarvis_icon.png"   del /q "jarvis_icon.png"   >nul 2>&1
echo   ✓ Временные файлы удалены

:: Ярлык
echo [4/4] Удаление ярлыка...
if exist "%userprofile%\Desktop\Джарвис.lnk" (
    del /q "%userprofile%\Desktop\Джарвис.lnk"
    echo   ✓ Ярлык удалён
) else (
    echo   • Ярлык не найден
)

echo.
echo ================================================
echo   ДЖАРВИС УДАЛЁН
echo ================================================
echo.
echo   Файлы проекта сохранены.
echo   Для полного удаления удалите папку вручную.
echo.
goto :end

:cancel
echo.
echo   Удаление отменено.

:end
echo.
pause