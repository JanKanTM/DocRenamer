import os

### watch folder ###
SCAN_FOLDER = "path/to/your/folder"

### log-file ###
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, 'logs', 'main.log')