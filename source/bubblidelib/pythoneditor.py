"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import os
import sys
from fileinput import filename
from tkinter import messagebox

from bubblib.filedialog import get_file_dialog
from bubblib.gutils import BubblFont, AutoScrollbar
from bubblib.modaldialogs import AlertDialog
from bubblib.uiserver import ui
from bubblib.utils import log
from bubblidelib.dialog import popup_input

KEYWORD   = r"\b(?P<KEYWORD>False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b"
EXCEPTION = r"([^.'\"\\#]\b|^)(?P<EXCEPTION>ArithmeticError|AssertionError|AttributeError|BaseException|BlockingIOError|BrokenPipeError|BufferError|BytesWarning|ChildProcessError|ConnectionAbortedError|ConnectionError|ConnectionRefusedError|ConnectionResetError|DeprecationWarning|EOFError|Ellipsis|EnvironmentError|Exception|FileExistsError|FileNotFoundError|FloatingPointError|FutureWarning|GeneratorExit|IOError|ImportError|ImportWarning|IndentationError|IndexError|InterruptedError|IsADirectoryError|KeyError|KeyboardInterrupt|LookupError|MemoryError|ModuleNotFoundError|NameError|NotADirectoryError|NotImplemented|NotImplementedError|OSError|OverflowError|PendingDeprecationWarning|PermissionError|ProcessLookupError|RecursionError|ReferenceError|ResourceWarning|RuntimeError|RuntimeWarning|StopAsyncIteration|StopIteration|SyntaxError|SyntaxWarning|SystemError|SystemExit|TabError|TimeoutError|TypeError|UnboundLocalError|UnicodeDecodeError|UnicodeEncodeError|UnicodeError|UnicodeTranslateError|UnicodeWarning|UserWarning|ValueError|Warning|WindowsError|ZeroDivisionError)\b"
BUILTIN   = r"([^.'\"\\#]\b|^)(?P<BUILTIN>abs|all|any|ascii|bin|breakpoint|callable|chr|classmethod|compile|complex|copyright|credits|delattr|dir|divmod|enumerate|eval|exec|exit|filter|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|isinstance|issubclass|iter|len|license|locals|map|max|memoryview|min|next|oct|open|ord|pow|print|quit|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|sum|type|vars|zip)\b"
DOCSTRING = r"(?P<DOCSTRING>(?i:r|u|f|fr|rf|b|br|rb)?'''[^'\\]*((\\.|'(?!''))[^'\\]*)*(''')?|(?i:r|u|f|fr|rf|b|br|rb)?\"\"\"[^\"\\]*((\\.|\"(?!\"\"))[^\"\\]*)*(\"\"\")?)"
STRING    = r"(?P<STRING>(?i:r|u|f|fr|rf|b|br|rb)?'[^'\\\n]*(\\.[^'\\\n]*)*'?|(?i:r|u|f|fr|rf|b|br|rb)?\"[^\"\\\n]*(\\.[^\"\\\n]*)*\"?)"
TYPES     = r"\b(?P<TYPES>bool|bytearray|bytes|dict|float|int|list|str|tuple|object)\b"
NUMBER    = r"\b(?P<NUMBER>((0x|0b|0o|#)[\da-fA-F]+)|((\d*\.)?\d+))\b"
CLASSDEF  = r"(?<=\bclass)[ \t]+(?P<CLASSDEF>\w+)[ \t]*[:\(]" #recolor of DEFINITION for class definitions
DECORATOR = r"(^[ \t]*(?P<DECORATOR>@[\w\d\.]+))"
INSTANCE  = r"\b(?P<INSTANCE>super|self|cls)\b"
COMMENT   = r"(?P<COMMENT>#[^\n]*)"
SYNC      = r"(?P<SYNC>\n)"

