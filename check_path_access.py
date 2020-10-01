import os
from pathlib import Path

import bpy


def check_path_access(path):
    if path.startswith("//"):
        abs_path = Path(bpy.data.filepath).parent / path.replace("//", "")
    else:
        abs_path = Path(path)

    # TODO fix windows write permission
    if os.sys.platform == 'win32':
        return True

    write_permission = False
    try:
        abs_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        write_permission = False

    if os.access(path=abs_path, mode=os.W_OK):
        write_permission = True

    return write_permission
