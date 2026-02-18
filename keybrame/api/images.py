from flask import jsonify, request
import os
from . import api_bp
from keybrame.core.image import calculate_gif_duration
from keybrame.utils import paths

config_manager = None


@api_bp.route('/images', methods=['GET'])
def get_images():
    try:
        images_dir = paths.get_images_dir()
        if not os.path.exists(images_dir):
            return jsonify([])

        images = []
        for filename in os.listdir(images_dir):
            filepath = os.path.join(images_dir, filename)

            if not os.path.isfile(filepath):
                continue

            _, ext = os.path.splitext(filename)
            ext = ext.lower()

            if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
                continue

            size = os.path.getsize(filepath)
            duration = calculate_gif_duration(filepath) if ext == '.gif' else None

            images.append({
                'path': f"assets/{filename}",
                'filename': filename,
                'size': size,
                'type': ext[1:],
                'duration': duration
            })

        images.sort(key=lambda x: x['filename'].lower())
        return jsonify(images)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/images/upload', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
        filename = file.filename
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext not in allowed_extensions:
            return jsonify({'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}), 400

        images_dir = paths.get_images_dir()
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

        filepath = os.path.join(images_dir, filename)

        # Append a number if file already exists
        if os.path.exists(filepath):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(filepath):
                filename = f"{base}_{counter}{ext}"
                filepath = os.path.join(images_dir, filename)
                counter += 1

        file.save(filepath)

        duration = calculate_gif_duration(filepath) if ext == '.gif' else None

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
    try:
        # Prevent path traversal
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid filename'}), 400

        if 'assets/' in filename:
            filename = filename.split('assets/')[-1]

        filepath = os.path.join(paths.get_images_dir(), filename)

        if not os.path.exists(filepath):
            return jsonify({'error': 'Image not found'}), 404

        if not os.path.isfile(filepath):
            return jsonify({'error': 'Invalid path'}), 400

        os.remove(filepath)
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
