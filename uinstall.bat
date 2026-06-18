@echo off
chcp 65001 >nul
title Удаление Джарвиса

echo ================================================
echo   УДАЛЕНИЕ ДЖАРВИСА
echo ================================================
echo.

echo   Внимание! Будут удалены:
echo   - Все файлы проекта
echo   - Виртуальное окружение (venv)
echo   - Папка с моделями
echo.

choice /c YN /m "  Вы уверены? (Y - да, N - нет)"
if errorlevel 2 goto :cancel
if errorlevel 1 goto :uninstall

:uninstall
echo.
echo   Удаление...

:: Удаление Python-пакетов (опционально)
choice /c YN /m "  Удалить Python-зависимости? (Y/N)"
if errorlevel 2 goto :skip_pip
if errorlevel 1 (
    echo   Удаляю пакеты...
    pip uninstall pyaudio faster-whisper edge-tts pygame numpy -y >nul 2>&1
    pip uninstall pystray pillow keyboard pyautogui pyperclip -y >nul 2>&1
    pip uninstall pycaw comtypes ollama -y >nul 2>&1
    echo   ✓ Пакеты удалены
)

:skip_pip
:: Удаление виртуального окружения
if exist "venv" (
    echo   Удаляю venv...
    rmdir /s /q "venv"
    echo   ✓ venv удалён
)

:: Удаление моделей
if exist "models" (
    echo   Удаляю модели...
    rmdir /s /q "models"
    echo   ✓ Модели удалены
)

:: Удаление иконки
if exist "jarvis_icon.png" (
    del /q "jarvis_icon.png"
    echo   ✓ Иконка удалена
)

:: Удаление ярлыка с рабочего стола
if exist "%userprofile%\Desktop\Джарвис.lnk" (
    del /q "%userprofile%\Desktop\Джарвис.lnk"
    echo   ✓ Ярлык удалён
)

echo.
echo ================================================
echo   ДЖАРВИС ПОЛНОСТЬЮ УДАЛЁН
echo ================================================
goto :end

:cancel
echo.
echo   Удаление отменено.

:end
echo.
pause