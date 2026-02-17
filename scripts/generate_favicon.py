#!/usr/bin/env python3
"""
Script para generar el favicon de Keybrame
Usa el mismo diseño del icono del system tray
"""

import os
from PIL import Image, ImageDraw


def create_favicon_image(size=64):
    """Crea la imagen del favicon - icono de teclado moderno con supersampling"""
    # Renderizar a 4x para luego escalar y obtener antialiasing
    render_size = size * 4
    width = render_size
    height = render_size

    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)

    # Colores azul
    color1 = '#2563eb'  # Azul
    color2 = '#0ea5e9'  # Azul cielo

    scale = render_size / 64.0

    # Dibujar rectángulo con borde redondeado (teclado)
    padding = int(8 * scale)
    top = int(16 * scale)
    bottom = int(48 * scale)
    radius = int(6 * scale)
    dc.rounded_rectangle(
        [padding, top, width - padding, bottom],
        radius=radius,
        fill=color1,
        outline=color2,
        width=int(2 * scale)
    )

    # Dibujar teclas pequeñas
    key_size = int(6 * scale)
    spacing = int(2 * scale)
    start_x = int(14 * scale)

    # Fila 1
    y1 = int(22 * scale)
    for i in range(4):
        x = start_x + i * (key_size + spacing)
        dc.rectangle([x, y1, x + key_size, y1 + key_size], fill='white')

    # Fila 2
    y2 = int(30 * scale)
    for i in range(4):
        x = start_x + i * (key_size + spacing)
        dc.rectangle([x, y2, x + key_size, y2 + key_size], fill='white')

    # Escalar de vuelta al tamaño objetivo con antialiasing
    return image.resize((size, size), Image.LANCZOS)


def main():
    # Crear imágenes en diferentes tamaños para el favicon web
    favicon_sizes = [16, 32, 48, 64]
    favicon_images = [create_favicon_image(size) for size in favicon_sizes]

    # Guardar como favicon.ico (multi-tamaño)
    favicon_output = os.path.join('static', 'favicon.ico')
    favicon_images[0].save(
        favicon_output,
        format='ICO',
        sizes=[(s, s) for s in favicon_sizes],
        append_images=favicon_images[1:]
    )
    print(f"[OK] Favicon generado: {favicon_output}")

    # También guardar como PNG para usar en otros contextos
    png_path = os.path.join('static', 'favicon.png')
    favicon_images[-1].save(png_path, format='PNG')
    print(f"[OK] Favicon PNG generado: {png_path}")

    # Crear icono para el ejecutable (tamaños más grandes)
    exe_sizes = [16, 32, 48, 64, 128, 256]
    exe_images = [create_favicon_image(size) for size in exe_sizes]

    # Guardar como app.ico para el ejecutable
    exe_icon_path = os.path.join('scripts', 'app.ico')
    exe_images[0].save(
        exe_icon_path,
        format='ICO',
        sizes=[(s, s) for s in exe_sizes],
        append_images=exe_images[1:]
    )
    print(f"[OK] Icono del ejecutable generado: {exe_icon_path}")


if __name__ == '__main__':
    main()
