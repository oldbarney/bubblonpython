"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from .machineimports import get_imported_machine_init
from .bubblevent import MessageEvent
from .bubbljson import fromJSON
from .globaldefs import ExState
from .bubblmach import BBSM
from .logger import Logger
from .table import AbstractRow
from .uiserver import ui
from .utils import log, get_resource


class BaseBUBBLApp:

    next_child=1

    def __init__(self,code,filename=None,external_db=False):
        self.filename=filename
        if isinstance(code,str):
            init=fromJSON(code)
        else:
            init=code

        self.machs={'main':BBSM(self,'main',init['machines']['main'],external_db=external_db)}
        #with open(os.path.dirname(os.path.abspath(__file__))+os.sep+"bubblutils.pbub","r") as f:
        #    sysinit=fromJSON(f.read())
        #    sysinit=sysinit['machines']['main']
        #sysinit=fromJSON(get_resource('bubblutils.pbub'))['machines']['main']
        sysinit = BBSM.sys_init()
        self.sys_mach=BBSM(self,'_sys',sysinit,external_db=False)
        self.sys_mach.machine_state_changed.connect(self.sys_mach_state_changed)
        self.sys_mach_program=None
        self.sys_event=None
        self.child_exit_handlers={}
        self.running_machines=set()
        self.dialog_callback=None
        self.table_ed_callback=None


    def added_machine(self,filename,name=None,start_diag='',start_node=None):
        if name is None:
            name=f'{BaseBUBBLApp.next_child}'
            BaseBUBBLApp.next_child+=1
        init=get_imported_machine_init(filename)
        if init is None:
            return None
        mach=BBSM(self,name,init,external_db=False)
        self.machs[name]=mach
        mach.machine_state_changed.connect(
            lambda mach=mach:self.child_state_changed(mach))
        if start_diag:
            self.run_child_diag(name,start_diag,start_node)
        #mach.command('run')
        self.running_machines.add(mach)
        return mach

    def run_child_diag(self,name,diag,exit_func=None,node=None,**pars):
        mach=self.machs[name]
        if node is None:
            node=mach.diags[diag].links[0]
        log('run_child_diag',diag,'from',node)
        if mach.state in (ExState.stopped_on_link,
                          ExState.stopped_on_node,
                          ExState.exited,
                          ExState.quiescent):
            mach.diags[diag].variables.update(pars)
            if exit_func is not None:
                self.child_exit_handlers[mach]=exit_func
            log('running now')
            mach.command('goto',diag,node)
            mach.command('run')
        else:
            log('Cannot run diag in already running machine',level=Logger.INFO)

    def child_state_changed(self,mach):
        log('child machine_state in basebubblapp.py',repr(ExState(mach.state)))
        #print('CHILDMACHINCHANGES')
        if mach not in self.running_machines:
            return
        if mach.state in (ExState.exited,):
            if mach in self.child_exit_handlers:
                self.child_exit_handlers[mach](mach)
            else:
                self.close_child_mach(mach.name)

    def close_child_mach(self, name):
        mach=self.machs[name]
        mach.command('kill')
        self.machs.pop(mach.name)
        if mach in self.running_machines:
            self.running_machines.remove(mach)
        try:
            self.child_exit_handlers.pop(mach)
        except KeyError:
            pass

        log(f'Child machine {mach.name} shut down',
            level=Logger.INFO)

    def message_machine(self,sender,receiver,message):
        try:
            rec=self.machs[receiver]
            event=MessageEvent(sender,message)
            rec.queue_event(event)
        except KeyError:
            log('Messaging unknown machine',receiver,level=Logger.INFO)

    def run_dialog(self,mach,callback,defn_table,
                   record,loop,x=None,y=None): #todo here implement histories
        self.dialog_callback=callback

        self.record=record
        if isinstance(record,AbstractRow):
            self.wk_rec=record.get_dict()
        else:
            self.wk_rec=dict(record)

        if x is None:
            x=ui.mx()
        if y is None:
            y=ui.my()

        self.sys_mach.history=mach.history
        self.sys_mach_program='dialog'
        self.sys_mach.diags['dialogrunner'].variables['table']=defn_table
        self.sys_mach.diags['dialogrunner'].variables['record']=self.wk_rec

        if loop:
            self.sys_mach.diags['dialogrunner'].variables[
                'x']=self.sys_mach.diags['rundialog'].variables['x']
            self.sys_mach.diags['dialogrunner'].variables[
                'y']=self.sys_mach.diags['rundialog'].variables['y']
        else:
            self.sys_mach.diags['dialogrunner'].variables['x']=x
            self.sys_mach.diags['dialogrunner'].variables['y']=y

        if loop:
            self.sys_mach.command('goto','dialogrunner',2)
        else:
            self.sys_mach.history=mach.history
            self.sys_mach.command('goto','dialogrunner',1)
        self.sys_mach.command('run')

    def run_table_editor(self,parent,
                   callback,
                   mach,
                   table,
                   x=None,
                   y=None,
                   title=None,
                   width=None,
                   length=10,
                   view_mode='list-view',
                   record=0,
                   ):

        """Edit table and
        return 0 if updated
           or  1 if cancelled"""



        self.table_ed_callback=callback
        self.sys_mach_program='tableeditor'
        self.sys_mach.diags['tableeditor'].variables['parent']=parent
        self.sys_mach.diags['tableeditor'].variables['table']=table
        self.sys_mach.diags['tableeditor'].variables['record']=record
        self.sys_mach.diags['tableeditor'].variables['x']=x
        self.sys_mach.diags['tableeditor'].variables['y']=y
        self.sys_mach.diags['tableeditor'].variables['width']=width
        self.sys_mach.diags['tableeditor'].variables['title']=title
        self.sys_mach.diags['tableeditor'].variables['height']=y
        self.sys_mach.diags['tableeditor'].variables['length']=length
        self.sys_mach.diags['tableeditor'].variables['mode']=view_mode
        self.sys_mach.history=mach.history
        self.sys_mach.command('goto','tableeditor',self.sys_mach.diags['tableeditor'].links[0])
        self.sys_mach.command('run')

    def sys_mach_state_changed(self):
        if self.sys_mach_program=='dialog':
            if self.sys_mach.state==ExState.exited: #stopped_on_link:
                self.result=self.sys_mach.diags['dialogrunner'].variables['result']
                if self.result=='Ok':
                    if isinstance(self.record,dict):
                        self.record.update(self.wk_rec)
                    else:
                        for f in self.wk_rec:
                            try:
                                setattr(self.record,f,self.wk_rec[f])
                            except:
                                log('Unable to update dialog field',f,level=Logger.INFO)
                    self.dialog_callback('ok')
                elif self.result=='Esc':
                    self.dialog_callback('esc')
                else:
                    self.dialog_callback(self.result)
                    #self.sys_mach.diags['dialogrunner'].variables['_ev'])

        elif self.sys_mach_program=='tableeditor':
            if self.sys_mach.state==ExState.exited:#stopped_on_link:
                self.table_ed_callback(self.sys_mach.diags['tableeditor'].variables['result'])

    def close_children(self):
        for mach in list(self.machs):
            if mach!='main':
                self.close_child_mach(mach)

    def handle_page_event(self,event):
        pass

    @staticmethod
    def get_pbub_from_file(filename):
        with open(filename, 'r') as f:
            text = f.read()
        if filename.lower().endswith('.pbub'):
            return fromJSON(text)

        try:
            start = text.index('pbub=r"""')
        except Exception as e:
            print('NOT A BUBBL PROGRAM', e)
            raise Exception(f'Not a bubble program (1). {e}')

        text = text[start + 9:text.find('"""', start + 9)]
        try:
            result = fromJSON(text)
        except Exception as e:
            raise Exception(f'Not a bubbl program, invalid JSON: {e}')

        if 'config' not in result or 'machines' not in result:
            raise Exception(
                'Not a bubbl program, Invalid structure of Initialisation')

        return result

    #def cleanup(self):
    #    for m in self.machs:
    #        self.machs[m].cleanup()