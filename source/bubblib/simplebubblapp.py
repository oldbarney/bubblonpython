"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import sys
import os

from .basebubblapp import BaseBUBBLApp
from .bubbljson import toJSON
from .globaldefs import ExState
from .logger import Logger
from .uiserver import ui
from .utils import runtime_log as log

class ErrorIDE:
    def handle_python_syntax_error(self, message, diag_name, node_no, line_no,col_no):
        print('Handling python syntax error', message, diag_name, node_no,
              line_no, col_no)

    def handle_python_block_exception(self,diag_name,node,python_exception):
        print(f'Python block exception in node:{node} in {diag_name}:{python_exception.exception}')

class SimpleBUBBLApp(BaseBUBBLApp):
    def __init__(self,code,is_main_app=False,logfolder=None,
                 exit_func=None,loglevel=4):
        filename=os.path.abspath(sys.argv[0])
        BaseBUBBLApp.__init__(self,code,filename=filename,external_db=True)
        self.is_main_app=is_main_app
        self.mach=self.machs['main']
        if logfolder is not None:
            self.mach.logger=Logger(log_folder=logfolder,level=loglevel)
        else:
            self.mach.logger.level=loglevel
        self.got_running=False
        self.exit_func=exit_func
        self.mach.machine_state_changed.connect(self.mach_state_changed)
        self.bubblIDE=ErrorIDE()

    def run(self):
        #print('running now')
        self.mach.command('goto','main',self.mach.diags["main"].links[0])
        self.mach.command('run')
        self.got_running=True

    def mach_state_changed(self):
        if not self.got_running:
            return
        if self.mach.state in (ExState.stopped_on_link,
                               ExState.stopped_on_node,
                               ExState.exited):
            self.mach.save_data_to_db()
            if self.exit_func is not None:
                self.exit_func(self)
            ui.root.after_idle(self.close_down)

    def close_down(self):
        for mach in reversed(list(self.machs)):
            self.close_child_mach(mach)
        self.mach.cleanup_dialog()
        self.mach.command('kill')
        self.mach.app.close_children()
        self.mach.app.sys_mach.command('kill')
        log('Simple bubblApp Machine told to die')
        if self.is_main_app:
            ui.root.after_idle(ui.close)

class Runner:
    def __init__(self,code):
        self.code=code
        ui.root.after_idle(self.run)

    def run(self):
        def exit_func(*args):
            ui.root.destroy()
        kwargs={}
        for arg in sys.argv[1:]:
            if arg.startswith('logfolder='):
                kwargs['logfolder']=arg[10:]
            elif arg.startswith('loglevel='):
                kwargs['loglevel']=arg[9:]

        self.app=SimpleBUBBLApp(self.code,is_main_app=True,**kwargs)
        self.app.run()

app_prefix=f'''#!python
pbub=r"""
'''
app_suffix='''
"""
import sys
import os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+os.sep+'bubblib')
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+os.sep+'bubblidelib')
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+os.sep+'bubblib.zip')

from bubblib.simplebubblapp import Runner
from bubblib.uiserver import ui
if __name__=='__main__':
    Runner(pbub)
    ui.run()
'''

def app_string(json):
    return app_prefix+json+app_suffix

def get_pbub_from_python(python):
    def quoted_slist(slist):
        return ',\n'.join(toJSON(el) for el in slist)

    return ("""
    {"config": {},
     "machines": {"main": {"diags": {"main": {"nodes": {"1": {"links": [2],
              "params":["""+quoted_slist(python.splitlines())+
    """],
              "pos": [15, 8],
              "size": [9, 2],
              "type": "PYTHON"},
        "2": {"links": [],
              "params": [0],
              "pos": [15, 12],
              "size": [3, 2],
              "type": "LINK"}},
"signature": {"linknames": [],
            "loop": 0,
            "params": ["#DDD"],
            "pos": [15, 5],
            "size": [7, 1],
            "start": 1,
            "undoable": true},
"vars": {}}},
"tables": {
"_config": {"_table": {"defaults": ["", ""],
      "fieldnames": ["key:none",
                     "value:none"],
      "name": "_config",
      "rows": [
          ["scale", "normal"],
          ["tkinterfiledialog",
           false]]}},
"_history": {"_table": {"defaults": ["", ""],
       "fieldnames": [
           "key:none",
           "value:none"],
       "name": "_history",
       "rows": []}}}}}}
    """)
