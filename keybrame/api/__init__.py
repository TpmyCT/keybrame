from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from . import settings, keybindings, images, server_control

def init_api(config_manager_instance, socketio_instance, reload_callback):
    settings.config_manager = config_manager_instance
    settings.socketio = socketio_instance
    settings.reload_global_config = reload_callback

    keybindings.config_manager = config_manager_instance
    images.config_manager = config_manager_instance
    server_control.config_manager = config_manager_instance
