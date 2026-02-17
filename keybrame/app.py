#!/usr/bin/env python3
"""
Aplicación Flask para Keybrame
Maneja las rutas web y websocket
"""

import os
import json
from flask import Flask, send_from_directory, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from keybrame.api import api_bp, init_api
from keybrame.utils import paths


def generate_placeholder_svg():
    """Genera un SVG placeholder para cuando no hay imagen configurada"""
    svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="600" fill="#1a1a1a"/>
  <text x="400" y="280" font-family="Arial, sans-serif" font-size="32"
        fill="#666" text-anchor="middle">Sin imagen configurada</text>
  <text x="400" y="330" font-family="Arial, sans-serif" font-size="18"
        fill="#444" text-anchor="middle">Configura una imagen desde el panel de administración</text>
</svg>'''
    return svg


def create_app(config_manager, keyboard_handler=None):
    """
    Crea y configura la aplicación Flask

    Args:
        config_manager: Gestor de configuración
        keyboard_handler: Handler de teclado/mouse (opcional, se setea después)

    Returns:
        tuple: (app, socketio)
    """
    static_folder = paths.get_static_dir()
    images_folder = paths.get_images_dir()

    # Crear app Flask
    app = Flask(__name__, static_folder=static_folder)
    app.config['SECRET_KEY'] = 'obs-image-switcher-secret'
    CORS(app)

    # Crear SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Variable para almacenar el keyboard_handler
    _keyboard_handler = {'handler': keyboard_handler}

    # Callback para reload de config
    def reload_global_config():
        """Callback para cuando se actualiza la configuración"""
        print("[INFO] Configuración global actualizada")
        if _keyboard_handler['handler']:
            _keyboard_handler['handler'].reload_config()
            print("[INFO] Keyboard handler recargado")

    # Función para setear el keyboard_handler después de crear la app
    def set_keyboard_handler(handler):
        _keyboard_handler['handler'] = handler

    # Guardar set_keyboard_handler en la app para acceso desde server.py
    app.set_keyboard_handler = set_keyboard_handler

    # Registrar API
    init_api(config_manager, socketio, reload_global_config)
    app.register_blueprint(api_bp)

    # ========== RUTAS FLASK ==========

    @app.route('/')
    def index():
        """Página principal para OBS Browser Source"""
        index_path = os.path.join(os.path.dirname(__file__), 'index.html')
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()

    @app.route('/admin')
    def admin_ui():
        """Panel de administración web"""
        return send_from_directory(static_folder, 'admin.html')

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Servir archivos estáticos"""
        return send_from_directory(static_folder, filename)

    @app.route('/config')
    def get_config():
        """Endpoint legacy para obtener configuración"""
        config = config_manager.get_config()
        return json.dumps(config)

    @app.route('/assets/placeholder.svg')
    def serve_placeholder():
        """Devuelve un SVG placeholder cuando no hay imagen configurada"""
        svg = generate_placeholder_svg()
        return Response(svg, mimetype='image/svg+xml')

    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        """Servir assets (imágenes del usuario)"""
        # Si es el placeholder, redirigir a la ruta especial
        if filename == 'placeholder.svg':
            return serve_placeholder()

        filepath = os.path.join(images_folder, filename)
        if not os.path.exists(filepath):
            print(f"[WARNING] Imagen no encontrada: {filename}")
            # Devolver el placeholder en vez de 204
            return serve_placeholder()
        return send_from_directory(images_folder, filename)

    # ========== WEBSOCKET HANDLERS ==========

    @socketio.on('connect')
    def handle_connect():
        """Cliente conectado al websocket"""
        print('[OK] Cliente conectado')
        config = config_manager.get_config()
        default_image = config.get('default_image', '')
        if not default_image:
            default_image = 'assets/placeholder.svg'
        emit('image_change', {'image': default_image})

        from keybrame.core.updater import get_update_info
        update_info = get_update_info()
        if update_info and update_info.get('available'):
            emit('update_available', update_info)

    @socketio.on('disconnect')
    def handle_disconnect():
        """Cliente desconectado del websocket"""
        print('[X] Cliente desconectado')

    return app, socketio
