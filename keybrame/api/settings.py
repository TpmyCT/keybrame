#!/usr/bin/env python3

from flask import jsonify, request
import json
import os
from . import api_bp
from keybrame.utils import paths

config_manager = None
socketio = None
reload_global_config = None


@api_bp.route('/settings', methods=['GET'])
def get_settings():
    """Obtiene la configuración general"""
    try:
        conn = config_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value, type FROM settings")

        settings = {}
        for row in cursor.fetchall():
            key, value, value_type = row
            if value_type == 'integer':
                settings[key] = int(value)
            elif value_type == 'array':
                settings[key] = json.loads(value)
            else:
                settings[key] = value

        conn.close()
        return jsonify(settings)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/settings', methods=['PUT'])
def update_settings():
    """Actualiza la configuración general"""
    try:
        data = request.json
        conn = config_manager.get_connection()
        cursor = conn.cursor()

        reload_required = False

        if 'port' in data:
            cursor.execute("SELECT value FROM settings WHERE key = 'port'")
            current_port = cursor.fetchone()
            current_port_value = int(current_port[0]) if current_port else 5000

            if current_port_value != data['port']:
                reload_required = True

            cursor.execute(
                "UPDATE settings SET value = ? WHERE key = 'port'",
                (str(data['port']),)
            )

        if 'shutdown_combo' in data:
            cursor.execute(
                "UPDATE settings SET value = ? WHERE key = 'shutdown_combo'",
                (json.dumps(data['shutdown_combo']),)
            )

        if 'default_image' in data:
            default_image = data['default_image']

            if default_image:
                filename = default_image.replace('assets/', '')
                image_path = os.path.join(paths.get_images_dir(), filename)

                if not os.path.exists(image_path):
                    conn.close()
                    return jsonify({
                        'error': f'La imagen "{filename}" no existe. Por favor, sube la imagen primero.'
                    }), 400

            cursor.execute(
                "UPDATE settings SET value = ? WHERE key = 'default_image'",
                (default_image,)
            )

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'reloadRequired': reload_required
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/reload', methods=['POST'])
def reload_config():
    """Recarga la configuración desde la base de datos"""
    try:
        config_manager.reload()

        if reload_global_config:
            reload_global_config()

        if socketio:
            socketio.emit('config_reloaded', {})

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/export', methods=['GET'])
def export_config():
    """Exporta la configuración actual como JSON"""
    try:
        config = config_manager.load_config()
        return jsonify(config)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/import', methods=['POST'])
def import_config():
    """Importa configuración desde JSON"""
    try:
        from .validation import validate_keybinding_data
        from keybrame.core.image import calculate_gif_duration

        data = request.json

        if 'port' not in data or 'keybindings' not in data:
            return jsonify({'error': 'JSON inválido: faltan campos requeridos'}), 400

        conn = config_manager.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM keybindings")
        cursor.execute("DELETE FROM transitions")

        cursor.execute(
            "UPDATE settings SET value = ? WHERE key = 'port'",
            (str(data.get('port', 5000)),)
        )
        cursor.execute(
            "UPDATE settings SET value = ? WHERE key = 'shutdown_combo'",
            (json.dumps(data.get('shutdown_combo', ['ctrl', 'shift', 'q'])),)
        )
        cursor.execute(
            "UPDATE settings SET value = ? WHERE key = 'default_image'",
            (data.get('default_image', ''),)
        )

        for idx, binding in enumerate(data.get('keybindings', [])):
            valid, errors = validate_keybinding_data(binding)
            if not valid:
                conn.rollback()
                conn.close()
                return jsonify({
                    'error': f'Keybinding #{idx+1} inválido',
                    'details': errors
                }), 400

            cursor.execute('''
                INSERT INTO keybindings (keys, type, image, description, priority)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                json.dumps(binding['keys']),
                binding.get('type', 'toggle'),
                binding['image'],
                binding.get('description', ''),
                len(data['keybindings']) - idx
            ))

            keybinding_id = cursor.lastrowid

            if 'transition_in' in binding:
                trans = binding['transition_in']
                duration = trans.get('duration')
                if duration is None:
                    duration = calculate_gif_duration(trans['image'])
                cursor.execute('''
                    INSERT INTO transitions (keybinding_id, direction, image, duration)
                    VALUES (?, ?, ?, ?)
                ''', (keybinding_id, 'in', trans['image'], duration))

            if 'transition_out' in binding:
                trans = binding['transition_out']
                duration = trans.get('duration')
                if duration is None:
                    duration = calculate_gif_duration(trans['image'])
                cursor.execute('''
                    INSERT INTO transitions (keybinding_id, direction, image, duration)
                    VALUES (?, ?, ?, ?)
                ''', (keybinding_id, 'out', trans['image'], duration))

        conn.commit()
        conn.close()

        config_manager.reload()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
