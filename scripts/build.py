#!/usr/bin/env python3

import PyInstaller.__main__
import os
import sys
import shutil

# Agregar la raíz del proyecto al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keybrame.utils.version import __version__

VERSION = __version__

print(f"Building Keybrame v{VERSION}...")

# Intentar limpiar directorios anteriores
try:
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
except PermissionError:
    print("\n[ERROR] No se pudo eliminar dist/build")
    print("Cierra Keybrame.exe antes de compilar de nuevo")
    print("(Click derecho en el icono del tray -> Detener servidor)\n")
    sys.exit(1)

args = [
    'server.py',
    '--name=Keybrame',
    '--onedir',
    '--windowed',
    '--add-data=static;static',
    '--add-data=keybrame;keybrame',
    '--add-data=assets;assets',
    '--hidden-import=pynput',
    '--hidden-import=flask_socketio',
    '--hidden-import=flask_cors',
    '--hidden-import=pystray',
    '--hidden-import=PIL',
    '--hidden-import=engineio.async_drivers.threading',
    '--hidden-import=keybrame.api.settings',
    '--hidden-import=keybrame.api.keybindings',
    '--hidden-import=keybrame.api.images',
    '--hidden-import=keybrame.api.server_control',
    '--hidden-import=keybrame.api.validation',
    '--hidden-import=keybrame.config.manager',
    '--hidden-import=keybrame.core.image',
    '--hidden-import=keybrame.utils.version',
    '--hidden-import=keybrame.utils.paths',
]

if os.path.exists('scripts/app.ico'):
    args.append('--icon=scripts/app.ico')

PyInstaller.__main__.run(args)

print(f"\n[OK] Build completado: dist/Keybrame.exe")
print(f"[OK] Version: {VERSION}")
