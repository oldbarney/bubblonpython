"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import sys,os
from zipfile import ZipFile

from bubblib.bubbljson import toJSON
from bubblib.table import Table

default_apps=('helloworld.py',
              'jigsaw.py',
              'sudokusolver.py',
              'alarm.py',
              'oware.py',
              'seed.png',
              'cup.png',
              'cuba.wav',
              'pompey.py',
              '_bgo.png',
              'setup.py',
              'facedetect.py',
              )

def get_default_cfg(home):
    tkinterfiledialog=sys.platform.startswith('win')
    return toJSON(
        { "ideloglevel":3,
          "loglevel":3,
          "recent":[home+'helloworld.py'],
          "state_map":{home+'helloworld.py':{"main":{"editors":[]}}},
          "tkinterfiledialog":tkinterfiledialog,
          "history":[]})

def create_home(home):
    if os.path.isfile(home+'bubblib.zip'):
        with ZipFile(home+'bubblib.zip',mode='r') as zipped:
            for app in default_apps:
                if app!='setup.py':
                    zipped.extract(app,home)

    with open(home+'bubblide.cfg','w') as f:
        f.write(get_default_cfg(home))
