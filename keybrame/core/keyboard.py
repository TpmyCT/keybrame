#!/usr/bin/env python3

import sys
import os
from pynput import keyboard, mouse


class KeyboardMouseHandler:

    def __init__(self, config_manager, socketio):
        self.config_manager = config_manager
        self.socketio = socketio
        self.config = config_manager.get_config()

        self.pressed_keys = set()
        self.physically_pressed_keys = set()
        self.active_press_key = None

        self.keyboard_listener = None
        self.mouse_listener = None

    def reload_config(self):
        self.config = self.config_manager.get_config()
        self.pressed_keys.clear()
        self.physically_pressed_keys.clear()
        self.active_press_key = None

        default_image = self.config.get('default_image', '') or 'assets/placeholder.svg'
        self.socketio.emit('image_change', {'image': default_image})
        print("[INFO] Configuración del handler actualizada y estado reseteado")

    def normalize_key(self, key):
        try:
            if hasattr(key, 'name'):
                key_name = key.name.lower()
                if key_name in ['ctrl_l', 'ctrl_r']:
                    return 'ctrl'
                elif key_name in ['shift_l', 'shift_r']:
                    return 'shift'
                elif key_name in ['alt_l', 'alt_r', 'alt_gr']:
                    return 'alt'
                elif key_name in ['cmd_l', 'cmd_r']:
                    return 'cmd'
                return key_name
            elif hasattr(key, 'char') and key.char:
                char_code = ord(key.char)
                if 1 <= char_code <= 26:
                    return chr(char_code + 96)
                elif char_code < 32:
                    return None
                return key.char.lower()
            else:
                key_str = str(key).replace("'", "").lower()
                if key_str in ['<unknown>', '?', '', 'none']:
                    return None
                return key_str
        except:
            return None

    def check_combos(self):
        for binding in self.config['keybindings']:
            if len(binding['keys']) > 1:
                required_keys = set(k.lower() for k in binding['keys'])
                if required_keys.issubset(self.pressed_keys):
                    return binding['image']
        return None

    def check_hold_keys(self):
        for binding in self.config['keybindings']:
            if binding.get('type') == 'hold':
                required_keys = set(k.lower() for k in binding['keys'])
                if required_keys.issubset(self.pressed_keys):
                    return binding['image']
        return None

    def get_base_image(self):
        if self.active_press_key:
            for binding in self.config['keybindings']:
                if binding.get('type') == 'toggle':
                    binding_keys = frozenset(k.lower() for k in binding['keys'])
                    if binding_keys == self.active_press_key:
                        return binding['image']
        default = self.config.get('default_image', '')
        return default if default else 'assets/placeholder.svg'

    def determine_current_image(self):
        combo_image = self.check_combos()
        if combo_image:
            return combo_image

        hold_image = self.check_hold_keys()
        if hold_image:
            return hold_image

        return self.get_base_image()

    def on_press(self, key):
        if isinstance(key, str):
            key_name = key
        else:
            key_name = self.normalize_key(key)
            if not key_name:
                return

        if key_name in self.physically_pressed_keys:
            return

        self.physically_pressed_keys.add(key_name)
        self.pressed_keys.add(key_name)

        self.socketio.emit('key_pressed', {'key': key_name})

        shutdown_combo = self.config.get('shutdown_combo')
        if shutdown_combo:
            shutdown_keys = set(k.lower() for k in shutdown_combo)
            if shutdown_keys.issubset(self.pressed_keys):
                print("\n" + "="*60)
                print(f"  Shutdown combo detectado ({'+'.join(shutdown_combo)}) - Cerrando servidor...")
                print("="*60)
                sys.stdout.flush()
                try:
                    self.socketio.stop()
                except:
                    pass
                os._exit(0)

        matched_binding = None

        if self.active_press_key:
            if frozenset(self.pressed_keys) == self.active_press_key:
                for binding in self.config['keybindings']:
                    binding_keys = frozenset(k.lower() for k in binding['keys'])
                    if binding_keys == self.active_press_key and binding.get('type') == 'toggle':
                        matched_binding = binding
                        break

        if not matched_binding:
            for binding in self.config['keybindings']:
                if len(binding['keys']) > 1:
                    required_keys = set(k.lower() for k in binding['keys'])
                    if required_keys.issubset(self.pressed_keys):
                        matched_binding = binding
                        break

            if not matched_binding:
                for binding in self.config['keybindings']:
                    if len(binding['keys']) == 1 and binding['keys'][0].lower() == key_name:
                        if self.active_press_key and key_name in self.active_press_key:
                            continue
                        matched_binding = binding
                        break

        if matched_binding:
            binding_keys = frozenset(k.lower() for k in matched_binding['keys'])
            binding_type = matched_binding.get('type', 'toggle')

            if binding_type == 'toggle':
                is_active = (self.active_press_key == binding_keys)

                if is_active:
                    self.active_press_key = None
                    default_image = self.config.get('default_image', '')

                    if 'transition_out' in matched_binding:
                        transition_data = matched_binding['transition_out']
                        self.socketio.emit('transition', {
                            'transition_image': transition_data['image'],
                            'duration': transition_data.get('duration'),
                            'final_image': default_image
                        })
                    else:
                        self.socketio.emit('image_change', {'image': default_image})
                else:
                    self.active_press_key = binding_keys

                    transition_data = matched_binding.get('transition_in') or matched_binding.get('transition')
                    if transition_data:
                        self.socketio.emit('transition', {
                            'transition_image': transition_data['image'],
                            'duration': transition_data.get('duration'),
                            'final_image': matched_binding['image']
                        })
                    else:
                        self.socketio.emit('image_change', {'image': matched_binding['image']})

            elif binding_type == 'hold':
                current_image = self.determine_current_image()
                self.socketio.emit('image_change', {'image': current_image})

    def on_release(self, key):
        if isinstance(key, str):
            key_name = key
        else:
            key_name = self.normalize_key(key)
            if not key_name:
                unknown_keys = [k for k in self.pressed_keys if k in ['?', '<unknown>', 'unknown']]
                for unknown_key in unknown_keys:
                    self.pressed_keys.discard(unknown_key)
                    self.physically_pressed_keys.discard(unknown_key)
                    self.socketio.emit('key_released', {'key': unknown_key})
                return

        self.physically_pressed_keys.discard(key_name)

        is_toggle_key = any(
            binding.get('type') == 'toggle' and key_name in [k.lower() for k in binding['keys']]
            for binding in self.config['keybindings']
        )

        is_hold_key = any(
            binding.get('type') == 'hold' and key_name in [k.lower() for k in binding['keys']]
            for binding in self.config['keybindings']
        )

        self.socketio.emit('key_released', {'key': key_name})

        if is_hold_key:
            self.pressed_keys.discard(key_name)
            current_image = self.determine_current_image()
            self.socketio.emit('image_change', {'image': current_image})
        else:
            self.pressed_keys.discard(key_name)

    def on_click(self, x, y, button, pressed):
        button_name = None
        if button == mouse.Button.left:
            button_name = 'mouse_left'
        elif button == mouse.Button.right:
            button_name = 'mouse_right'
        elif button == mouse.Button.middle:
            button_name = 'mouse_middle'

        if button_name:
            if pressed:
                self.on_press(button_name)
            else:
                self.on_release(button_name)

    def on_scroll(self, x, y, dx, dy):
        if dy > 0:
            scroll_name = 'scroll_up'
        elif dy < 0:
            scroll_name = 'scroll_down'
        else:
            return

        self.on_press(scroll_name)
        self.on_release(scroll_name)

    def start(self):
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.keyboard_listener.start()
        print("[OK] Listener de teclado iniciado")

        self.mouse_listener = mouse.Listener(
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        self.mouse_listener.start()
        print("[OK] Listener de mouse iniciado")

    def stop(self):
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
