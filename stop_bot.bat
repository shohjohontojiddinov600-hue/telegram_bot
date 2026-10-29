@echo off
chcp 65001 >nul
powershell -NoProfile -Command "Stop-Process -Name pythonw -Force -ErrorAction SilentlyContinue"
echo =========================================
echo   Bot muvaffaqiyatli to'xtatildi!
echo =========================================
