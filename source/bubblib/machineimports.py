"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from bubblib.bubbljson import fromJSON

import_cache={} #Repository for imported BUBBL modules init
def get_imported_machine_init(filename):
    try:
        return import_cache[filename]
    except KeyError:
        try:
            with open(filename,'r') as f:
                import_cache[filename]=result=fromJSON(
                    f.read())['machines']['main']
            return result
        except:
            return None
