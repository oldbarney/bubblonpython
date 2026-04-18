#!python
import subprocess
import sys

from bubblib.utils import print_

installs=[
    'pillow',
    'tkinterdnd2',
]

try:
    import tkinter as tk
except:
    installs.append('tkinter')

if (sys.version_info[0]<3 or
    sys.version_info[1]<8 or
    sys.version_info[1]==8 and sys.version_info[2]<10):
    print_('BUBBL requires python version 3.8.10 or later')
    sys.exit(1)

def is_venv():
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

if not sys.platform.startswith('win') and not is_venv():
    print_('BUBBL should be run in a virtual environment on Linux/Unix')
    sys.exit(1)

for install in installs:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", install])
    except Exception as e:
        print_('Failed to install',install,e)
