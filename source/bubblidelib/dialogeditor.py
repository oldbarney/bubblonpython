"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import os

from bubblib.bubbljson import fromJSON
from bubblib.bubblmach import BBSM
from bubblib.globaldefs import ExState
from bubblib.table import Table, RawTable
from bubblib.utils import log


class DialogEditor:
    field_specs=['Label','Thing','X:int','Y:int',
                 'W:int','H:int','Fill','Colour',
                 'Align','Field','Font','Params']
    field_names=['Label','Thing','X','Y',
                 'W','H','Fill','Colour',
                 'Align','Field','Font','Params']
    def __init__(self,x,y,table,fields,callback):
        if isinstance(table,str):
            table=Table(table,self.field_specs)

            table.insert_row(-1,['Dialog','win',
                0,0,600,400,'#FFF','#000','','','sanserif,10',''])

        self.callback=callback

        if not isinstance(table,RawTable):
            self.callback(None)
            return
        if table.field_names!=self.field_names:
            log('Table fieldnames is',table.field_names)
            log('DialogEditor.fieldnames is',self.field_names)
            self.callback(None)
            return

        self.table=table
        if isinstance(fields,Table):
            fields=fields.field_names
        elif isinstance(fields,str):
            fields=fields.split(',')
        else:
            fields=list(fields)
        self.fields=fields


        init=BBSM.sys_init()
        self.mach=BBSM(self,'d_ed',init,external_db=False)
        self.mach.machine_state_changed.connect(self.mach_state_changed)
        self.mach.database[self.table.table_name]=self.table
        self.mach.diags['dialogeditor'].variables['table']=self.table.table_name
        self.mach.diags['dialogeditor'].variables['fields']=self.fields
        self.mach.command('goto','dialogeditor',1)
        self.mach.command('run')

    def mach_state_changed(self):
        log('dialogEditor mach_state_changed')
        if self.mach.state==ExState.stopped_on_link:
            self.mach.machine_state_changed.disconnect(self.mach_state_changed)
            if self.mach.diags['dialogeditor'].variables['result']=='Ok':
                self.result=self.mach.database[self.table.table_name]
            else:
                self.result=None
            self.callback(self.result)
            self.mach.command('kill')

            #uiserver.ui.root.after(0, self.mach.command('kill'))
            log('Diag editor machine told to die')
            #self.mach.thr.join()
            self.mach=None