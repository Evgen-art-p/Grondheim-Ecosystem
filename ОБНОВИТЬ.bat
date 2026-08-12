@echo off
chcp 65001 >nul
cd /d "%~dp0"
title ОБНОВИТЬ ГОРОД
where py >nul 2>&1
if %errorlevel%==0 ( py -3 "obnovit.py" & goto :k )
where python >nul 2>&1
if %errorlevel%==0 ( python "obnovit.py" & goto :k )
echo.
echo   Питон не найден.
echo.
pause
:k
