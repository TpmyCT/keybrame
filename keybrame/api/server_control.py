#!/usr/bin/env python3

from flask import jsonify
import os
import sys
import subprocess
import threading
import pathlib
from . import api_bp

config_manager = None


@api_bp.route('/version', methods=['GET'])
def get_version():
    from keybrame.utils.version import __version__
    return jsonify({'version': __version__})


@api_bp.route('/server/update', methods=['POST'])
def trigger_update():
    try:
        from keybrame.core.updater import get_update_info, download_and_install

        update_info = get_update_info()
        if not update_info or not update_info.get('available'):
            return jsonify({'error': 'No hay actualización disponible'}), 400

        threading.Thread(target=download_and_install, args=(update_info,), daemon=True).start()
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/server/shutdown', methods=['POST'])
def shutdown_server():
    try:
        def delayed_shutdown():
            import time
            import atexit
            if getattr(sys, 'frozen', False):
                atexit._clear()
            time.sleep(0.5)
            os._exit(0)

        threading.Thread(target=delayed_shutdown, daemon=True).start()
        return jsonify({'success': True, 'message': 'Servidor apagándose...'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/server/restart', methods=['POST'])
def restart_server():
    try:
        def delayed_restart():
            import time
            import atexit
            if getattr(sys, 'frozen', False):
                atexit._clear()
            time.sleep(0.5)

            script = os.path.abspath(sys.argv[0])
            base_dir = pathlib.Path(__file__).parent.parent.parent
            venv_pythonw = base_dir / 'venv' / 'Scripts' / 'pythonw.exe'
            python_exe = str(venv_pythonw) if venv_pythonw.exists() else sys.executable

            if os.name == 'nt':
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                subprocess.Popen(
                    [python_exe, script] + sys.argv[1:],
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    close_fds=True
                )
            else:
                subprocess.Popen(
                    [python_exe, script] + sys.argv[1:],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )

            time.sleep(0.2)
            os._exit(0)

        threading.Thread(target=delayed_restart, daemon=True).start()
        return jsonify({'success': True, 'message': 'Servidor reiniciando...'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
