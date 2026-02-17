#!/usr/bin/env python3

from flask import jsonify, request
import os
from . import api_bp
from keybrame.core.image import calculate_gif_duration
from keybrame.utils import paths

# Variable global que se seteará desde init_api()
config_manager = None


@api_bp.route('/images', methods=['GET'])
def get_images():
    """Lista archivos en /assets/ con metadata"""
    try:
        images_dir = paths.get_images_dir()
        if not os.path.exists(images_dir):
            return jsonify([])

        images = []
        for filename in os.listdir(images_dir):
            filepath = os.path.join(images_dir, filename)

            # Solo archivos
            if not os.path.isfile(filepath):
                continue

            # Obtener extensión
            _, ext = os.path.splitext(filename)
            ext = ext.lower()

            # Solo imágenes
            if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
                continue

            # Obtener tamaño
            size = os.path.getsize(filepath)

            # Calcular duración si es GIF
            duration = None
            if ext == '.gif':
                duration = calculate_gif_duration(filepath)

            images.append({
                'path': f"assets/{filename}",  # Frontend espera path relativo
                'filename': filename,
                'size': size,
                'type': ext[1:],  # Quitar el punto
                'duration': duration
            })

        # Ordenar por nombre
        images.sort(key=lambda x: x['filename'].lower())

        return jsonify(images)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/images/upload', methods=['POST'])
def upload_image():
    """Sube una nueva imagen a la carpeta /assets/"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validar extensión
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
        filename = file.filename
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext not in allowed_extensions:
            return jsonify({'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}), 400

        # Asegurar que la carpeta assets existe
        images_dir = paths.get_images_dir()
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

        # Guardar archivo
        filepath = os.path.join(images_dir, filename)

        # Si el archivo ya existe, agregar un número
        if os.path.exists(filepath):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(filepath):
                filename = f"{base}_{counter}{ext}"
                filepath = os.path.join(images_dir, filename)
                counter += 1

        file.save(filepath)

        # Calcular duración si es GIF
        duration = None
        if ext == '.gif':
            duration = calculate_gif_duration(filepath)

        return jsonify({
            'success': True,
            'filename': filename,
            'path': f"assets/{filename}",
            'size': os.path.getsize(filepath),
            'type': ext[1:],
            'duration': duration
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/images/<path:filename>', methods=['DELETE'])
def delete_image(filename):
    """Elimina una imagen de la carpeta /assets/"""
    try:
        # Validar que no se intente eliminar fuera de /assets/
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid filename'}), 400

        # Extraer solo el nombre del archivo si viene con path completo
        if 'assets/' in filename:
            filename = filename.split('assets/')[-1]

        filepath = os.path.join(paths.get_images_dir(), filename)

        if not os.path.exists(filepath):
            return jsonify({'error': 'Image not found'}), 404

        # Verificar que es un archivo (no directorio)
        if not os.path.isfile(filepath):
            return jsonify({'error': 'Invalid path'}), 400

        # Eliminar archivo
        os.remove(filepath)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
