@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo =========================================
echo   BOT HOLATINI TEKSHIRISH
echo =========================================
tasklist /fi "imagename eq pythonw.exe" | findstr /i "pythonw.exe" >nul
if %errorlevel% equ 0 (
    echo   [+] BOT ISHLAMOQDA! (Orqa fonda faol)
) else (
    echo   [-] BOT ISHLAMAYAPTI (To'xtatilgan)
)
echo =========================================
echo.
pause