PROG   = rf"{KEYWORD}|{BUILTIN}|{EXCEPTION}|{TYPES}|{COMMENT}|{DOCSTRING}|{STRING}|{SYNC}|{INSTANCE}|{DECORATOR}|{NUMBER}|{CLASSDEF}"
#original - r"\s+(\w+)"
IDPROG = r"(?<!class)\s+(\w+)"

FONTBOLD=BubblFont('TkFixedFont,10,b').font
FONTITAL=BubblFont('TkFixedFont,10,i').font
FONTNORM=BubblFont('TkFixedFont,10').font

TAGDEFS   = {
'COMMENT'    : {'foreground': '#08F' , 'background': None},
'TYPES'      : {'foreground': '#779'    , 'background': None},
'NUMBER'     : {'foreground': '#BB5'  , 'background': None},
'BUILTIN'    : {'foreground': '#BBB' , 'background': None},
'STRING'     : {'foreground': '#950' , 'background': None},
'DOCSTRING'  : {'foreground': '#999'    , 'background': None},
'EXCEPTION'  : {'foreground': '#779'   , 'background': None, 'font':FONTBOLD},
'DEFINITION' : {'foreground':'#006', 'background': None, 'font':FONTBOLD},
'DECORATOR'  : {'foreground':'#880'     , 'background': None, 'font':FONTITAL},
'INSTANCE'   : {'foreground': '#555'    , 'background': None, 'font':FONTITAL},
'KEYWORD'    : {'foreground': '#33F',   'background': None, 'font':FONTBOLD},
'CLASSDEF'   : {'foreground': '#F0F'    , 'background': None, 'font':FONTBOLD},
}

'''
#what literally happens to this data when it is applied
for tag, cfg in self.tagdefs.items():
    self.tag_configure(tag, **cfg)
'''

import tkinter as tk

#import idlelib.colorizer as ic
#import re

#cdg = ic.ColorDelegator()
#cdg.idprog = re.compile(r'\s+(\w+)', re.S)

#cdg.tagdefs['MYGROUP'] = {'foreground': '#7F7F7F', 'background': '#FFFFFF'}

# These five lines are optional. If omitted, default colours are used.
#cdg.tagdefs['COMMENT'] = {'foreground': '#FF0000', 'background': '#FFFFFF'}
#cdg.tagdefs['KEYWORD'] = {'foreground': '#007F00', 'background': '#FFFFFF'}
#cdg.tagdefs['BUILTIN'] = {'foreground': '#7F7F00', 'background': '#FFFFFF'}
#cdg.tagdefs['STRING'] = {'foreground': '#7F3F00', 'background': '#FFFFFF'}
#cdg.tagdefs['DEFINITION'] = {'foreground': '#007F7F', 'background': '#FFFFFF'}
#from idlelib.colorizer import ColorDelegator, color_config
#from idlelib.percolator import Percolator

from bubblib.borrowedfromidlelib import ColorDelegator, color_config,\
    Percolator,UndoDelegator

def get_finds(target,key,cased):
    if not cased:
        target=target.lower()
        key=key.lower()
    result=[]
    p=target.find(key)
    while p!=-1:
        result.append(p)
        p=target.find(key,p+1)
    return result

