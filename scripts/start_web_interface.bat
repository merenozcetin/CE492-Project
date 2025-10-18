@echo off
echo Starting SeaRoute Web Interface...
echo.

REM Add Java to PATH for this session
set PATH=%PATH%;C:\Program Files\Java\jdk-25\bin

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.6 or higher
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Java is installed
java --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Java is not installed or not in PATH
    echo Please install Java JDK 9 or higher
    echo See docs\SETUP_GUIDE.md for installation instructions
    pause
    exit /b 1
)

REM Start the web server
cd ..\web-interface
python searoute_server.py

pause
