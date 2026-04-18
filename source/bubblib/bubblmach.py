"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import subprocess
import sys
import threading
import time
import tempfile
import os
import tkinter

from PIL.Image import Image

from . import utils
from .tkfiledialog import TkFileDialog

running_windows=sys.platform.startswith('win')

from collections import deque
from tkinter import colorchooser
from .gutils import BubblFont, save_canvas_message, BUBBLImage
from .tableeditor import TableEditor
from .texteditor import TextEditor

#try:
#    import sqlite3
#except:
#    sqlite3=None
sqlite3=None
from .block import ExecutableBlock
from .bubbljson import toJSON, fromJSON, GlobalDatabase
from .filedialog import get_file_dialog
from .historymanager import HistoryTable
from .logger import RuntimeException, Logger, QueueLogger
from .modaldialogs import InputDialog, AlertDialog, AskUserDialog, menu_dialog, \
    ChoiceDialog
from .uiserver import ui
from .mybuiltins import my_builtins
from .blockfactory import LoopBlock
from .bubblevent import BubblEvent, MouseEvent,AsyncEvent
from .bubblpage import BubblPage, stdoutpage, StdOutPage
from .bubblrunvm import BubblRunVM
from .bubbldiag import BubblDiag
from .iset import Iset
from .signals import Signal
from .sysvars import PageVars, FileVars, OSVars, NetworkVars
from .undoableiterator import undoable_iterator
from .utils import value_from_str, get_val_from_kvlist, get_error_and_line, \
    get_raw_val_from_kvlist, reextensioned, quoted, find_func, \
    log, is_valid_identifier, get_resource, log_level
from .globaldefs import svnames, ExState, Activity, BubblWaitException, \
    PythonBlockException, PythonBlockSyntaxException
from .table import Table, RawTable

'''
for exec - globals={}
  locals = {'_diag':diag}
'''


# from random import random,choice
max_undos = 1000000
page_timeout = 1
ui_timeout = 0.25

class ConfigAccessor:
    def __init__(self,mach):
        self.mach=mach

    def __getitem__(self,key):
        if isinstance(key,str):
            default=key
        else:
            try:
                default=key[1]
                key=key[0]
            except:
                return key
        try:
            tb=self.mach.database['_config']
            return tb[tb.rows_matching('key',key)[0]].value
        except:
            return default

    def __setitem__(self,key,value):
        self.mach.database['_config'].update_or_insert_record(
            'value',value,
            'key',key
        )

