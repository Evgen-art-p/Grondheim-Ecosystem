@echo off
chcp 65001 >nul
cd /d "%~dp0"
title КАРТРИДЖ ЦЕХА
where py >nul 2>&1
if %errorlevel%==0 ( py -3 "ceh_kartridzh.py" & goto :k )
where python >nul 2>&1
if %errorlevel%==0 ( python "ceh_kartridzh.py" & goto :k )
echo.
echo   Питон не найден.
echo.
pause
:k
