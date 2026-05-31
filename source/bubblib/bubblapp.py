"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"

from .basebubblapp import BaseBUBBLApp
from .bubblevent import BubblEvent, MouseEvent

newAppInit={'config': {},
            'machines':{
                'main':{
                    'diags':{
                        'main': {
                            'signature':{
                            'params': ['#DDD'],
                            'linknames': [],
                            'start': 0,
                            'loop': 0,
                            'undoable': True},
                            'vars': {},
                            'nodes': {}
                        },
                    },
                    'tables':{}
                },
             }
            }

class BUBBLApp(BaseBUBBLApp):
    def __init__(self,ide,init:dict,filename=''):
        BaseBUBBLApp.__init__(self,init,external_db=False)
        self.bubblIDE=ide
        self.filename=filename
        self.config=init["config"]

    def get_init(self):
        return {"config":self.config,
                "machines":{'main':self.machs['main'].get_init()}
               }


    def handle_page_event(self,event:BubblEvent):
        if isinstance(event,MouseEvent):
            page=event.page
            over=page.point_over(event.x,event.y)
            if over:
                item=page[over[-1]]
            else:
                item=None
            self.bubblIDE.handle_user_page_event(item,event)