import os
import sys
from pathlib import Path

def get_app_data_dir():
    if not getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if sys.platform == 'win32':
        base = os.getenv('APPDATA')
        if not base:
            base = os.path.expanduser('~\\AppData\\Roaming')
    elif sys.platform == 'darwin':
        base = os.path.expanduser('~/Library/Application Support')
    else:
        base = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))

    return os.path.join(base, 'Keybrame')

def get_images_dir():
    if not getattr(sys, 'frozen', False):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(project_root, 'assets')
    return os.path.join(get_app_data_dir(), 'assets')

def get_database_path():
    if not getattr(sys, 'frozen', False):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(project_root, 'data', 'config.db')
    return os.path.join(get_app_data_dir(), 'config.db')

def get_logs_dir():
    if not getattr(sys, 'frozen', False):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(project_root, 'logs')
    return os.path.join(get_app_data_dir(), 'logs')

def get_log_file():
    return os.path.join(get_logs_dir(), 'server.log')

def ensure_directories():
    if getattr(sys, 'frozen', False):
        for directory in [get_app_data_dir(), get_images_dir(), get_logs_dir()]:
            os.makedirs(directory, exist_ok=True)
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        for directory in [get_images_dir(), get_logs_dir(), os.path.join(project_root, 'data')]:
            os.makedirs(directory, exist_ok=True)
    return True

def get_static_dir():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'static')
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(project_root, 'static')

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ensure_directories()

if __name__ == '__main__':
    print(f"[INFO] Keybrame rutas:")
    print(f"  - Datos: {get_app_data_dir()}")
    print(f"  - Imágenes: {get_images_dir()}")
    print(f"  - Base de datos: {get_database_path()}")
    print(f"  - Logs: {get_logs_dir()}")
