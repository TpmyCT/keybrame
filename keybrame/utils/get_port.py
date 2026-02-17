#!/usr/bin/env python3
"""Script auxiliar para obtener el puerto configurado"""

import sys
import os

# Suprimir todos los mensajes durante la carga
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Redirigir stdout y stderr para suprimir mensajes
stdout_backup = sys.stdout
stderr_backup = sys.stderr
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

# Agregar el directorio raíz al path para poder importar keybrame
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

try:
    from keybrame.config.manager import ConfigManager
    from keybrame.utils import paths

    config_manager = ConfigManager(paths.get_database_path())
    config = config_manager.get_config()

    # Restaurar stdout y stderr antes de imprimir
    sys.stdout.close()
    sys.stderr.close()
    sys.stdout = stdout_backup
    sys.stderr = stderr_backup

    print(config.get('port', 5000), end='')
except Exception:
    # Restaurar stdout y stderr
    if sys.stdout != stdout_backup:
        sys.stdout.close()
        sys.stdout = stdout_backup
    if sys.stderr != stderr_backup:
        sys.stderr.close()
        sys.stderr = stderr_backup
    # Si falla, usar puerto por defecto
    print('5000', end='')
