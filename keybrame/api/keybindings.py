from flask import jsonify, request
import json
import sqlite3
from . import api_bp
from .validation import validate_keybinding_data
from keybrame.core.image import calculate_gif_duration

config_manager = None


@api_bp.route('/keybindings', methods=['GET'])
def get_keybindings():
    try:
        conn = config_manager.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, keys, type, image, description, priority, enabled
            FROM keybindings
            ORDER BY priority DESC, id
        ''')

        keybindings = []
        for row in cursor.fetchall():
            kb = {
                'id': row['id'],
                'keys': json.loads(row['keys']),
                'type': row['type'],
                'image': row['image'],
                'description': row['description'] or '',
                'priority': row['priority'],
                'enabled': bool(row['enabled'])
            }

            cursor.execute('''
                SELECT direction, image, duration
                FROM transitions
                WHERE keybinding_id = ?
            ''', (row['id'],))

            for trans_row in cursor.fetchall():
                direction = trans_row['direction']
                trans_data = {'image': trans_row['image']}
                if trans_row['duration'] is not None:
                    trans_data['duration'] = trans_row['duration']

                if direction == 'in':
                    kb['transition_in'] = trans_data
                elif direction == 'out':
                    kb['transition_out'] = trans_data

            keybindings.append(kb)

        conn.close()
        return jsonify(keybindings)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/keybindings', methods=['POST'])
def create_keybinding():
    try:
        data = request.json

        valid, errors = validate_keybinding_data(data)
        if not valid:
            return jsonify({'error': 'Datos inválidos', 'details': errors}), 400

        conn = config_manager.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COALESCE(MAX(priority), 0) FROM keybindings")
        max_priority = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO keybindings (keys, type, image, description, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            json.dumps(data['keys']),
            data['type'],
            data['image'],
            data.get('description', ''),
            max_priority + 1
        ))

        keybinding_id = cursor.lastrowid

        if 'transition_in' in data and data['transition_in']:
            trans = data['transition_in']
            duration = trans.get('duration')
            if duration is None:
                duration = calculate_gif_duration(trans['image'])
            cursor.execute('''
                INSERT INTO transitions (keybinding_id, direction, image, duration)
                VALUES (?, ?, ?, ?)
            ''', (keybinding_id, 'in', trans['image'], duration))

        if 'transition_out' in data and data['transition_out']:
            trans = data['transition_out']
            duration = trans.get('duration')
            if duration is None:
                duration = calculate_gif_duration(trans['image'])
            cursor.execute('''
                INSERT INTO transitions (keybinding_id, direction, image, duration)
                VALUES (?, ?, ?, ?)
            ''', (keybinding_id, 'out', trans['image'], duration))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'id': keybinding_id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/keybindings/<int:kb_id>', methods=['PUT'])
def update_keybinding(kb_id):
    try:
        data = request.json

        valid, errors = validate_keybinding_data(data, is_update=True)
        if not valid:
            return jsonify({'error': 'Datos inválidos', 'details': errors}), 400

        conn = config_manager.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM keybindings WHERE id = ?", (kb_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Keybinding no encontrado'}), 404

        # Build dynamic UPDATE
        updates = []
        values = []

        if 'keys' in data:
            updates.append("keys = ?")
            values.append(json.dumps(data['keys']))

        if 'type' in data:
            updates.append("type = ?")
            values.append(data['type'])

        if 'image' in data:
            updates.append("image = ?")
            values.append(data['image'])

        if 'description' in data:
            updates.append("description = ?")
            values.append(data['description'])

        if 'enabled' in data:
            updates.append("enabled = ?")
            values.append(1 if data['enabled'] else 0)

        updates.append("updated_at = CURRENT_TIMESTAMP")

        if updates:
            values.append(kb_id)
            cursor.execute(f'''
                UPDATE keybindings
                SET {', '.join(updates)}
                WHERE id = ?
            ''', values)

        if 'transition_in' in data:
            cursor.execute(
                "DELETE FROM transitions WHERE keybinding_id = ? AND direction = 'in'",
                (kb_id,)
            )
            if data['transition_in']:
                trans = data['transition_in']
                duration = trans.get('duration')
                if duration is None:
                    duration = calculate_gif_duration(trans['image'])
                cursor.execute('''
                    INSERT INTO transitions (keybinding_id, direction, image, duration)
                    VALUES (?, ?, ?, ?)
                ''', (kb_id, 'in', trans['image'], duration))

        if 'transition_out' in data:
            cursor.execute(
                "DELETE FROM transitions WHERE keybinding_id = ? AND direction = 'out'",
                (kb_id,)
            )
            if data['transition_out']:
                trans = data['transition_out']
                duration = trans.get('duration')
                if duration is None:
                    duration = calculate_gif_duration(trans['image'])
                cursor.execute('''
                    INSERT INTO transitions (keybinding_id, direction, image, duration)
                    VALUES (?, ?, ?, ?)
                ''', (kb_id, 'out', trans['image'], duration))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/keybindings/<int:kb_id>', methods=['DELETE'])
def delete_keybinding(kb_id):
    try:
        conn = config_manager.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM keybindings WHERE id = ?", (kb_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Keybinding no encontrado'}), 404

        # Transitions are removed automatically via CASCADE
        cursor.execute("DELETE FROM keybindings WHERE id = ?", (kb_id,))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/keybindings/reorder', methods=['PUT'])
def reorder_keybindings():
    try:
        data = request.json
        # Expected: { "order": [id1, id2, id3, ...] }
        order = data.get('order', [])

        if not order:
            return jsonify({'error': 'Order array requerido'}), 400

        conn = config_manager.get_connection()
        cursor = conn.cursor()

        # Higher index = higher priority
        for idx, kb_id in enumerate(order):
            priority = len(order) - idx
            cursor.execute(
                "UPDATE keybindings SET priority = ? WHERE id = ?",
                (priority, kb_id)
            )

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
