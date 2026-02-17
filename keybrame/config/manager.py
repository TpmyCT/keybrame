#!/usr/bin/env python3

import sqlite3
import json
import os
import threading
from datetime import datetime
from keybrame.core.image import calculate_gif_duration


class ConfigManager:
    def __init__(self, db_path='config.db'):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._config_cache = None
        self._initialize_database()

    def _initialize_database(self):
        db_exists = os.path.exists(self.db_path)

        if not db_exists:
            self._create_tables()
            self._create_default_config()
            print("[INFO] Configuración por defecto creada")
        else:
            self._migrate_image_paths_if_needed()
            print("[INFO] Usando base de datos existente: config.db")

    def _create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('string', 'integer', 'array'))
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keybindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keys TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('toggle', 'hold')),
                image TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 0,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_keybindings_priority
            ON keybindings(priority DESC, id)
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keybinding_id INTEGER NOT NULL,
                direction TEXT NOT NULL CHECK(direction IN ('in', 'out')),
                image TEXT NOT NULL,
                duration INTEGER,
                FOREIGN KEY (keybinding_id) REFERENCES keybindings(id) ON DELETE CASCADE,
                UNIQUE(keybinding_id, direction)
            )
        ''')

        conn.commit()
        conn.close()

    def _create_default_config(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO settings (key, value, type) VALUES (?, ?, ?)",
            ('port', '5000', 'integer')
        )
        cursor.execute(
            "INSERT INTO settings (key, value, type) VALUES (?, ?, ?)",
            ('shutdown_combo', json.dumps(['ctrl', 'shift', 'q']), 'array')
        )
        cursor.execute(
            "INSERT INTO settings (key, value, type) VALUES (?, ?, ?)",
            ('default_image', '', 'string')
        )

        conn.commit()
        conn.close()

    def _migrate_image_paths_if_needed(self):
        """Migra rutas de 'images/' o 'img/' a 'assets/' si es necesario (una sola vez)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verificar si hay rutas viejas (images/ o img/)
        cursor.execute("SELECT COUNT(*) FROM keybindings WHERE image LIKE 'images/%' OR image LIKE 'img/%'")
        old_paths = cursor.fetchone()[0]

        if old_paths > 0:
            print("[INFO] Migrando rutas de imagenes...")
            # Migrar desde images/
            cursor.execute("UPDATE keybindings SET image = REPLACE(image, 'images/', 'assets/')")
            cursor.execute("UPDATE transitions SET image = REPLACE(image, 'images/', 'assets/')")
            cursor.execute("UPDATE settings SET value = REPLACE(value, 'images/', 'assets/') WHERE key = 'default_image'")
            # Migrar desde img/
            cursor.execute("UPDATE keybindings SET image = REPLACE(image, 'img/', 'assets/')")
            cursor.execute("UPDATE transitions SET image = REPLACE(image, 'img/', 'assets/')")
            cursor.execute("UPDATE settings SET value = REPLACE(value, 'img/', 'assets/') WHERE key = 'default_image'")
            conn.commit()
            print("[OK] Rutas migradas a assets/")

        conn.close()

    def _process_config_transitions(self, config):
        for binding in config.get('keybindings', []):
            for transition_type in ['transition_in', 'transition_out', 'transition']:
                if transition_type in binding:
                    transition = binding[transition_type]
                    if 'duration' not in transition or transition['duration'] is None:
                        image_path = transition['image']
                        calculated_duration = calculate_gif_duration(image_path)
                        transition['duration'] = calculated_duration
                        if calculated_duration > 0:
                            print(f"[INFO] Duración auto-detectada para {image_path}: {calculated_duration}ms")
        return config

    def load_config(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT key, value, type FROM settings")
        settings = {}
        for row in cursor.fetchall():
            key = row['key']
            value = row['value']
            value_type = row['type']

            if value_type == 'integer':
                settings[key] = int(value)
            elif value_type == 'array':
                settings[key] = json.loads(value)
            else:
                settings[key] = value

        cursor.execute('''
            SELECT id, keys, type, image, description, enabled
            FROM keybindings
            WHERE enabled = 1
            ORDER BY priority DESC, id
        ''')

        keybindings = []
        for row in cursor.fetchall():
            keybinding = {
                'keys': json.loads(row['keys']),
                'type': row['type'],
                'image': row['image']
            }

            if row['description']:
                keybinding['description'] = row['description']

            kb_id = row['id']
            cursor.execute('''
                SELECT direction, image, duration
                FROM transitions
                WHERE keybinding_id = ?
            ''', (kb_id,))

            for trans_row in cursor.fetchall():
                direction = trans_row['direction']
                trans_data = {
                    'image': trans_row['image']
                }
                if trans_row['duration'] is not None:
                    trans_data['duration'] = trans_row['duration']

                if direction == 'in':
                    keybinding['transition_in'] = trans_data
                elif direction == 'out':
                    keybinding['transition_out'] = trans_data

            keybindings.append(keybinding)

        conn.close()

        config = {
            'port': settings.get('port', 5000),
            'shutdown_combo': settings.get('shutdown_combo', ['ctrl', 'shift', 'q']),
            'default_image': settings.get('default_image', ''),
            'keybindings': keybindings
        }

        config = self._process_config_transitions(config)

        return config

    def reload(self):
        with self._lock:
            self._config_cache = self.load_config()
            print("[INFO] Configuración recargada desde base de datos")
            return self._config_cache

    def get_config(self):
        if self._config_cache is None:
            with self._lock:
                if self._config_cache is None:
                    self._config_cache = self.load_config()
        return self._config_cache

    def get_connection(self):
        return sqlite3.connect(self.db_path)
