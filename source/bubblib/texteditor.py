"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import sys
import tkinter.ttk as ttk
import tkinter as tk

from bubblib.borrowedfromidlelib import UndoDelegator
from .basetexteditor import BaseTextItem
from .gutils import length_for_pixels, BubblFont
from .keyhandler import PythonEditorKeyHandler
from .uiserver import ui
from .utils import log


class TextEditorWidget:
    def __init__(self,parent_canvas,x,y,update_func,text='',
                 width=320,height=240,colour='#000',fill='#fff',
                 enabled=True,font=None):
        self.text_in=text
        self.parent_canvas=parent_canvas
        self.colour=colour
        self.update_func=update_func
        if font is None:
            font=BubblFont().font

        width=length_for_pixels(width,font)
        height=round(round(height+font.metrics('linespace')-1)//font.metrics('linespace'))

        #self.canvas=tk.Canvas(width=width,height=height)
        self.text = tk.Text(self.parent_canvas,width=width,height=height,
                            undo=True,background=fill,foreground=colour,
                            wrap='word',font=font,
                            state='normal' if enabled else 'disabled')
        self.uid=self.parent_canvas.create_window(x,y,window=self.text,anchor='nw')
        self.text.bind('<Tab>',lambda event:self.tab_key())
        if sys.version_info[1]>=12:
            self.text.bind('<ISO_Left_Tab>',lambda event:self.back_tab_key())
        self.text.bind('<Escape>',lambda event:self.esc())
        self.text.bind('<Key>',self.edit_separator)
        self.text.config()
        self.text.insert('1.0',text)
        self.text.edit_reset()

        self.undo = UndoDelegator()
        self.text.bind('<FocusIn>',self.focus_in)
        self.text.bind('<FocusOut>',self.focus_out)
        self.text.bind('<<Modified>>',self.modified)
        self.suppress_callback=False

    def tab_key(self):
        pos=self.text.index('insert')
        #print('type poss',type(pos))
        row,col=f'{pos}'.split('.')
        col=int(col)
        new_col=(col//4+1)*4
        spaces=' '*(new_col-col)
        self.text.edit_separator()
        self.text.insert(f'{row}.{col}',spaces,'after')
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

    def edit_separator(self,event):
        if bool(event.state &0x4):
            c=event.keysym
            #print('CTRL',c)
            if c in ('u','z'):
                #print('UNDO')
                return
        self.text.edit_separator()

    def esc(self):
        self.text.insert('1.0',self.text_in)

    def focus_in(self,_event):
        self.undo.undo_block_start()
        self.text_in=self.text.get('1.0','end-1c')

    def focus_out(self,_event):
        try:
            self.undo.undo_block_stop()
        except Exception as e:
            log('unable to close block for undoing in textEditorWidget',level=2)

    def ok(self):
        self.params[:]=self.text.get('1.0','end-1c').split('\n')

    def modified(self,_event):
        if self.suppress_callback:
            self.suppress_callback=False
            return
        self.text.edit_modified(False)
        self.update_func(self.text.get('1.0','end-1c'))
        return 'break'

    def change_text(self,text):
        self.suppress_callback=True
        self.text.replace('1.0','end-1c',text)


class TextEditor:
    def __init__(self,parent,x,y,update_func,text='',title='Text Editor',width=640,height=480):
        self.window = tk.Toplevel(parent, width=width, height=height)
        if title is not None:
            self.window.wm_title(title)
        self.window.wm_geometry(f'{width}x{height}+{x}+{y}')
        self.window.protocol("WM_DELETE_WINDOW", lambda:self.button_press('close'))
        self.text_in=text
        self.update_func=update_func
        self.window.title(title)
        self.window.option_add('*tearOff', False)
        self.window.columnconfigure(0,weight=1)
        self.window.rowconfigure(0,weight=1)
        #self.window.rowconfigure(1,weight=1)
        self.canvas = tk.Canvas(self.window, background='#FFF')
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.canvas.bind('<1>',self.mouse_left)
        self.canvas.bind('<B1-ButtonRelease>', self.mouse_up)
        self.canvas.bind('<Motion>',self.mouse_move)
        buttons=tk.Frame(self.window)
        buttons.rowconfigure(0,weight=1)
        def add_button(index,text):
            button=ttk.Button(buttons,text=text,command=lambda text=text:self.button_press(text))
            button.grid(column=index,row=0)
        for i,but in enumerate(['Cancel','Undo','Help','Ok']):
            add_button(i,but)
        buttons.grid(row=1,column=0)

        self.text_holder=BaseTextItem(text)
        self.keyhandler=PythonEditorKeyHandler(self,self.window)
        self.cursor_coords=0,0,0,0
        self.cursor_phase=0
        self.got_mouse=False
        self.refresh()
        self.closing=False
        self.update_cursor()

    def button_press(self,command):
        if command=='close':
            if self.text_in!=self.text_holder.plain_text:
                 if tk.messagebox.askyesnocancel(message=f'Save edits ?',
                                           title='Close editor',
                                           icon='question', parent=self.window):
                     self.update_func(self.text_holder.plain_text)
            self.close()
        elif command=='Cancel':
            self.update_func(None)
            self.close()
        elif command=='Help':
            log('Text editor help')
        elif command=='undo':
            self.text_holder.command('undo')
        elif command=='Ok':
            self.update_func(self.text_holder.html)
            self.close()

    def refresh(self):
        #return true if cursor changed
        #print('Text Presenter Refreshing')
        last=self.cursor_coords
        self.cursor_coords=self.text_holder.draw(1,1,self.canvas,'hmm')
        #print('Python editor Refreshing',self.cursor_coords)
        if last[0]!=self.cursor_coords[0] or last[1]!=self.cursor_coords[1]:
            self.cursor_phase=3

    #def text_cursor_off(self):
    #    self.canvas.delete('textcursor')

    def close(self):
        self.closing=True

    def update_cursor(self):
        #print('updating cursor',self.cursor_phase,self.cursor_coords)
        if self.closing:
            self.window.destroy()
            return
        self.cursor_phase+=1
        if self.cursor_phase>=7:
            #print('CURSOR COORDS before error',self.cursor_coords)
            self.canvas.create_line(*self.cursor_coords,fill='#000',width=2,tag='textcursor')
            self.cursor_phase=0
        elif self.cursor_phase==4:
            self.canvas.delete('textcursor')
        ui.root.after(100,self.update_cursor)

    def mouse_left(self,event):
        #print('livetextedit mouse down')
        x=self.canvas.canvasx(event.x)
        y=self.canvas.canvasy(event.y)
        self.text_holder.position_cursor(x,y,False)
        self.got_mouse=True
        self.refresh()

    def mouse_move(self,event):
        #print(f'Python Editor mouseMoveEvent')
        if self.got_mouse:
            x=self.canvas.canvasx(event.x)
            y=self.canvas.canvasy(event.y)
            self.text_holder.position_cursor(x,y,True)
            self.refresh()

    def mouse_up(self,event):
        self.got_mouse=False

"""

import sys, traceback
from traceback import TracebackException

def lumberjack():
    bright_side_of_life()

def bright_side_of_life():
    return tuple()[0]

try:
    lumberjack()
except IndexError as exc:
    t=TracebackException.from_exception(exc,capture_locals=True)
    print(dir(t))



import sys, traceback
import tokenize
from io import BytesIO

gl={}
src='''
    def this(that):
        print(that)
        print(that,again)
        return "you passed "+that
    this('MESS')
'''

bio=BytesIO(src.encode())
#t=tokenize.tokenize(bio.readline)
#for f in t:
#    print(repr(f))

try:
    cc=compile(src,'python-block','exec')
except SyntaxError as e:
    print(repr(e))
    print('line',e.lineno)
    print('col',e.offset)
    print('msg',e.msg)
    print(dir(e))
try:
    exec(cc,gl,gl)
except Exception as e:
    #print(sys.exc_info())
    #import traceback
    #print(''.join(traceback.format_exception(None, e, e.__traceback__)).split('\n')[-3:-1])
    err,ln=get_error_and_line(e)

    lines=src.split('\n')

    print(f'''
{err} in line {ln}:
>{lines[ln-1]}<
''')

#    except Exception as e:
#        print(repr(e))
#        print(dir(e))
        #print('line',e.lineno)
        #print('col',e.offset)
        #print('msg',e.msg)

try:
    exec(src,gl,gl)
except Exception as e:
    print('ln',e.__traceback__.tb_lineno)
    print('ex',e)

"""