class BBSM:
    """BUBBL Behavioural State Machine -manages a BUBBL program execution
    Bubble instructions ('blocks') have compiled code attributes and
    compiled 'undoable' code attributes. 'For' and 'Call' blocks also
    have similar 'auxcode' attributes to handle their alternative
    'entry points'
    This class maintains a current 'diag'(BUBBL diagram),'node'
    (block) and 'link' attributes equivalent to an 'instruction pointer'.
    The 'node' attribute holds the index of next block whose code/
    undoable code will be executed and the 'link' attribute holds the
    link-number followed from the previous block executed.  A 'node'
    value of 0 indicates that the previous link was not connected to a block.
    This class also maintains a call-stack with values pushed and popped
    by 'call' blocks and 'link' blocks.
    An instruction's code (or undoable_code etc.) is executed with a
    Python 'exec' call, with globals being the 'diag' attribute's
    'variables' or '_variables' dictionary.  A diagram's 'variables' dict
    is a wrapper for the _variable's dict which intercepts inserts,
    updates and deletes to the underlying dictionary to generate
    'undoable' code, allowing for programs to be stepped backwards.

    Each block is responsible for keeping 'diag','node' and 'link'
    attributes updated ('via the _variables' '_mach' entry which maps
    on to this object).  A block which does not execute immediately
    (such as a 'wait' block) throws a BubblWaitException to tell this
    machine to manage asynchronous execution of the BUBBL program

    An event queue is maintained by this machine and if certain
    BubblWaitExceptions have been raised, events will trigger on-going
    program execution.  Other BubblWaitExceptions are handled by
    callbacks within the instruction's code.

    BubblWaitExceptions ensure that after the 'wait', the program
    continues to run in the same mode as before the exception.

    Bubbl blocks are executed synchronously with the TkInter event
    loop, always scheduled in the main thread with an 'after_idle' call.
    For maximum execution speed, non-waiting blocks are executed one
    after another for a maximum time period before deferring to the
    event loop.
    """
    python_block_exception_class=PythonBlockException
    try:
        with open("bubblib" + os.sep + "bubblutils.pbub", "r") as f:
            bubblutils_source=f.read()
    except FileNotFoundError:
        bubblutils_source=get_resource('bubblutils.pbub')


    def __init__(self, app, name, init,external_db=True,logger=None):
        self.machine_state_changed = Signal()
        self._state = ExState.quiescent
        self.external_db=external_db
        self.activity = Activity.none
        self.runtime_exception = None

        self.app = app
        self.name = name
        self.pagevars = PageVars(self)
        self.osvars = OSVars(self)
        self.network = NetworkVars(self)
        self.filevars = FileVars(self)
        self.ui=ui
        self.config=ConfigAccessor(self)
        self.database = GlobalDatabase(**init['tables'])
        if '_history' not in self.database:
            self.database['_history'] = Table('_history', ['key', 'value'])
        if '_config' not in self.database:
            self.database['_config'] = Table('_config', ['key', 'value'])
            self.config['scale']='normal'
            self.config['tkinterfiledialog']=utils.windows

        for tn in self.database:
            t=self.database[tn]
            if isinstance(t,Table):
                t.mach = self

        self.history = HistoryTable(self.database['_history'])

        self.sys_vars = {
            "_mach": self,
            #"_PR": self.printervars,
            "_fs": self.filevars,
            "_pg": self.pagevars,
            "_os": self.osvars,
            "_nw": self.network,
            "_db": self.database,
            '_Iset': Iset,
            '_eval': value_from_str,
            "__builtins__": my_builtins
        }

        self.event_queue = deque(maxlen=400)  # that should be long enough
        if logger is None:
            logger=QueueLogger(level=1)
        self.logger=logger
        self._exec_exception=''
        self.popped_event = None
        self.dialog = None
        self.stack = []
        self.undo_list = deque(maxlen=max_undos)
        # contains alternate records of ('diagname',node), ('diagname',[deltas])
        self.for_iterators = {}  # dict of all for_loop reversible iterators
        self.current_page = stdoutpage
        self.pages = {}
        self.page_names = []
        self.last_node = 0
        self.node = 0
        self.link = 0
        self.steppable_diags = []
        self.step_stack_level=0
        self.last_diag = ''
        self.last_node = 0

        self.error_message = ''
        self.current_event = BubblEvent("START")
        self.current_editor = None

        self.stopped=False
        self.run_func=None


        if 'main' in init:  # handle old format diags only
            init = {'diags': init, 'tables': {}}

        diags = init['diags']
        self.diags = {dn: BubblDiag(self, dn, diags[dn]) for dn in diags}

        for dn in self.diags:
            self.diags[dn].compile_nodes()
        if not "main" in self.diags:
            self.diags["main"] = BubblDiag(self,'main')  # ..getBlank("main")
        self.diag = self.diags["main"]

        self.runvm = BubblRunVM(self)
        self.break_point = None
        self.wait_exception_class=BubblWaitException

        if self.name=='main' and self.external_db:
            self.load_data_from_db()
        #self.tablevars._restore_globals()

    @classmethod
    def sys_init(cls):
        return fromJSON(cls.bubblutils_source)['machines']['main']

    def log(self,*args,**kwargs):
        self.logger.log(*args,'Diag:',self.diag.name,f'Node:{self.node}',**kwargs)
        try:
            self.app.bubblIDE.refresh_runtime_log()
        except:
            pass

    @property
    def tkinter_file_dialog(self):
        return self.config[('tkinterfiledialog', running_windows)]

    @property
    def message(self):
        return None
    @message.setter
    def message(self,value):
        self.log('message pars',value)
        try:
            self.app.message_machine(self.name,value[0],value[1])
        except Exception as e:
            self.log('Invalid message',e,level=2)

    def save_data_to_db(self):
        if not self.external_db:
            return
        filename=self.app.filename
        if not filename:
            return
        if sqlite3:
            self.save_data_to_sqlite_db(filename)
        else:
            self.save_data_to_jsonfile(filename)

    def save_data_to_sqlite_db(self,filename):
        filename=reextensioned(filename,'db')
        con=sqlite3.connect(filename)

        con.execute('CREATE TABLE IF NOT EXISTS variables(diagname,varname,json_blob);')
        con.execute('CREATE TABLE IF NOT EXISTS tables(name,json_blob);')
        con.execute('DELETE from variables;')
        con.execute('DELETE from tables;')
        values=[]
        for diag in self.diags.values():
            for vn in diag.normal_variable_names():
                values.append((toJSON(diag.name),
                               toJSON(vn),
                               #lzma.compress(toJSON(diag.variables[vn]).encode())))
                               toJSON(diag.variables[vn])))
        con.executemany(f'INSERT INTO variables VALUES (?,?,?);',values)

        values=[]
        for gl in self.database:
            values.append((quoted(gl),
                           #lzma.compress(toJSON(self.database[gl]).encode())))
                           toJSON(self.database[gl])))
        con.executemany(f'INSERT INTO tables VALUES (?,?);',values)
        con.commit()
        con.close()

    def save_data_to_jsonfile(self,filename):
        filename=reextensioned(filename,'json')

        variables=[]
        for diag in self.diags.values():
            for vn in diag.normal_variable_names():
                variables.append([diag.name,vn,diag.variables[vn]])
        globals=[]

        for gl in self.database:
            globals.append([gl,self.database[gl]])

        with open(filename,'w') as f:
            f.write(toJSON({'variables':variables,'globals':globals}))


    def load_data_from_db(self):
        if not self.external_db:
            return
        filename=self.app.filename
        if not filename:
            return
        if sqlite3:
            self.load_data_from_sqlite_db(filename)
        else:
            self.load_data_from_jsonfile(filename)

    def load_data_from_jsonfile(self,filename):
        filename=reextensioned(filename,'json')
        try:
            with open(filename,'r') as f:
                data=fromJSON(f.read())
        except:
            log('Failed to load database from',filename,level=2)
            return
        try:
            variables=data['variables']
        except:
            log('Failed to find "variables" in',filename,level=2)
            variables=[]
        for spec in variables:
            try:
                dn,vn,v=spec
                self.diags[dn].variables[vn]=v
            except Exception as e:
                log('Failed to initialiase variable',e,level=2)

        try:
            globals=data['globals']
        except:
            log('Failed to find "globals" in',filename,level=2)
            globals=[]
        for spec in globals:
            try:
                vn,v=spec
                if isinstance(v,Table):
                    v.mach=self
                self.database[vn]=v
            except Exception as e:
                log('Failed to initialiase _db variable',e,level=2)

    def load_data_from_sqlite_db(self,filename):
        filename=reextensioned(filename,'db')
        con=sqlite3.connect(filename)
        cursor=con.cursor()
        try:
            cursor.execute('SELECT diagname,varname,json_blob FROM variables;')
            for (dn,vn,vb) in cursor.fetchall():
                try:
                    self.diags[fromJSON(dn)].variables[fromJSON(vn)]=fromJSON(vb)
                except IndexError:
                    pass
            cursor.execute('SELECT name,json_blob FROM tables;')
            for (gl,glc) in cursor.fetchall():
                #gl_var=fromJSON(lzma.decompress(glc).decode())
                gl_var=fromJSON(glc)
                if isinstance(gl_var,Table):
                    gl_var.mach=self
                self.database[fromJSON(gl)]=gl_var
        except Exception as e:
            self.log('Failed to initialise data from',filename,':',e,level=2)

        cursor.close()
        con.close()

    def runtime_error(self, message):
        self.runtime_exception = RuntimeException(self, message)
        self.stopped=True  # just in case


    def raise_python_syntax_error(self,message,line_no,col_no):
        raise PythonBlockSyntaxException(message,line_no,col_no)

    def python_syntax_error(self,message,line_no,col_no):
        #print('pse',message,line_no,col_no)
        self.stopped = True
        self.state=ExState.stopped_on_node
        self.app.bubblIDE.handle_python_syntax_error(message,self.diag.name,self.node,line_no,col_no-1)


    def is_active(self):
        return self.state == ExState.active

    def is_stepping_back(self):
        return self.is_active() and self.activity in (
        Activity.stepping_back_to, Activity.stepping_back)

    def is_running(self):
        return (self.is_active() and
                self.activity in (Activity.running,
                                  Activity.undoably_running,
                                  Activity.stepping,
                                  Activity.running_to,
                                  Activity.undoably_running_to))

    def can_run_to(self):
        return self.is_running() or self.state == ExState.stopped_on_node

    def cleanup_dialog(self,do_stop=False):
        if self.dialog is not None:  # todo here close dialog windows
            self.dialog.close()
            self.dialog = None
            if do_stop:
                self.state=ExState.stopped_on_node,'CLEAN UP DIALOG'

    def get_db_list(self):
        return [(v,isinstance(self.database[v],RawTable)) for v in self.database]# if isinstance(self.database[tab],Table)]

    def find(self, key, cased, whole_word, scope):
        finder_func = find_func(key, cased, whole_word)
        self.log('finder_func is',finder_func)
        finds={}
        def find_in_diag(diag):
            nodes=diag.nodes
            d_finds={}
            for no in nodes:
                s=finder_func(str(nodes[int(no)].params))
                if s:
                    d_finds[int(no)]=s
            return d_finds
        if scope=='All blocks':
            finds={}
            for diag in self.diags.values():
                d_finds=find_in_diag(diag)
                if d_finds:
                    finds[diag.name]=d_finds
        elif scope=='Current block':
            finds={}
            ide=self.app.bubblIDE
            self.log('ide is ',ide)
            ed=ide.get_current_editor()
            self.log('ed is',ed)
            diag=ed.diag
            self.log('diag is',diag)
            d_finds=find_in_diag(diag)
            if d_finds:
                finds[diag.name]=d_finds
        elif scope=='Tables':
            for table in self.database:
                if not isinstance(table,Table):
                    continue
                t_finds={}
                s=finder_func(table.field_names)
                if s>0:
                    t_finds[-1]=s
                for i,row in enumerate(table):
                    s=find_func(row.get_list())
                    if s>0:
                        t_finds[i]=s
                if t_finds:
                    finds[table.table_name]=t_finds

        return finds

    def bug_exception(self, message,e,code_text):

        mess, line_no = get_error_and_line(e)
        self.runtime_exception = RuntimeException(
            self,
            message+mess,
            line_no,
            code_text)
        self.log('Bug Exception:', message, level=3)

    def print_code(self, undoable=False, aux=False):  # For debugging only
        #list the currently executing block's source
        inst = self.diag.nodes[self.node]

        def get_code():
            if aux:
                if undoable:
                    return 'U-AUX\n' + inst.undoable_auxcode_text()
                else:
                    return 'AUX\n' + inst.auxcode_text()
            else:
                if undoable:
                    return inst.undoable_code_text()
                else:
                    return 'U-\n' + inst.code_text()

        log(f'''
diag:{self.diag.name} node:{self.node} type:{inst.type_name}
pars:{inst.params}
*********START_mach.print_code**{'undoable' if undoable else '*******'}********
{get_code()}
***************FINISH_mach.print_code*******************
''')

    def vref(self, key):
        p = key.find('.')
        sv = key[:p]
        vn = key[p + 1:]
        if sv in svnames:  # and vn in self.__dict__[sv]:
            return sv, vn
        return None, key

    def add_undo(self, delta):
        self.undo_list.append(delta)
        while self.undo_list and not isinstance(self.undo_list[0],int): #When undo_list clipped
            self.undo_list.popleft() #throw away whole history of instruction

    def pop_undo(self,node):
        while self.undo_list:
            if self.undo_list.pop()==node:
                break

    def remove_undos_with_diag(self,target):
        # go back through undos applying pushes and pops to stack only until
        # target not in stack. If it's still in stack unstack until it isn't.

        while any(diag==target for (diag,_) in self.stack):
            if len(self.undo_list)==0:
                self.stack.pop()
            else:
                par=self.undo_list.pop()
                if isinstance(par,int):
                    continue
                if par[0]=='push':
                    self.stack.append(par[1:])
                elif par[0]=='pop':
                    self.stack.pop()

    def okundo(self):
        #log('BUBBLMACH okundo')
        if len(self.undo_list) > 0:
            par = self.undo_list.pop()
            #log('BUBBLMACH okundo first par is', par)
            while not isinstance(par, int):
                try:
                    self.runvm.delta(par)
                except Exception as e:
                    log('BUBBLMACH okundo error',e,level=3)
                    return False
                if len(self.undo_list) == 0:
                    return False
                par = self.undo_list.pop()
            self.node = par
            return True
        else:
            return False

    def page_undo(self):
        try:
            BubblPage.ok_undo(self)
        except Exception as e:
            log(f'BBSM.page_undo failed:{e}',level=Logger.INFO)

    def get_undoable_iterator(self, iterable):
        return undoable_iterator(iterable)

    def showText(self, text):
        log(text)

    def get_init(self):
        return {'diags': {dn: self.diags[dn].get_init()
                          for dn in self.diags if not dn.startswith('_')},
                'tables': {tn: self.database[tn]
                           for tn in self.database}
                }

    def remove_page(self, name, undoable):
        if name in self.pages:
            page = self.pages.pop(name)
            self.page_names.remove(name)
            if undoable:
                #log('mach undoably clearing page')
                page.undoably_clear_page()
                #log('undoably cleared page')
                self.add_undo(['create_page', name, page.markups])
                #log(f'undolist had appended:{self.undo_list[-1]}')
            if self.current_page == page:
                if self.pages:
                    self.current_page = self.pages[
                        self.page_names[- 1]]
                else:
                    self.current_page = stdoutpage
            page.canvas.master.destroy()

    def close_page(self, name):
        if name != 'STDOUT':
            self.remove_page(name, False)

    def undoably_close_page(self, name):
        if name != 'STDOUT':
            self.remove_page(name, True)

    def close_all_pages(self):
        for page in list(self.pages):
            self.close_page(page)

    def clear_page(self, name):
        if name in self.pages:
            page = self.pages[name]
            page.clear_page()
            # page.repaint_all()

    def undoably_clear_page(self, name):
        if name in self.pages:
            page = self.pages[name]
            page.undoably_clear_page()
            # page.repaint_all()

    def select_page(self, undoable, name, **kwargs):
        if name in self.pages:
            if undoable:
                #log('getting page markups for ', name)
                mups = self.current_page.markups
                #log('got page markups')
                self.add_undo(["page_update", name, mups])
            self.current_page = self.pages[name]
            #log('Reselect Page kwargs',kwargs)
            #del kwargs['x']
            #del kwargs['y']
            self.current_page.update(kwargs)
        else:
            if undoable:
                self.add_undo(["page_destroy", name])
            self.do_select_page( name, **kwargs)

    def do_select_page(self, name, **kwargs):
        # log(f'Machine selecting page {name} ')
        if name == 'STDOUT':
            if self.current_page == stdoutpage:
                return
            self.current_page = stdoutpage
            return
        page = BubblPage(self, name, **kwargs)
        self.current_page = self.pages[name] = page
        self.page_names.append(name)

    def current_xy(self):
        page = self.current_page
        if page == stdoutpage:
            return ui.mx(), ui.my()

        # log('current_xy page.x',page.x,'y',page.y,'cx',page.cx,'cy',page.cy)
        return page.x + page.cx, page.y + page.cy

    def refresh_current_page(self):
        # log(f'refreshing {self.current_page}')
        #ui.root.update_idletasks()
        pass

    def update_page(self, name, undoable, markups):
        if name in self.pages:
            page = self.pages[name]
            if undoable:
                self.add_undo(["page_update", name, page._get_markups()])
            page._apply_markups(markups)

    def input_vars(self, links,var_names, markups):
        # Return Null or array of strings to be assigned to vars in varbs list
        hkey = get_raw_val_from_kvlist('history', markups, 'DEFAULT')
        log('BBSM input_vars var_names', var_names)
        self.cleanup_dialog()
        def callback(results,links=links,var_names=var_names):
            if results is not None:
                for name, value in zip(var_names, results):
                    vhkey=f'{hkey}{name}' if hkey.endswith('_') else hkey
                    self.history.add(vhkey, value)
                    if self.undoable:
                        self.diag.variables[name]=value_from_str(value)
                    else:
                        self.diag.variables[name]=value_from_str(value)
                self.link=1
            else:
                self.link=0
            link = links[self.link]
            if link == 0:
                self.state = ExState.stopped_on_link
            else:
                self.node = link
                ui.root.after_idle(self.run_func)

        self.dialog = InputDialog(callback, *self.current_xy(),
                                  var_names,
                                  hkey,
                                  markups,
                                  tkinterfiledialog=self.tkinter_file_dialog,
                                  history=self.history)
        raise BubblWaitException('INPUT')

    def alert(self,links, message, markups):
        def callback(links=links):
            self.link=0
            link=links[0]
            if link==0:
                self.state = ExState.stopped_on_link
            else:
                self.node = link
                ui.root.after_idle(self.run_func)
        self.cleanup_dialog()
        self.dialog = AlertDialog(callback, *self.current_xy(), f'{message}', markups,history=self.history)
        raise BubblWaitException('ALERT')

    def yes_no_esc(self, links,question, markups):
        def callback(res,links=links):
            if res == 'esc':
                self.link = 0
            elif res == 'no':
                self.link = 1
            else:
                self.link = 2
            link=links[self.link]
            if link==0:
                self.state = ExState.stopped_on_link
            else:
                self.node = link
                ui.root.after_idle(self.run_func)

        self.cleanup_dialog()
        self.dialog = AskUserDialog(callback, *self.current_xy(), question, markups)
        raise BubblWaitException('ASK')

    def get_markup(self, key, kvlist, default):
        return get_val_from_kvlist(key, kvlist, default)

    def input_choice(self,links,variable, choices, markups):
        def callback(result,links=links,variable=variable):
            if result is not None:
                if is_valid_identifier(variable):
                    if self.undoable:
                        if variable in self.diag.variables:
                            self.add_undo(['varassign',variable,self.diag.variables[variable]])
                        else:
                            self.add_undo(['vardel',variable])
                        self.diag.variables[variable]=result
                    else:
                        self.diag.variables[variable]=result
                self.link=1
            else:
                self.link=0
            link=links[self.link]
            if link==0:
                self.state = ExState.stopped_on_link
            else:
                self.node = link
                ui.root.after_idle(self.run_func)

        parent = self.get_parent()
        self.dialog = ChoiceDialog(parent, callback,
                                   choices, markups)
        raise BubblWaitException('CHOICE')

    def colour_menu(self, default, markups):
        parent = ui.root
        ui.root.deiconify()
        ui.root.lift()
        ui.root.withdraw()
        log('Colour menu parent is ', parent)
        if not ui.is_safe_colour(default):
            default = '#888'

        x=get_val_from_kvlist('x',markups,ui.root.winfo_pointerx())
        y=get_val_from_kvlist('y',markups,ui.root.winfo_pointery())

        parent=tkinter.Toplevel()
        parent.overrideredirect(True)
        parent.geometry(f"1x1+{x+200}+{y+100}")
        result = colorchooser.askcolor(default,parent=parent)  # ,alog(*self.current_xy(),parent,default,markups)
        parent.destroy()
        if result[0] is None:
            return result[0]
        return result[1]

    def file_menu(self, links, variable, default, markups):
        self.cleanup_dialog()

        saveas = get_val_from_kvlist('saveas', markups, False)
        directory = get_val_from_kvlist('folder', markups, False)
        multiple = get_val_from_kvlist('multiple', markups,
                                       False) and not saveas
        title=get_val_from_kvlist('title',markups,None)
        hkey = 'FILE_' + get_val_from_kvlist('history', markups, 'DEFAULT')
        show_hidden = get_val_from_kvlist('hidden', markups, False)
        view = get_val_from_kvlist('view', markups, 'list')
        filetypes = get_val_from_kvlist('filetypes', markups, 'All:*')
        widths = [200, 50, 80, 150]

        if default is None:
            default = ''

        def process_callback(result,
                             variable=variable,
                             links=links,
                             multiple=multiple):
            self.dialog = None
            if result is None:
                self.link = 0
            else:
                if is_valid_identifier(variable):
                    if self.undoable:
                        if variable in self.diag.variables:
                            self.add_undo(['varassign', variable,
                                           self.diag.variables[variable]])
                        else:
                            self.add_undo(['vardel', variable])
                        self.diag.variables[variable] = result
                    else:
                        self.diag.variables[variable] = result
                    if not multiple:
                        self.history.add(hkey, result)
                self.link = 1

        if self.tkinter_file_dialog:
            def callback(result,links=links):
                process_callback(result)
                self.node = links[self.link]
            self.dialog = get_file_dialog(default,
                         callback,
                         saveas=saveas,
                         directory=directory,
                         multiple=multiple,
                         history=self.history.get_list(hkey),
                         show_hidden=show_hidden,
                         icon_view=view == 'icons',
                         filter=filetypes,
                         widths=widths,
                         title=title,
                         use_tkinter=True)
        else:
            def callback(result,links=links):
                process_callback(result)
                node=links[self.link]
                if node:
                    self.node=node
                    ui.root.after_idle(self.run_func)
                else:
                    self.state = ExState.stopped_on_link

            self.dialog = get_file_dialog(default,
                         callback,
                         saveas=saveas,
                         directory=directory,
                         multiple=multiple,
                         history=self.history.get_list(hkey),
                         show_hidden=show_hidden,
                         icon_view=view == 'icons',
                         filter=filetypes,
                         widths=widths,
                         title=title,
                         use_tkinter=False)
            raise BubblWaitException('FILEMENU')

    def run_text_editor(self,links,variable,
                        x=None,y=None,
                        width=None,
                        length=None,
                        title=None):

        if isinstance(self.current_page,StdOutPage):
            parent=ui.root
        else:
            parent=self.current_page.window
        if x is None:
            x=ui.mx()
        else:
            x=int(x)
        if y is None:
            y=ui.my()
        else:
            y=int(y)
        if width is None:
            width=640
        else:
            width=int(width)
        if length is None:
            height=480
        else:
            height=int(length)*BubblFont().line_space

        def update_func(text,links=links,variable=variable):
            if text is not None:
                self.link=0
                if is_valid_identifier(variable):
                    if self.undoable:
                        self.diag.variables[variable]=text.replace('<br />','\n')
                    else:
                        self.diag.variables[variable]=text.replace('<br />','\n')
            else:
                self.link=1
            link = links[self.link]
            if link == 0:
                self.state = ExState.stopped_on_link
            else:
                self.node = link
                ui.root.after_idle(self.run_func)
        try:
            text=f'{self.diag.variables[variable]}'
        except KeyError:
            text=''

        if title is None:
            title=variable

        self.dialog=TextEditor(parent,x,y,update_func,text=text,
                      title=title,
                      width=width,
                      height=height,
                      )
        raise BubblWaitException('TEXTED')

    def run_table_editor(
         self,
         parent,
         links,
         mach,
         table,
         x=None,
         y=None,
         title=None,
         width=None,
         length=10,
         view_mode='list-view',
         record=0
         ):
        def callback(result,links=links):
            if result=='ok':
                self.link = 0
            else:
                self.link= 1
            link=links[self.link]
            if link==0:
                self.state=ExState.stopped_on_link
            else:
                self.node=link
                ui.root.after_idle(self.run_func)

        self.dialog=self.app.run_table_editor(
            parent,
            callback,
            mach,
            table,
            x=x,
            y=y,
            title=title,
            width=width,
            length=length,
            view_mode=view_mode,
            record=record,
        )
        raise BubblWaitException('TABLEED')

    def run_dialog(self,links,defn_table, record, loop, x=None, y=None,
                   histories=None):  # todo here implement histories
        self.cleanup_dialog()
        def callback(result,links=links,event=None):
            if result=='ok':
                self.dialog=None
                self.link=0
            elif result=='esc':
                self.link=1
                self.dialog=None
            else:
                self.diag.variables['_ev']=result
                self.link=2
            link=links[self.link]
            if link==0:
                self.state=ExState.stopped_on_link
            else:
                self.node=link
                ui.root.after_idle(self.run_func)

        #if histories :y is None: todo sort it out


        self.dialog = self.app.run_dialog(self,
            callback, defn_table, record,
            loop, x=x, y=y)
        raise BubblWaitException('DIALOG')


    def edit_table_list_view(self,table,record,length,x=None,y=None,col_widths=None):
        def finished_editing(update,offset,col_widths,width,height):
            #update True=ok, false=cancel, None=Switch view
            pass

        try:
            parent=self.current_page.window
        except:
            parent=self.get_parent()

        self.log('Ed Table List View parent is ',parent)
        self.log('Ed Table List View table is ',table)
        self.log('Ed Table List View record is ',record)

        TableEditor(parent,
            table,
            finished_editing,
            offset=record,
            length=length,
            col_widths=col_widths,
            allow_record_view=True,
            x=x,
            y=y)
        raise BubblWaitException('TABLEED')

    def get_parent(self):
        return ui.root
        """try:
            parent = self.current_page.window
            parent.lift()
        except:
            log('file --menu parent is not current page.window')
            try:
                parent = self.app.bubblIDE.desktop_window
                parent.lift()
            except:
                log('file menu parent is not desktop window')
                parent = ui.root
                # ui.root.lift()
            # ui.root.lift()
        return parent
"""

    def menu(self, items, links,markups):
        # return '1-based index of item according to user choice
        # or 0 for esc/cancel
        self.cleanup_dialog()
        parent = self.get_parent()
        def callback(item,items=items,links=links):
            self.dialog=None
            if item is None:
                self.link=0
            else:
                self.link=1+items.index(item)

            link=links[self.link]
            if link==0:
                self.state=ExState.stopped_on_link
            else:
                self.node=link
                ui.root.after_idle(self.run_func)
        self.dialog = menu_dialog(parent, callback, *self.current_xy(), items,
                                  markups)
        raise BubblWaitException('MENU')

    def create_process(self, command, links, synch=False):
        if synch:
            exited=threading.Event()
            process=self.osvars._created_sync_process(command,
                                                      self,
                                                      exited)
            if process is None:
                self.link = 1
                self.node = links[1]
                return
            else:
                def wait_for_exit(process=process,
                                  exited=exited,
                                  links=links):
                    exited.wait(0.05)
                    if exited.is_set():
                        if process.exit_code:
                            self.link=1
                            link=links[1]
                            self.osvars.message='Non-zero exit code'
                        else:
                            self.link=0
                            link=links[0]
                        if link==0:
                            self.state=ExState.stopped_on_link
                            self.stopped=True
                        else:
                            self.node=link
                            ui.root.after_idle(self.run_func)
                    elif self.stopped:
                        process.kill()
                        self.state=ExState.stopped_on_node
                        self.stopped=True
                    else:
                        ui.root.after_idle(wait_for_exit,
                                           process,
                                           exited,
                                           links)
                    return
                ui.root.after_idle(wait_for_exit,
                                   process,
                                   exited,
                                   links)
                raise BubblWaitException('SYNCPROCESS')

        if self.osvars._ok_create_async_process(command, self):
            self.link = 0
        else:
            self.link = 1
        self.node = links[self.link]

    def play_media(self, command,file, links, synch=False):
        if synch:
            exited = threading.Event()
            process = self.osvars._created_sync_process(
                ' '.join([command, file]),
                self, exited)
            if process is None:
                self.link = 1
                self.node = links[1]
                return
            else:
                def wait_for_exit(process=process,
                                  exited=exited,
                                  links=links):
                    exited.wait(0.05)
                    if exited.is_set():
                        self.link = 0
                        link = links[0]
                        if link == 0:
                            self.state = ExState.stopped_on_link
                            self.stopped=True
                        else:
                            self.node = link
                            ui.root.after_idle(self.run_func)

                    elif self.stopped:
                        process.kill()
                        self.state = ExState.stopped_on_node
                        self.stopped=True
                    else:
                        ui.root.after_idle(wait_for_exit,
                                           process,
                                           exited,
                                           links)
                    return
                ui.root.after_idle(wait_for_exit,
                                   process,
                                   exited,
                                   links)
                raise BubblWaitException('PLAYMEDIA')

        if self.osvars._ok_create_async_process(' '.join([command,file]), self,delete_on_exit=True):
            self.link = 0
        else:
            self.link = 1
        self.node = links[self.link]

    def get_table(self, ref):
        if isinstance(ref, RawTable):
            # log('returning rawTable')
            return ref
        try:
            return self.database[ref]
        except:
            try:
                if ref.startswith('_pg.'):
                    return self.pages[ref[5:]].contents
            except:
                log(f'non existant table:{ref}',level=Logger.INFO)
                return None



    def sort_table(self, name, fields, descending,undoable):
        '''
        :param name:
        :param name,sorttype:+,-,+cased,-cased
        :param undoable:
        '''

        try:
            self.database[name].sort(fields, descending, undoable)
        except:
            log('Failed to sort table in BBSM')

    def unsort_table(self,name,order):
        try:
            self.database[name].unsort(order)
        except:
            log('Failed to sort table in BBSM',level=Logger.INFO)



    def create_table(self, name, fields, undoable):
        '''

        :param ref:
        :param fields:
            name(:type from none, str, num, int, float,
                choice:choice1:choice2:...) (=<default value>)
        :param undoable:
        :return:
        '''
        if undoable:
            if name in self.database:
                self.destroy_table(name, True)
            self.undo_list.append(['tabledestroy', name])
        defaults = []
        fieldspecs = []
        for fsp in fields:
            if isinstance(fsp, str):
                parts = fsp.split('=')
                fs = parts[0]
                if len(parts) > 1:
                    dv = '='.join(parts[1:])
                else:
                    dv = ''
            else: #allow (fieldname,type,default) field
                [fn, ft, dv] = fsp
                fs = fn + ':' + ft

            fieldspecs.append(fs)
            defaults.append(dv)
        # log(f'about to insert table {name}')
        try:
            self.database[name] =Table(name, fieldspecs, defaults, machine=self)
        except:
            log('Failed to put table in BBSM',level=Logger.INFO)

    def destroy_table(self, name, undoable):
        if name in self.database and isinstance(self.database[name], Table):
            table = self.database[name]
            if undoable:
                # log(f'reversed(table)={reversed(table)}')
                for r in reversed(table):
                    # log(f'Adding undo tableinsert {r} to {table}')
                    self.add_undo(["tableinsert", name, 0, r])
                self.add_undo(['tablecreate', name, table.full_field_specs(),False])
            del self.database[name]

    def remove_table_row(self, name, row):  # for use by undo only
        self.get_table(name).remove_row(row, False)

    def ok_swap_table_fields(self, name, row, vals):
        return self.get_table(name).ok_swap_fields(row, vals)

    def delete_table_rows(self, table, rows, undoable):
        if table == None:
            return
        rows = list(rows)
        rows.sort(reverse=True)
        for r in rows:
            table.remove_row(r, undoable)

    def insert_table_row(self, table, index, row, undoable):
        table = self.get_table(table)
        try:
            table.insert_row(index, row, undoable)
        except Exception as e:
            log(f'_mach insert_table_row error:{e}',level=Logger.INFO)

    def ok_send_to_printer(self,source,
                           command=None,
                           printer=None,
                           filename=None,
                           paper_size=None,
                           landscape=False,
                           monochrome=False,
                           postscript=False):
        """
        create a printable file (png,jpg,eps,pdf or text) defaulting to
        'bubbl.<ext>' in temporary directory.
        If pdf is specified, ghostscript needs to be installed to convert
        eps to pdf.
        Source is a page, a string, a tkinter canvas, a list (of strings),
        a PIL image, or a BUBBLImage.
        elif isinstance(source,PageVars):
            source=self.current_page
        """
        do_print=filename==None

        if command is None:
            if running_windows:
                command='print'
            else:
                command='lp'
        if printer is not None:
            printer=[print]
        else:
            printer=[]

        left_margin=0
        top_margin=0  #suppress warning

        if isinstance(source,BubblPage):
            left_margin=source.left_margin
            top_margin=source.top_margin
            source=source.canvas
            default_ext = '.eps' if postscript else '.pdf'
        elif isinstance(source,tkinter.Canvas):
            left_margin=self.config[('left_margin',0)]
            top_margin = self.config[('top_margin', 0)]
            default_ext = '.eps' if postscript else '.pdf'
        elif isinstance(source,(BUBBLImage,Image)):
            default_ext='.png'
        else:
            default_ext='.txt'

        if filename is None:
            filename=tempfile.gettempdir() + os.sep + 'bubbl'+default_ext
        else:
            if '.' not in filename:
                filename+=default_ext

        if isinstance(source,(list,tuple)):
            source='\n'.join(f'{el}' for el in source)
        if isinstance(source,str):
            with open(filename, 'w') as f:
                f.write(source)

        elif isinstance(source,tkinter.Canvas):
            message = save_canvas_message(
                source,
                filename,
                left_margin=left_margin,
                top_margin=top_margin,
                paper_size=paper_size,
                monochrome=monochrome,
                landscape=landscape)
            if message != 'Ok':
                log('Failed to print.',message,level=2)
                return False
        else:
            if not self.filevars._ok_save_to_file(source,filename):
                log('Cannot print',self.filevars.file_message,level=2)
                return False
        if do_print:
            if running_windows:
                os.startfile(filename,"print"," ".join(printer))
                return True
            else:
                exit_code = subprocess.run([command]+printer+[filename])
                if exit_code==0:
                    return True
                else:
                    log('Failed to print',filename,level=2)
                    return False
        return True

    def can_add_undos(self):
        return self.state != ExState.active or self.activity != Activity.running




    def handle_python_exception(self,python_exception):
        self.state=ExState.stopped_on_node,f'PYTHON EXCEPTION:{python_exception}'
        self.stopped=True
        self.log('Python Error', self.diag.name, self.node, level=5)
        try:
            self.app.bubblIDE.handle_python_block_exception(
                self.diag.name,
                self.node,
                python_exception
            )
        except Exception as e:
            print('failed to handle_python_exception',e)
            print(repr(e))

    def run_async_block(self, filename, diag_name, args):
        mach=self.app.added_machine(filename)
        def exit_func(mach):
            self.queue_event(AsyncEvent(mach, diag_name))
            self.app.close_child_mach(mach.name)
        if mach is not None:
            try:
                diag=mach.diags[diag_name]
                log('RUN ASYNC BLOCK ARGS',args)
                diag.variables.update(args)
                self.app.run_child_diag(mach.name, diag_name, exit_func=exit_func)
            except:
                pass

    # @Slot(BubblEvent)
    def queue_event(self, event):
        # log(f'mach event coming in {event.event_type}')
        #if event.event_type=='Timer':
        #    print('TIMER EVENT',event.Id,'QUEUED')
        if self.state == ExState.active and self.activity in (
                Activity.running,
                Activity.undoably_running,
                Activity.running_to,
                Activity.undoably_running_to,
                Activity.stepping):
            self.do_queue_event(event)
        elif self.state==ExState.quiescent:
            #self.set_event(event)
            self.app.handle_page_event(event)
        # self.event_flag.set()

    #def get_event(self):
    #    result=self.get_event_really()
    #    if result is not None:
    #        print('EVENT GOT IS',result)
    #    return result

    def do_queue_event(self,event):
        def condensed():
            if event.event_type=='MouseMv':
                try:
                    last=self.event_queue.pop()
                except IndexError:
                    return event
                while last.event_type=='MouseMv':
                    try:
                        last=self.event_queue.pop()
                    except IndexError:
                        break
                if last.event_type!='MouseMv':
                    self.event_queue.append(last)
                return event
            elif event.event_type=='MouseWh':
                try:
                    last=self.event_queue.pop()
                except IndexError:
                    return event
                while last.event_type=='MouseWh':
                    event.offset+=last.offset
                    try:
                        last=self.event_queue.pop()
                    except IndexError:
                        break
                if last.event_type!='MouseWh':
                    self.event_queue.append(last)
                return event
            elif event.event_type=='Scroll':
                try:
                    last=self.event_queue.pop()
                except IndexError:
                    return event
                while last.event_type=='Scroll' and last.source==event.source:
                    try:
                        last=self.event_queue.pop()
                    except IndexError:
                        break
                if last.event_type!='Scroll' or last.source!=event.source:
                    self.event_queue.append(last)
                return event
            elif event.event_type == 'WinSize':
                try:
                    last = self.event_queue.pop()
                except IndexError:
                    return event
                while last.event_type == 'WinSize':
                    try:
                        last = self.event_queue.pop()
                    except IndexError:
                        break
                if last.event_type != 'WinSize':
                    self.event_queue.append(last)
                return event
            else:
                return event
        try:
            ev=condensed()
            self.event_queue.append(ev)
        except Exception as e:
            print('CONDENSED EXCEPTION',e,event)

    def get_event(self):
        try:
            return self.event_queue.popleft()
        except IndexError:
            return None

    def set_event(self, event):  # Called by WAIT instr on responding to event
        if isinstance(event, MouseEvent):
            event._page.mx = event.x
            event._page.my = event.y

        for diag in self.diags:
            self.diags[diag].variables['_ev'] = event
    # @Slot(str)
    def command(self, cmd, *args,**kwargs):
        if cmd =='reset':
            self.stopped=True
            self.undo_list.clear()
            self.stack.clear()
            self.state = ExState.quiescent  # This may not be necessary

        elif cmd == 'goto':
            if self.state != ExState.active:
                diag = self.diags[args[0]]
                self.remove_undos_with_diag(diag)
                node = args[1]
                # log('mach command goto',diag,node)
                if node == 0:
                    raise Exception('CANNOT GOTO 0')
                    return
                if not isinstance(diag.nodes[node], ExecutableBlock):
                    # log('not going to executable block')
                    return
                self.undo_list.append(['diag',args[0]])
                self.diag = diag
                self.node = node
                if 'no_signal' in kwargs and kwargs['no_signal']:
                    if self.node!=0:
                        self._state=ExState.stopped_on_node
                    else:
                        self._state=ExState.quiescent
                else:
                    if self.node != 0:
                        self.state = ExState.stopped_on_node,'GOTO SIGNAL'
                    else:
                        self.state = ExState.quiescent
        elif cmd == 'steppable':
            self.steppable_diags = args
        elif cmd == 'stop':
            self.cleanup_dialog(do_stop=True)
            self.stopped=True
        elif cmd == 'run':
            if self.state == ExState.stopped_on_node:
                self.activity = Activity.running  # here todo end debugging
                self._state = ExState.active
                self.stopped = False
                ui.root.after_idle(self.run)
        elif cmd == 'undoablerun':
            if self.state == ExState.stopped_on_node:
                self.activity = Activity.undoably_running
                self._state = ExState.active
                self.stopped = False
                ui.root.after_idle(self.undoablyrun)
        elif cmd == 'step':
            log('stepping with open editors', self.steppable_diags)
            if self.state == ExState.stopped_on_node:
                self.step_stack_level = len(self.stack)
                self.activity = Activity.stepping
                self._state = ExState.active
                self.stopped = False
                ui.root.after_idle(self.step)
        elif cmd == 'back':
            if self.state in (ExState.stopped_on_link,
                              ExState.stopped_on_node,
                              ExState.exited,
                              ExState.quiescent):
                self.step_stack_level = len(self.stack)
                self.activity = Activity.stepping_back
                self._state = ExState.active
                self.stopped = False
                ui.root.after_idle(self.step_back)
        elif cmd == 'kill':
            log('Execution state at kill is', repr(ExState(self.state)))
            self.stopped = True
            self._state = ExState.dying
            ui.root.after_idle(self.cleanup_dialog)
        elif cmd == 'edit':
            if self.state == ExState.active:
                self.stopped=True
            self.state = ExState.quiescent  # This may not be necessary
        elif cmd == 'back_to_breakpoint':
            if self.state != ExState.active:
                self.activity = Activity.stepping_back_to
                self._state = ExState.active
                ui.root.after_idle(self.step_back_to)
        elif cmd == 'set_breakpoint':
            self.break_point = self.diags[args[0]].nodes[args[1]]
        elif cmd == 'clear_breakpoint':
            self.break_point= None
        elif cmd == 'activate_flasher':
            if self.node==0:
                self.node = self.last_node
                new_state=ExState.stopped_on_link
            else:
                #print('ACTIVATE_FLASHER')
                new_state=ExState.stopped_on_node
            self.state=new_state
        else:
            raise Exception(f'Unknown run control command:{cmd}')

    def repstate(self):
        self.log(f'mach:{self.name} diag:{self.diag.name} node:{self.node} ')

    @property
    def undoable(self):
        if self.diag.undoable:
            return self.activity in (
                Activity.undoably_running,
                Activity.undoably_running_to,
                Activity.stepping)
        return False

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self,value):
        if isinstance(value,tuple):
            self._state=value[0]
        else:
        #if value!=self._state:
            self._state=value
        self.machine_state_changed.emit()

    def stop(self):
        self.stopped=True
        self.state=ExState.quiescent

    def stop_on_node(self):
        self.node=self.last_node
        self.state= ExState.stopped_on_node

    def stop_on_link(self):
        if self.last_node and isinstance(
            self.diag.nodes[self.last_node], LoopBlock):
            if self.diag.nodes[self.last_node].links[
                0] != 0:
                self.last_node = self.diag.nodes[
                    self.last_node].links[0]
            self.node = self.last_node
        self.state = ExState.stopped_on_link


    def handle_wait_exception(self,e:BubblWaitException,undoable=False,stepping=False):
        if e.type_name == 'WAIT':
            if undoable:
                self.pop_undo(self.last_node)
            if self.stopped:
                self.state = ExState.stopped_on_node,'HANDLING WAIT EXCEPTION STOPPED'
            else:
                def delayed_recall():
                    if stepping:
                        ui.root.after(1,self.step)
                    else:
                        ui.root.after(1,self.run_func)

                ui.root.after_idle(delayed_recall)
        elif e.type_name == 'EMPTYWAIT':
            if self.stopped:
                self.state=ExState.stopped_on_node,'EMPTYWAIT'
            else:
                ui.root.after_idle(self.handle_wait_exception,e,undoable)
        elif e.type_name == 'PAGE':
            if self.node:
                ui.root.after_idle(self.run_func)
            else:
                self.state=ExState.stopped_on_link
        elif e.type_name=='FILEMENU':
            pass #Just ensure we wait for callback to continue execution

    def run(self):
        self.run_func=self.run
        start_time=time.perf_counter_ns()
        #last_last=self.node
        #last=self.node
        while (time.perf_counter_ns()-start_time<200000
                and not self.stopped): #give it at least 0.2ms

            try:
                self.diag.nodes[self.node].exec()
            except BubblWaitException as e:
                self.handle_wait_exception(e)
                return
            except PythonBlockException as e:
                self.handle_python_exception(e)
                self.stopped=True
                return
            except PythonBlockSyntaxException as e:
                self.python_syntax_error(e.message,
                                         e.diag_name,
                                         e.line_no,
                                         e.col_no)
                self.stopped=True
                return
            except Exception as e:
                self.bug_exception(
                    f'Run-Crash:{self.diag.name} node:{self.node}',
                    e,
                    self.diag.nodes[self.node].code_text()
                )
                if self.state ==ExState.exited:
                    return
                self.stopped=True
        if self.stopped:
            if self.node:
                self.last_node=self.node
                self.state=ExState.stopped_on_node,'RUN'
            else:
                self.state=ExState.stopped_on_link
        else:
            ui.root.after_idle(self.run)

    def undoablyrun(self):
        self.run_func=self.undoablyrun
        start_time = time.perf_counter_ns()
        while (time.perf_counter_ns() - start_time < 200000):  # give it at least 0.2ms
            if self.stopped:
                self.stop_on_node()
                return
            diag=self.diag
            if diag.undoable:
                try:
                    node=self.node
                    instr=diag.nodes[node]
                    if instr is self.break_point:
                        self.stopped=True
                        self.state=ExState.stopped_on_node,'undoably run BREAKPOINT'
                        return
                    self.last_node = node
                    self.add_undo(node)
                    instr.exec_undoable()
                    #exec(instr.undoable_code, diag.variables, diag.variables)

                    if self.node:
                        continue
                        #ui.root.after_idle(self.undoablyrun)
                    else:
                        self.state=ExState.stopped_on_link
                        return
                except BubblWaitException as e:
                    self.handle_wait_exception(e, undoable=True)
                    return
                except PythonBlockException as e:
                    self.handle_python_exception(e)
                    self.stopped=True
                    return
                except PythonBlockSyntaxException as e:
                    self.python_syntax_error(e.message,
                                             e.diag_name,
                                             e.line_no,
                                             e.col_no)
                    self.stopped = True
                    return

                except Exception as e:
                    #print(f'Undoably Run-Crash:{diag.name} node:{self.node}:{e}')
                    self.bug_exception(
                 f'Undoably Run-Crash:{diag.name} node:{self.node}',
                          e,
                          diag.nodes[self.node].get_exec_code_text()
                    )
                    self.stop_on_node()
                    return
            else:
                node=self.node
                instr=diag.nodes[node]
                if instr is self.break_point:
                    self.state = ExState.stopped_on_node,'BREAKPOINT TO'
                    return
                self.last_node = node
                try:
                    instr.exec_undoably()
                    if self.node:
                        continue
                    else:
                        self.state=ExState.stopped_on_link
                        return
                except BubblWaitException as e:
                    self.handle_wait_exception(e)
                    return
                except PythonBlockException as e:
                    self.handle_python_exception(e)
                    self.stopped = True
                    return
                except PythonBlockSyntaxException as e:
                    self.python_syntax_error(e.message,
                                             e.diag_name,
                                             e.line_no,
                                             e.col_no)
                    self.stopped = True
                    return

                except Exception as e:
                    self.bug_exception(
                        f'Undoably Run-unundoable Crash:{self.diag.name} node:{self.node}',
                        e,
                        self.diag.nodes[self.node].get_exec_code_text()
                    )
                    self.stop_on_node()
                    return
        if self.stopped:
            self.stop_on_node()
            return
        if self.node:
            self.last_node=self.node
            ui.root.after_idle(self.undoablyrun)
        else:
            self.state=ExState.stopped_on_link

    def step(self,waiting=False):
        self.run_func=self.step
        if self.stopped:
            self.state=ExState.stopped_on_node,'STEP STOPPED'
            return

        if self.diag.undoable:
            if log_level==1:
                print('DEBUG node:',self.node)
                print(f'''---------------The code is ---------------------------------:
{self.diag.nodes[self.node].undoable_code_text()}
---------------That was the code ---------------------------''')
            self.last_node = self.node
            self.add_undo(self.last_node)
            try:
                self.diag.nodes[self.node].exec_undoable()
                if waiting:
                    return

                if self.node:
                    if (self.step_stack_level < len(self.stack)
                            and not self.diag.undoable
                            or self.diag.name not in self.steppable_diags):
                        ui.root.after_idle(self.step)
                    else:
                        self.state=ExState.stopped_on_node,'STEP STOPPED 2'
                else:
                    self.state=ExState.stopped_on_link
            except BubblWaitException as e:
                def stepped():
                    if self.node:
                        if (self.step_stack_level < len(self.stack)
                                and not self.diag.undoable
                                or self.diag.name not in self.steppable_diags):
                            ui.root.after_idle(self.step)
                        else:
                            self.state = ExState.stopped_on_node,'WaitException stepped'
                    else:
                        self.state = ExState.stopped_on_link
                self.run_func=stepped
                self.handle_wait_exception(e, undoable=True,stepping=True)
            except PythonBlockException as e:
                self.handle_python_exception(e)
                self.stopped = True
                return
            except PythonBlockSyntaxException as e:
                self.python_syntax_error(e.message,
                                         e.diag_name,
                                         e.line_no,
                                         e.col_no)
                self.stopped=True
                return

            except Exception as e:
                raise e
                self.bug_exception(
                    f'Step-Crash:{self.diag.name} node:{self.node}:{e}',
                    e,
                    self.diag.nodes[self.node].undoable_code_text()
                )
                self.stop_on_node()
                return
        else:
            try:
                self.diag.nodes[self.node].exec()
                #exec(self.diag.nodes[self.node].code,
                #     self.diag.variables, self.diag.variables)
                if self.node:
                    if (self.step_stack_level < len(self.stack)
                            and not self.diag.undoable
                            or self.diag.name not in self.steppable_diags):
                        ui.root.after_idle(self.step)
                    else:
                        self.state=ExState.stopped_on_node,'STEP STOPPED 3'
                else:
                    self.state=ExState.stopped_on_link
            except BubblWaitException as e:
                def stepped():
                    if self.node:
                        if (self.step_stack_level < len(self.stack)
                                and not self.diag.undoable
                                or self.diag.name not in self.steppable_diags):
                            ui.root.after_idle(self.step)
                        else:
                            self.state = ExState.stopped_on_node,'undoablyrun stepped'
                    else:
                        self.state = ExState.stopped_on_link
                self.run_func =stepped
                self.handle_wait_exception(e)
            except PythonBlockException as e:
                self.handle_python_exception(e)
                self.stopped = True
                return
            except PythonBlockSyntaxException as e:
                self.python_syntax_error(e.message,
                                         e.diag_name,
                                         e.line_no,
                                         e.col_no)
                self.stopped=True
                return

            except Exception as e:
                raise e
                self.bug_exception(
                    f'Step-Crash:{self.diag.name} node:{self.node}:{e}',
                    e,
                    self.diag.nodes[self.node].undoable_code_text()
                )
                self.stop_on_node()
                return

    def step_back(self):
        if self.okundo():
            if len(self.stack) > self.step_stack_level:
                if self.diag.name not in self.steppable_diags:
                    ui.root.after_idle(self.step_back)
                else:
                    self.stopped=True
                    self.state=ExState.stopped_on_node,'STEP BACK'
            else:
                self.stopped=True
                self.state=ExState.stopped_on_node,'STEP BACK 2'
        else:
            self.stop()

    def step_back_to(self):
        if self.okundo():
            try:
                if self.diag.nodes[self.node] is self.break_point:
                    self.state=ExState.stopped_on_node,'STEP BACK TO'
                    return
            except Exception as e:
                self.log(f'Undo Error:{e}')
                self.stop()
                return
            ui.root.after_idle(self.step_back_to)
        else:
            self.stop()
