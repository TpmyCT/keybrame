import os
import sys
import subprocess
import tempfile
import threading

import requests
from packaging import version as version_parser

from keybrame.utils.version import __version__

GITHUB_REPO = "TpmyCT/keybrame"
UPDATE_CHECK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

_socketio = None
_update_info = None


def get_update_info():
    return _update_info


def check_for_updates():
    try:
        response = requests.get(UPDATE_CHECK_URL, timeout=5)
        if response.status_code != 200:
            return {'available': False}

        release_data = response.json()
        latest_version = release_data['tag_name'].lstrip('v')
        current = version_parser.parse(__version__)
        latest = version_parser.parse(latest_version)

        if latest > current:
            download_url = None
            for asset in release_data.get('assets', []):
                if asset['name'].endswith('.exe'):
                    download_url = asset['browser_download_url']
                    break

            return {
                'available': True,
                'version': latest_version,
                'current_version': __version__,
                'download_url': download_url,
                'release_url': release_data['html_url']
            }

    except Exception as e:
        print(f"[WARNING] No se pudo verificar actualizaciones: {e}")

    return {'available': False}


def download_and_install(update_info):
    try:
        download_url = update_info.get('download_url')
        if not download_url:
            print("[ERROR] No se encontró URL de descarga")
            if _socketio:
                _socketio.emit('update_error', {'error': 'No se encontró URL de descarga'})
            return

        print(f"[INFO] Descargando actualización v{update_info['version']}...")

        response = requests.get(download_url, stream=True, timeout=300)
        total_size = int(response.headers.get('content-length', 0))

        # Guardar en AppData\Keybrame en vez de %TEMP% para evitar
        # que Windows Defender lo quarantine agresivamente
        from keybrame.utils.paths import get_app_data_dir
        installer_path = os.path.join(get_app_data_dir(), 'update_installer.exe')

        downloaded = 0
        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and _socketio:
                        progress = int((downloaded / total_size) * 100)
                        _socketio.emit('update_progress', {'progress': progress})

        if total_size > 0 and downloaded < total_size:
            raise Exception(f'Descarga incompleta: {downloaded}/{total_size} bytes')

        print(f"[INFO] Descarga completa ({downloaded} bytes). Ejecutando instalador...")
        if _socketio:
            _socketio.emit('update_installing', {})

        import time

        # VBScript: completamente silencioso (wscript.exe no abre consola),
        # espera 4 segundos y lanza el installer.
        vbs_path = os.path.join(get_app_data_dir(), 'update_launch.vbs')
        with open(vbs_path, 'w') as vbs:
            vbs.write(
                'Set sh = CreateObject("WScript.Shell")\n'
                f'sh.Run Chr(34) & "{installer_path}" & Chr(34) & " /VERYSILENT", 0, False\n'
                'Set fso = CreateObject("Scripting.FileSystemObject")\n'
                'fso.DeleteFile WScript.ScriptFullName\n'
            )

        subprocess.Popen(
            ['wscript.exe', vbs_path],
            creationflags=subprocess.DETACHED_PROCESS,
            close_fds=True
        )

        time.sleep(0.5)
        os._exit(0)

    except Exception as e:
        print(f"[ERROR] Error en la actualización: {e}")
        if _socketio:
            _socketio.emit('update_error', {'error': str(e)})


def check_updates_async(socketio=None):
    global _socketio
    if socketio:
        _socketio = socketio

    def run():
        global _update_info
        print("[INFO] Verificando actualizaciones...")
        info = check_for_updates()
        _update_info = info

        if info['available']:
            print(f"[INFO] Nueva versión disponible: v{info['version']}")
            if _socketio:
                _socketio.emit('update_available', info)
        else:
            print(f"[INFO] Ya tienes la última versión (v{__version__})")

    threading.Thread(target=run, daemon=True).start()
