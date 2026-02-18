@echo off
echo ========================================
echo  Keybrame - Setup and Launch
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Could not create virtual environment.
        echo Make sure Python is installed.
        pause
        exit /b 1
    )
    echo Virtual environment created.
    echo.
) else (
    echo [OK] Virtual environment found.
)

REM Check if dependencies are installed
echo [2/3] Checking dependencies...
venv\Scripts\python.exe -c "import flask, flask_socketio, pynput" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo Error: Could not install dependencies.
        pause
        exit /b 1
    )
    echo Dependencies installed.
    echo.
) else (
    echo [OK] Dependencies installed.
)

REM Get configured port
echo [3/3] Starting server...
for /f %%i in ('venv\Scripts\python.exe keybrame\utils\get_port.py') do set PORT=%%i

start "" venv\Scripts\pythonw.exe server.py

echo Waiting for server to start...
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo  Server started on port %PORT%
echo ========================================
echo Opening admin panel...
start http://localhost:%PORT%/admin

exit
