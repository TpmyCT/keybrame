import sys
import webbrowser
import threading
import time
from keybrame.app import create_app
from keybrame.core.keyboard import KeyboardMouseHandler
from keybrame.core.tray import start_tray_icon
from keybrame.config.manager import ConfigManager
from keybrame.utils import version, paths
from keybrame.utils.console import print_banner, print_info, print_startup_message


def main():
    print_banner(version.get_version_string())

    config_manager = ConfigManager(paths.get_database_path())
    app, socketio = create_app(config_manager)

    config = config_manager.get_config()
    print_info({
        'Puerto': config['port'],
        'URL para OBS': f"http://localhost:{config['port']}",
        'Panel de administración': f"http://localhost:{config['port']}/admin",
        'Carpeta de datos': paths.get_app_data_dir(),
        'Carpeta de imágenes': paths.get_images_dir()
    })

    if version.AUTO_UPDATE_CHECK:
        from keybrame.core.updater import check_updates_async
        check_updates_async(socketio)

    keyboard_handler = KeyboardMouseHandler(config_manager, socketio)
    keyboard_handler.start()
    app.set_keyboard_handler(keyboard_handler)

    start_tray_icon(config_manager, socketio)

    def open_browser():
        time.sleep(2)
        url = f"http://localhost:{config['port']}/admin"
        try:
            webbrowser.open(url)
            print(f"[OK] Navegador abierto: {url}")
        except Exception as e:
            print(f"[WARNING] No se pudo abrir el navegador: {e}")

    if getattr(sys, 'frozen', False) and '--no-browser' not in sys.argv:
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

    print_startup_message(config.get('shutdown_combo', ['Ctrl', 'Shift', 'Q']))

    socketio.run(app, host='0.0.0.0', port=config['port'],
                 debug=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()