class PythonEditor:
    def __init__(self,parent,exit_func,
                 params=None,
                 filename=None,
                 read_only=False,
                 index='1.0'):
        self.exit_func=exit_func
        self.params=params
        self.filename=filename
        self.read_only=read_only
        self.window = tk.Toplevel(parent)
        if filename is None:
            title='Pure Python block source-code'
        else:
            title=f'File:{filename}'
        if read_only:
            title='(R/O) '+title
        self.window.title(title)
        x=ui.mx()
        y=ui.my()

        self.window.geometry(f'{640}x{480}+{x}+{y}')
        self.text = tk.Text(self.window,undo=True,background='#FFF',wrap='none')
        self.text.bind('<Tab>',lambda event:self.tab_key())
        if sys.version_info[1]>=12:
            self.text.bind('<ISO_Left_Tab>',lambda event:self.back_tab_key())
        self.text.bind('<Escape>',lambda event:self.esc())
        self.text.bind('<Key>',self.edit_separator)
        self.text.bind('<Control-s>',self.update)
        self.text.bind('<2>',self.mouse_right)
        self.text.bind('<3>', self.mouse_right)

        self.text.config()
        self.window.protocol("WM_DELETE_WINDOW",self.close_window)

        if filename is not None:
            try:
                with open(filename,'r') as f:
                    text=f.read()
            except:
                text=''
        else:
            text='\n'.join(params)

        self.text.insert('1.0',text)
        self.text.edit_reset()
        self.text.mark_set('insert',index)
        #self.text.bind('<Control-z>',lambda event:self.undo())

        self.text.grid(row=0,column=0,sticky='nsew')
        self.vscr=AutoScrollbar(self.window,orient=tk.VERTICAL)
        self.vscr.grid(row=0,column=1,sticky='ns')
        self.vscr.config(command=self.text.yview)
        self.text.configure(yscrollcommand=self.vscr.set)
        button_frame=tk.Frame(self.window)
        button_frame.grid(row=1,column=0,sticky='esw')
        for c in range(9):
            button_frame.columnconfigure(c,weight=1 if c==7 else 0)
        #button_frame.columnconfigure(2,weight=1)
        button_frame.rowconfigure(0,weight=0)
        tk.Button(button_frame,text='Cancel',command=self.esc).grid(
            row=0,column=0,sticky='w')
        tk.Button(button_frame,text='Test (compile)',
                  command=self.compile).grid(
                    row=0,column=1,sticky='w')
        self.find_label=tk.Label(button_frame,text='Find:',justify='left')
        self.find_label.grid(row=0,column=2,sticky='w')
        tk.Button(button_frame,text='Find',command=self.find).grid(
            row=0,column=3,sticky='w')
        self.next=tk.Button(button_frame,text='v',command=self.find_next)
        self.next.grid(row=0,column=4,sticky='w')
        self.prev=tk.Button(button_frame,text='^',command=self.find_prev)
        self.prev.grid(row=0,column=5,sticky='w')
        self.case=tk.Button(button_frame,text='Cc',foreground='#000',
                            command=self.find_case)
        self.case.grid(row=0,column=6,sticky='w')
        row,col=index.split('.')
        self.label=tk.Label(button_frame,text=f'Line: {row}, Column: {col}')
        tk.Label(button_frame,text='').grid(row=0,column=7,sticky='ew')  #spacer
        self.label.grid(row=0,column=8,sticky='e')
        tk.Button(button_frame,text='Ok',command=self.ok).grid(
            row=0,column=9,sticky='e')
        self.window.rowconfigure(0,weight=1)
        self.window.rowconfigure(1,weight=0)
        self.window.columnconfigure(0,weight=1)
        self.window.columnconfigure(1, weight=0)

        self.perc = perc = Percolator(self.text)
        self.undo = undo = UndoDelegator()
        perc.insertfilter(undo)
        self.color = None
        self.code_context = None
        self.ResetColorizer()
        self.text.bind('<1>',self.update_row_and_col,add=True)
        self.text.bind('<B1-ButtonRelease>',self.update_row_and_col,add=True)
        self.text.bind('<MouseWheel>',self.update_row_and_col,add=True)
        self.text.bind('<Key>',self.update_row_and_col,add=True)
        self.text.bind('<Control-f>',self.find)
        self.search_ind='1.0'
        self.text.see(index)
        self.text.focus_set()
        #todo add search history, ^ v Cc W find controls


    def set_finds(self,locs):
        row_offs=[0]
        lines=self.text.get('1.0','end-1c').split('\n')
        for line in lines:
            row_offs.append(row_offs[-1]+len(line)+1)
        self.finds=[]
        for loc in locs:
            for i,off in enumerate(row_offs,-1):
                if loc<off:
                    self.finds.append((i,loc-row_offs[i-1]))
                    break
            else:
                self.finds.append((i+1,loc-row_offs[i]))

    def find_next(self,backwards=False):
        #pos=self.text.index('insert')
        #row,col=f'{pos}'.split('.')
        #row=int(row)
        #col=int(col)
        #self.text.see()
        #for i,find in enumerate(self.finds):
        #    if find[0]>=row:
        #        self.text.index()

        key=self.find_label['text'][5:]
        #print('find_next',key)

        if not key:
            log('not searching')
            return

        if backwards:
            ind=self.text.search(key,self.search_ind,'1.0',exact=True,
                                 backwards=True,
                                 nocase=not self.fcase)
        else:
            ind=self.text.search(key,self.search_ind,'end-1c',exact=True,
                                 forwards=True,
                                 nocase=not self.fcase)
        #print('ind found',ind,type(ind))
        if not ind:
            if backwards:
                ind=self.text.search(key,'end-1c','1.0',
                                     backwards=True,
                                     nocase=not self.fcase)
            else:
                ind=self.text.search(key,'1.0','end-1c',
                                     forwards=True,
                                     nocase=not self.fcase)
            if not ind:
                self.next['state']='disabled'
                self.prev['state']='disabled'
                return

        row,col=ind.split('.')
        if backwards:
            if col==0:
                row=int(row)-1
                col=255
                if row==0:
                    self.search_ind='end-1c'
                else:
                    self.search_ind=f'{row}.255'
            else:
                self.search_ind=f'{row}.{int(col)-1}'
        else:
            self.search_ind=f'{row}.{int(col)+1}'
        self.text.tag_configure('FOUND',background='#FFF')
        self.text.tag_delete('FOUND')
        self.text.tag_add('FOUND',ind,f'{row}.{int(col)+len(key)}')
        self.text.tag_configure('FOUND',background='#A8A')
        self.update_row_and_col(None,ind)

        self.text.see(ind)

        #print(f'found >{ind}<')
        self.next['state']='normal'
        self.prev['state']='normal'

        #lines=self.text.get('1.0','end-1c').split('\n')

        #if self.locs:

        #print('next')

    def find_prev(self):
        self.find_next(backwards=True)

    def find_case(self):
        if self.fcase:
            self.case['foreground']='#000'
            self.case['activeforeground']='#000'

        else:
            self.case['foreground']='#B00'
            self.case['activeforeground']='#B00'

        #self.window.update_idletasks()

    @property
    def fcase(self):
        return self.case['foreground']!='#000'

    def find(self,*args):
        def callback(text):
            log('find callback',text)
            if text is None:
                return
            self.find_label['text']=f'Find:{text}'

            #locs=get_finds(self.text.get('1.0','end-1c'),
            #               text,
            #               self.fcase,
            #               self.fwhole)
            #if locs==[]:
            #    self.next['state']='disabled'
            #    self.prev['state']='disabled'
            #    return
            #self.next['state']='normal'
            #self.prev['state']='normal'
            #self.set_finds(locs)
            self.search_ind=self.text.index('insert')

            #self.text.tag_configure('FIND',background='#FFF')
            #self.text.tag_delete('FIND')

            self.find_next()

            #self.find_label['text']=f'{locs} match{"es" if len(locs)>1 else ""}'


        popup_input('Search Python source',ui.mx(),ui.my(),'Text',callback,
                    default=self.find_label['text'][5:])

    def update_row_and_col(self,_event,pos=None):
        if pos is None:
            pos=self.text.index('insert')
        row,col=f'{pos}'.split('.')
        col=int(col)
        self.label.config(text=f'Line: {row}  Column: {col}')

    def close(self):
        self.close_window()

    def close_window(self):
        if self.read_only:
            self.esc()
        else:
            self.ok()

    def _add_colorizer(self):
        if self.color:
            return
        self.color = ColorDelegator()
        self.perc.insertfilter(filter=self.color)

    def _rm_colorizer(self):
        if not self.color:
            return
        self.color.removecolors()
        self.perc.removefilter(self.color)
        self.color = None

    def ResetColorizer(self):
        self._rm_colorizer()
        self._add_colorizer()
        color_config(self.text)

    def tab_key(self):
        pos=self.text.index('insert')
        #print('type poss',type(pos))
        row,col=f'{pos}'.split('.')
        col=int(col)
        new_col=(col//4+1)*4
        spaces=' '*(new_col-col)
        self.text.edit_separator()
        self.text.insert(f'{row}.{col}',spaces,'after')

        #print('TAB','pos=',pos)
        return 'break'

    def back_tab_key(self):
        pos=self.text.index('insert')
        row,col=f'{pos}'.split('.')
        col=int(col)
        if col==0:
            return 'break'
        line=self.text.get(f'{row}.0',f'{row}.{col}')
        to=((col-1)//4)*4
        #print('to',to,'col',col,f'>{line[to:col]}<')
        self.text.edit_separator()
        if all(c==' ' for c in line[to:col]):
            self.text.replace(f'{row}.{to}',f'{row}.{col}','')
        else:
            self.text.replace(f'{row}.{col-1}',f'{row}.{col}','')
        return 'break'

        #def undo(self):
        #    self.text.edit_undo()

    def edit_separator(self,event):
        if bool(event.state &0x4):
            c=event.keysym
            #print('CTRL',c)
            if c in ('u','z'):
                #print('UNDO')
                return
        self.text.edit_separator()

    def esc(self):
        if self.read_only or tk.messagebox.askyesnocancel(
                         message=f'''Do you want to discard edits?''',
                        title='Exit editor without saving',
                        icon='question', parent=self.text):
            self.exit_func(False)
            self.window.destroy()

    def mouse_right(self,_event):
        use_tk=sys.platform.startswith('win')
        def callback(filename):
            if filename==self.filename or filename is None:
                return
            if not use_tk and os.path.isfile(filename):
                if not tk.messagebox.askyesnocancel(
                   message=f'''{filename} already exists.
Do you want to overwrite it?''',
                        title='File exists',
                        icon='question', parent=self.text):
                    return

            self.filename=filename
            self.read_only=False
            self.update()
        if self.filename is not None:
            default=self.filename
        else:
            default=''

        get_file_dialog(default=default,
                        callback=callback,
                        saveas=True,
                        title='Save As',
                        filter='Python:*.py',
                        use_tkinter=use_tk
                       )

    def update(self,_event=None):
        if not self.read_only:
            text=self.text.get('1.0','end-1c')
            if self.filename is not None:
                if os.path.isfile(self.filename):
                    os.rename(self.filename,self.filename+'.bak')
                with open(self.filename,'w') as f:
                    f.write(text)
            else:
                self.params[:] = text.split('\n')
            self.exit_func(True)
        else:
            messagebox.showerror('Whoops!','File is read-only')

    def ok(self):
        if self.read_only:
            self.exit_func(False)
        else:
            self.update()
        self.window.destroy()

    def compile(self):
        code=self.text.get('1.0','end-1c')
        x=ui.mx()
        y=ui.my()

        #print('Compiling')
        try:
            compile(code,'python-block','exec')
            #print('success')
            AlertDialog(lambda:None,x,y,'Success!',[]) #[['title','Compilation test']])
        except SyntaxError as e:
            log('Python Editor Compile fail',e)
            AlertDialog(lambda:None,x,y,
              f'{e.msg}\nline:{e.lineno}\ncolumn:{e.offset}',
                [])#[['title','Compilation test']])
        #ack.wait()
        #self.dialog=None


testpars=[]
def exit_func(update):
    print(testpars)


def main():
    editor = PythonEditor(testpars,exit_func)
    editor.text.focus_set()
    ui.root.mainloop()

if __name__=='__main__':
    main()