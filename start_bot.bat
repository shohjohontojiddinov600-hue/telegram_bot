@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -Command "Stop-Process -Name pythonw -Force -ErrorAction SilentlyContinue; Start-Process -FilePath '.\.venv\bin\pythonw.exe' -ArgumentList 'bot.py'"
echo ==============================================================
echo   Universal PRO Bot orqa fonda muvaffaqiyatli ishga tushirildi!
echo   Antigravity IDE ni bemalol yopishingiz mumkin.
echo ==============================================================
