@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Avtomatik ishga tushirish sozlanmoqda...
powershell -NoProfile -Command "$startup = [Environment]::GetFolderPath('Startup') + '\TelegramBot_Autostart.vbs'; $vbs = 'Set WshShell = CreateObject(\"WScript.Shell\")' + [Environment]::NewLine + 'WshShell.Run \"powershell -NoProfile -Command \"\"Stop-Process -Name pythonw -Force -ErrorAction SilentlyContinue; Start-Process -FilePath ''%~dp0.venv\bin\pythonw.exe'' -ArgumentList ''bot.py'' -WorkingDirectory ''%~dp0''\"\"\", 0, False'; Set-Content -Path $startup -Value $vbs -Encoding ASCII"

echo.
echo ==============================================================
echo   AVTO-ISHGA TUSHIRISH MUVAFFAQIYATLI YOQILDI!
echo   Endi kompyuterni yoqqaningizda bot o'zi fonda ishga tushadi.
echo   Antigravity IDE ni ochish umuman shart emas!
echo ==============================================================
echo.
pause

