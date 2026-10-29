@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==============================================================
echo   KOMPYUTERNI AVTO-ISHLASH REJIMIGA SOZLASH
echo ==============================================================
echo.
echo 1. Kompyuter uyquga (Sleep) ketmasligi sozlanmoqda...
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0

echo 2. Ekran quvvatni tejash uchun 10 daqiqada o'chadi (lekin bot to'xtamaydi)...
powercfg /change monitor-timeout-ac 10

echo 3. Noutbuk qopqog'i yopilganda ham bot to'xtamasligi sozlanmoqda...
powercfg /setacvalueindex SCHEME_CURRENT 4f971e89-eebd-4455-a8de-9e59040e7347 5ca83367-6e45-459f-a27b-476b1d01c936 0 >nul 2>&1
powercfg /setactive SCHEME_CURRENT >nul 2>&1

echo 4. Bot orqa fonda qayta ishga tushirilmoqda...
powershell -NoProfile -Command "Stop-Process -Name pythonw -Force -ErrorAction SilentlyContinue; Start-Process -FilePath '.\.venv\bin\pythonw.exe' -ArgumentList 'bot.py'"

echo.
echo ==============================================================
echo   MUVAFFAQIYATLI SOZLANDI!
echo.
echo   - Endi siz kompyuterga umuman tegmasangiz ham,
echo   - Noutbuk qopqog'ini yopib qo'ysangiz ham,
echo   - Bot orqa fonda 24/7 uzluksiz ishlayveradi!
echo ==============================================================
echo.
pause

