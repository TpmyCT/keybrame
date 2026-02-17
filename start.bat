@echo off
echo ========================================
echo  Keybrame - Setup y Ejecucion
echo ========================================
echo.

REM Verificar si existe el entorno virtual
if not exist "venv\Scripts\python.exe" (
    echo [1/3] Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo Error: No se pudo crear el entorno virtual.
        echo Asegurate de tener Python instalado.
        pause
        exit /b 1
    )
    echo Entorno virtual creado correctamente.
    echo.
) else (
    echo [OK] Entorno virtual encontrado.
)

REM Verificar si las dependencias estan instaladas
echo [2/3] Verificando dependencias...
venv\Scripts\python.exe -c "import flask, flask_socketio, pynput" 2>nul
if errorlevel 1 (
    echo Instalando dependencias...
    venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo Error: No se pudieron instalar las dependencias.
        pause
        exit /b 1
    )
    echo Dependencias instaladas correctamente.
    echo.
) else (
    echo [OK] Dependencias instaladas.
)

REM Obtener el puerto configurado
echo [3/3] Iniciando servidor...
for /f %%i in ('venv\Scripts\python.exe keybrame\utils\get_port.py') do set PORT=%%i

start "" venv\Scripts\pythonw.exe server.py

echo Esperando a que el servidor inicie...
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo  Servidor iniciado en puerto %PORT%
echo ========================================
echo Abriendo panel de administracion...
start http://localhost:%PORT%/admin

exit
