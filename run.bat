@echo off
REM QuickBooks Desktop Test Tool - Launch Script
REM Convenience script for running from source

echo Starting QBD Test Tool...
echo.
echo Make sure QuickBooks Desktop is running with a company file open!
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.11 or higher from python.org
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import win32com.client" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Required dependencies not installed
    echo.
    echo Run this command first:
    echo pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Launch the application
python src\app.py

REM If the script exits with an error, pause so user can see it
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
