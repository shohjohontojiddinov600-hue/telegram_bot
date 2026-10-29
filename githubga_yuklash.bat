@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==============================================================
echo   YANGI KODLARNI GITHUBGA VA RENDER SERVERIGA YUKLASH
echo ==============================================================
echo.

git add .
git commit -m "Add Render port check and new languages"
git branch -M main
git push -u origin main

echo.
if %errorlevel% equ 0 (
    echo ==============================================================
    echo   [V] TABRIKLAYMIZ! Kodlar GitHubga muvaffaqiyatli yuklandi!
    echo   Endi Render.com da 1 daqiqada bot "Live" (yashil) bo'ladi!
    echo ==============================================================
) else (
    echo ==============================================================
    echo   [X] Yuklashda xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.
    echo ==============================================================
)
echo.
pause
