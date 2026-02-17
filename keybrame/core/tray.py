#!/usr/bin/env python3
"""
Manejo del icono del system tray para Keybrame
"""

import os
import sys
import threading
import webbrowser
import pystray
from PIL import Image, ImageDraw
from keybrame.utils import paths


_tray_icon = None
_config_manager = None


def create_icon_image():
    """Crea la imagen del icono del system tray - icono de teclado moderno"""
    width = 64
    height = 64

    # Fondo transparente
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)

    # Colores azul
    color1 = '#2563eb'  # Azul
    color2 = '#0ea5e9'  # Azul cielo

    # Dibujar rectángulo con borde redondeado (teclado)
    dc.rounded_rectangle([8, 16, 56, 48], radius=6, fill=color1, outline=color2, width=2)

    # Dibujar teclas pequeñas
    key_size = 6
    spacing = 2

    # Fila 1
    for i in range(4):
        x = 14 + i * (key_size + spacing)
        dc.rectangle([x, 22, x + key_size, 22 + key_size], fill='white')

    # Fila 2
    for i in range(4):
        x = 14 + i * (key_size + spacing)
        dc.rectangle([x, 30, x + key_size, 30 + key_size], fill='white')

    return image


def open_admin():
    """Abre el panel de administración en el navegador"""
    global _config_manager
    if _config_manager:
        config = _config_manager.get_config()
        port = config.get('port', 5000)
        url = f"http://localhost:{port}/admin"
        webbrowser.open(url)


def open_logs():
    """Abre la carpeta de datos de la aplicación"""
    data_dir = paths.get_app_data_dir()
    if os.path.exists(data_dir):
        os.startfile(data_dir)


def quit_server(icon, item):
    """Cierra el servidor desde el system tray"""
    global _tray_icon
    print("\n" + "="*60)
    print("  Cerrando servidor desde system tray...")
    print("="*60)
    icon.stop()
    os._exit(0)


def setup_tray_icon():
    """Configura e inicia el icono del system tray"""
    global _tray_icon

    menu = pystray.Menu(
        pystray.MenuItem('Keybrame - OBS Image Switcher', None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Abrir panel de administración', lambda: open_admin(), default=True),
        pystray.MenuItem('Abrir carpeta de datos', lambda: open_logs()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Salir', quit_server)
    )

    icon_image = create_icon_image()
    _tray_icon = pystray.Icon(
        "Keybrame",
        icon_image,
        "Keybrame - Clic para abrir admin",
        menu
    )

    _tray_icon.run()


def start_tray_icon(config_manager, socketio):
    """Inicia el icono del system tray en un thread separado"""
    global _config_manager
    _config_manager = config_manager

    tray_thread = threading.Thread(target=setup_tray_icon, daemon=True)
    tray_thread.start()
    print("[OK] Icono en system tray iniciado")
