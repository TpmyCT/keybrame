import sys
import os

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Redirect stdout/stderr to suppress messages during import
stdout_backup = sys.stdout
stderr_backup = sys.stderr
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

try:
    from keybrame.config.manager import ConfigManager
    from keybrame.utils import paths

    config_manager = ConfigManager(paths.get_database_path())
    config = config_manager.get_config()

    sys.stdout.close()
    sys.stderr.close()
    sys.stdout = stdout_backup
    sys.stderr = stderr_backup

    print(config.get('port', 5000), end='')
except Exception:
    if sys.stdout != stdout_backup:
        sys.stdout.close()
        sys.stdout = stdout_backup
    if sys.stderr != stderr_backup:
        sys.stderr.close()
        sys.stderr = stderr_backup
    print('5000', end='')
