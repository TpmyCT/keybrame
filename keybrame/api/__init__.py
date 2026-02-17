from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Importar módulos para registrar las rutas
from . import settings, keybindings, images, server_control

def init_api(config_manager_instance, socketio_instance, reload_callback):
    """Inicializa la API con las dependencias necesarias"""
    from . import settings, keybindings, images, server_control

    settings.config_manager = config_manager_instance
    settings.socketio = socketio_instance
    settings.reload_global_config = reload_callback

    keybindings.config_manager = config_manager_instance
    images.config_manager = config_manager_instance
    server_control.config_manager = config_manager_instance
