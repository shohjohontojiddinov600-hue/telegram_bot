@echo off
chcp 65001 >nul

echo Avtomatik ishga tushirish tekshirilmoqda...
powershell -NoProfile -Command "$startup = [Environment]::GetFolderPath('Startup') + '\TelegramBot_Autostart.vbs'; if (Test-Path $startup) { Remove-Item $startup -Force; Write-Host 'Avtomatik ishga tushirish O''CHIRILDI!' -ForegroundColor Yellow } else { Write-Host 'Avtomatik ishga tushirish allaqachon o''chirilgan.' -ForegroundColor Cyan }"

echo.
echo ==============================================================
echo   Kompyuter yoqilganda bot avtomatik ishga tushishi to'xtatildi.
echo ==============================================================
echo.
pause

