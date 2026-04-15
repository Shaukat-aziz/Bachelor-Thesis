@echo off
REM Quick Start Script for Pentagon Photonic Crystal Simulator (Windows)
REM Usage: launch.bat [OPTIONS]

setlocal enabledelayedexpansion

REM Set colors (Windows 10+)
set "RESET=[0m"
set "RED=[31m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "BLUE=[34m"

REM Get script directory
set "APP_DIR=%~dp0"
set "PYTHON=python"

:main
if "%1"=="" (
    call :launch_app
    exit /b 0
) else if "%1"=="--help" (
    call :show_help
    exit /b 0
) else if "%1"=="-h" (
    call :show_help
    exit /b 0
) else if "%1"=="--check" (
    call :check_dependencies
    exit /b 0
) else if "%1"=="--gpu" (
    call :check_gpu
    exit /b 0
) else if "%1"=="--install" (
    call :install_dependencies
    exit /b 0
) else if "%1"=="--debug" (
    call :launch_debug
    exit /b 0
) else if "%1"=="--version" (
    echo Pentagon Photonic Crystal Simulator v1.0.0
    exit /b 0
) else (
    echo Unknown option: %1
    call :show_help
    exit /b 1
)

:print_banner
cls
echo.
echo ══════════════════════════════════════════════════════════
echo   Pentagon Photonic Crystal Simulator
echo   Version 1.0.0
echo ══════════════════════════════════════════════════════════
echo.
exit /b 0

:check_python
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.9+
    exit /b 1
)
for /f "tokens=2" %%i in ('%PYTHON% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python %PYTHON_VERSION% found
exit /b 0

:check_dependencies
call :print_banner
call :check_python
echo.
echo Checking dependencies...
echo.

set MISSING=0

for %%p in (numpy matplotlib scipy) do (
    %PYTHON% -c "import %%p" 2>nul
    if errorlevel 1 (
        echo [X] %%p (not installed)
        set /a MISSING=!MISSING!+1
    ) else (
        echo [OK] %%p
    )
)

echo.
for %%p in (meep cupy torch jax) do (
    %PYTHON% -c "import %%p" 2>nul
    if errorlevel 1 (
        echo [-] %%p (optional, not installed)
    ) else (
        echo [OK] %%p (optional)
    )
)

if %MISSING% gtr 0 (
    echo.
    echo WARNING: %MISSING% required package^(s^) not installed
    echo Install with: pip install -r requirements.txt
)
exit /b 0

:check_gpu
call :print_banner
echo Checking GPU availability...
echo.

where nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo No NVIDIA GPU detected (nvidia-smi not found)
) else (
    echo NVIDIA GPU drivers found
    for /f "tokens=*" %%i in ('nvidia-smi --query-gpu=name --format=csv,noheader') do (
        echo GPU: %%i
    )
)

%PYTHON% -c "import cupy; print('CuPy GPU support available')" 2>nul
if errorlevel 1 (
    echo CuPy not available (GPU acceleration disabled)
) else (
    echo CuPy GPU support available
)
exit /b 0

:install_dependencies
call :print_banner
echo Installing dependencies...
echo.

if exist "%APP_DIR%requirements.txt" (
    pip install -r "%APP_DIR%requirements.txt"
    echo.
    echo Dependencies installed successfully
) else (
    echo Error: requirements.txt not found
    exit /b 1
)
exit /b 0

:launch_app
call :print_banner
call :check_python
echo.
echo Launching Pentagon Photonic Crystal Simulator...
echo.

cd /d "%APP_DIR%"
start "" %PYTHON% app.py

echo Application launched. Check your desktop for the window.
exit /b 0

:launch_debug
call :print_banner
call :check_python
echo.
echo Launching in debug mode (foreground)...
echo.

cd /d "%APP_DIR%"
%PYTHON% app.py
exit /b 0

:show_help
call :print_banner
echo.
echo Usage: launch.bat [OPTIONS]
echo.
echo OPTIONS:
echo   --help, -h       Show this help message
echo   --check         Check dependencies only
echo   --gpu           Show GPU information
echo   --debug         Run in debug mode (foreground)
echo   --install       Install dependencies
echo   --version       Show version
echo.
echo EXAMPLES:
echo   launch.bat              # Launch application
echo   launch.bat --check      # Check dependencies
echo   launch.bat --gpu        # Check GPU
echo   launch.bat --debug      # Debug mode
echo   launch.bat --install    # Install dependencies
echo.
exit /b 0
