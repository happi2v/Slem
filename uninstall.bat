@echo off
chcp 65001 >nul
title Удаление Джарвиса

echo ================================================
echo   УДАЛЕНИЕ ДЖАРВИСА
echo ================================================
echo.
echo   Внимание! Будут удалены:
echo   - Python-зависимости
echo   - Папка models
echo   - Файлы кэша и логов
echo.
echo   Файлы проекта НЕ удаляются.
echo.

choice /c YN /m "  Продолжить? (Y - да, N - нет)"
if errorlevel 2 goto :cancel
if errorlevel 1 goto :uninstall

:uninstall
echo.
echo   Удаление...

:: Python-зависимости
echo [1/3] Удаление Python-зависимостей...
pip uninstall pyaudio faster-whisper edge-tts numpy -y >nul 2>&1
pip uninstall keyboard pyautogui pyperclip -y >nul 2>&1
pip uninstall psutil gputil pillow -y >nul 2>&1
pip uninstall ollama -y >nul 2>&1
echo   ✓ Зависимости удалены

:: Модели
echo [2/3] Удаление моделей...
if exist "models" (
    rmdir /s /q "models"
    echo   ✓ Папка models удалена
) else (
    echo   • Папка models не найдена
)

:: Временные файлы
echo [3/3] Очистка временных файлов...
if exist "*.mp3" del /q "*.mp3" >nul 2>&1
if exist "*.wav" del /q "*.wav" >nul 2>&1
if exist "jarvis_icon.png" del /q "jarvis_icon.png" >nul 2>&1
if exist "test_tts.mp3" del /q "test_tts.mp3" >nul 2>&1
echo   ✓ Временные файлы удалены

:: Ярлык
if exist "%userprofile%\Desktop\Джарвис.lnk" (
    del /q "%userprofile%\Desktop\Джарвис.lnk"
    echo   ✓ Ярлык с рабочего стола удалён
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