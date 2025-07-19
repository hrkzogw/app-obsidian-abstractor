@echo off
REM Obsidian Abstractor - Run Script for Windows
REM This script sets up the environment and runs the application

setlocal enabledelayedexpansion

REM Get the directory of this script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Remove trailing backslash if present
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Virtual environment path
set "VENV_PATH=%SCRIPT_DIR%\venv"

REM Color codes for output
REM Note: Windows doesn't support ANSI colors in older versions

REM Function to find Python
set "PYTHON="
set "PYTHON_VERSION="

REM Check if virtual environment exists
if exist "%VENV_PATH%" (
    REM Activate existing virtual environment
    call "%VENV_PATH%\Scripts\activate.bat"
    echo Using existing virtual environment
    goto :check_config
)

REM Find suitable Python (try multiple commands)
echo Searching for Python 3.9+...

REM Try py launcher first (most reliable on Windows)
where py >nul 2>nul
if %errorlevel% equ 0 (
    REM Check for specific versions
    for %%v in (3.12 3.11 3.10 3.9) do (
        py -%%v --version >nul 2>nul
        if !errorlevel! equ 0 (
            set "PYTHON=py -%%v"
            set "PYTHON_VERSION=%%v"
            echo Found Python %%v
            goto :found_python
        )
    )
    REM Try default py command
    for /f "tokens=2" %%i in ('py --version 2^>^&1') do set "PY_VERSION=%%i"
    for /f "tokens=1,2 delims=." %%a in ("%PY_VERSION%") do (
        if %%a geq 3 if %%b geq 9 (
            set "PYTHON=py"
            set "PYTHON_VERSION=%PY_VERSION%"
            echo Found Python %PY_VERSION%
            goto :found_python
        )
    )
)

REM Try python3 command
where python3 >nul 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do set "PY_VERSION=%%i"
    for /f "tokens=1,2 delims=." %%a in ("%PY_VERSION%") do (
        if %%a geq 3 if %%b geq 9 (
            set "PYTHON=python3"
            set "PYTHON_VERSION=%PY_VERSION%"
            echo Found Python %PY_VERSION%
            goto :found_python
        )
    )
)

REM Try python command
where python >nul 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PY_VERSION=%%i"
    for /f "tokens=1,2 delims=." %%a in ("%PY_VERSION%") do (
        if %%a geq 3 if %%b geq 9 (
            set "PYTHON=python"
            set "PYTHON_VERSION=%PY_VERSION%"
            echo Found Python %PY_VERSION%
            goto :found_python
        )
    )
)

REM Python not found
echo Error: Python 3.9 or later is required.
echo Please install Python from: https://www.python.org/downloads/
echo.
echo Make sure to check "Add Python to PATH" during installation.
pause
exit /b 1

:found_python
REM Check if version is less than 3.11 (recommended)
for /f "tokens=2 delims=." %%i in ("%PYTHON_VERSION%") do (
    if %%i lss 11 (
        echo Warning: Python %PYTHON_VERSION% detected. Python 3.11+ recommended for better performance.
    )
)

REM Create virtual environment
echo Creating virtual environment...
%PYTHON% -m venv "%VENV_PATH%"
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
call "%VENV_PATH%\Scripts\activate.bat"

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>nul

REM Install dependencies
echo Installing dependencies...
if exist "pyproject.toml" (
    pip install -e . >nul 2>nul
    if !errorlevel! neq 0 (
        echo Error: Failed to install dependencies
        echo Please check pyproject.toml and try again
        pause
        exit /b 1
    )
) else (
    echo Error: pyproject.toml not found
    echo This may indicate an incomplete installation
    pause
    exit /b 1
)

echo Setup complete!

:check_config
REM Check if config exists
if not exist "config\config.yaml" (
    if exist "config\config.yaml.example" (
        echo.
        echo No configuration file found.
        echo Please copy config\config.yaml.example to config\config.yaml
        echo and configure your Google AI API key.
        echo.
        echo To get an API key, visit:
        echo https://makersuite.google.com/app/apikey
        pause
        exit /b 1
    )
)

REM Set PYTHONPATH to include current directory
if defined PYTHONPATH (
    set "PYTHONPATH=%PYTHONPATH%;%SCRIPT_DIR%"
) else (
    set "PYTHONPATH=%SCRIPT_DIR%"
)

REM Check if src directory exists
if not exist "%SCRIPT_DIR%\src" (
    echo Error: src directory not found at %SCRIPT_DIR%\src
    echo This may indicate an incomplete installation.
    echo Please run the installer again.
    pause
    exit /b 1
)

REM Check if src\main.py exists
if not exist "%SCRIPT_DIR%\src\main.py" (
    echo Error: src\main.py not found
    echo This may indicate an incomplete installation.
    pause
    exit /b 1
)

REM Run the main application
REM Pass all arguments to the script
python -m src.main %*