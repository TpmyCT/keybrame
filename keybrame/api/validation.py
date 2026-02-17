import os
from keybrame.utils import paths

VALID_KEYS = [
    *[chr(i) for i in range(ord('a'), ord('z')+1)],
    *[str(i) for i in range(10)],
    'space', 'enter', 'tab', 'esc', 'backspace',
    'ctrl', 'shift', 'alt', 'cmd',
    'up', 'down', 'left', 'right',
    *[f'f{i}' for i in range(1, 13)],
    *[f'num_{i}' for i in range(10)],
    'num_add', 'num_subtract', 'num_multiply', 'num_divide',
    'mouse_left', 'mouse_right', 'mouse_middle',
    'scroll_up', 'scroll_down'
]

def validate_keys(keys):
    if not isinstance(keys, list) or len(keys) == 0:
        return False, "Keys debe ser un array no vacío"

    for key in keys:
        if key.lower() not in VALID_KEYS:
            return False, f"Tecla inválida: {key}"

    return True, None

def validate_image_exists(image_path):
    if not image_path:
        return False, "Image path no puede estar vacío"

    # Extraer solo el filename (sin el prefijo assets/)
    filename = image_path.replace('assets/', '').replace('img/', '').replace('images/', '')

    # Construir path absoluto
    full_path = os.path.join(paths.get_images_dir(), filename)

    if not os.path.exists(full_path):
        return False, f"Imagen no encontrada: {filename}. Por favor, sube la imagen primero."

    return True, None

def validate_keybinding_data(data, is_update=False):
    errors = []

    if 'keys' in data:
        valid, error = validate_keys(data['keys'])
        if not valid:
            errors.append(error)

    if 'type' in data:
        if data['type'] not in ['toggle', 'hold']:
            errors.append("Type debe ser 'toggle' o 'hold'")

    if 'image' in data:
        valid, error = validate_image_exists(data['image'])
        if not valid:
            errors.append(error)

    if 'transition_in' in data and data['transition_in']:
        trans = data['transition_in']
        if 'image' in trans:
            valid, error = validate_image_exists(trans['image'])
            if not valid:
                errors.append(f"Transition in: {error}")

    if 'transition_out' in data and data['transition_out']:
        trans = data['transition_out']
        if 'image' in trans:
            valid, error = validate_image_exists(trans['image'])
            if not valid:
                errors.append(f"Transition out: {error}")

    if not is_update:
        if 'keys' not in data:
            errors.append("Campo requerido: keys")
        if 'type' not in data:
            errors.append("Campo requerido: type")
        if 'image' not in data:
            errors.append("Campo requerido: image")

    return len(errors) == 0, errors
