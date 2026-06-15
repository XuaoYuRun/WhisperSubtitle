@echo off
chcp 437 >nul

cd /d "%~dp0"

if not exist "whisper_env\Scripts\pythonw.exe" (
    msg * "Error: Virtual environment not found!"
    exit /b 1
)

start "" "whisper_env\Scripts\pythonw.exe" "src\gui\WhisperPyQtGUI.py"
