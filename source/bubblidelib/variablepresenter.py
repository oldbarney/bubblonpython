"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import tkinter as tk

from bubblib.table import RawTable
from bubblib.utils import quoted
from .baseelements import BlockPresenter
from bubblib.bubbljson import toJSON, fromJSON
from bubblib.globaldefs import render_defaults
from bubblib.gutils import BubblFont, cropped_string
from bubblib.tableeditor import TableEditor
from bubblib.textcontainer import BlockOfText
from bubblib.texteditor import TextEditor


#from textedwidget import TextEditorWidget

class VariablePresenterInfo:
    def __init__(self, name,variables,dim):
        self.name=name
        self.variables=variables
        self.dim=dim
        self.display_text=BlockOfText('')
        self.cache={}
        self.live_update()

    def live_update(self):
        try:
            v=self.variables[self.name]
        except KeyError:
            self.display_text.plain_text= '--deleted--'
            return

        if isinstance(v,str):
            self.display_text.plain_text=v
        else:
            self.display_text.plain_text=toJSON(self.variables[self.name])

    def ndisplay_lines(self):
        return max(1,self.dim[1])

    def display_line(self,index):
        if index==0:
            if isinstance(self.variables,dict):
                prefix=''
            else:
                prefix='_db.'
            return prefix+self.name+ ' = '+self.display_text.lines[0]
        try:
            return self.cache[index]
        except:
            if index<self.dim[1] and index<len(self.display_text.lines):
                self.cache[index]=result=self.display_text.lines[index]
                return result
            return ''

class VariablePresenter(BlockPresenter):
    def __init__(self, diag_editor,node,is_global=False):
        BlockPresenter.__init__(self,diag_editor,node,live_data=True)
        if is_global:
            self.source=diag_editor.diag.mach.database
        else:
            self.source=diag_editor.diag.variables
        self.info=VariablePresenterInfo(node.params[0],self.source,node.dim)

    def refresh(self):
        self.info.live_update() #todo here cache result -use dict assignments to nudge cache
        super().refresh()

    def edit(self,x,y,on_top=False,line_no=None):
        if self.editor is None:
            try:
                text=self.source[self.params[0]]
            except:
                text=''
            if isinstance(text,str):
                text=quoted(text.replace('\n','<br />'))
            else:
                text=toJSON(text)
            self.editor=TextEditor(
                self.canvas,x,y,
                self.update_variable,
                text=text,
                title=f'JSON representation of {self.params[0]}',
                width=320,height=240)
            if on_top:
                self.editor.window.attributes('-topmost',True)
        else:
            self.editor.window.attributes('-topmost',True)


    def update_variable(self,text):
        #todo here make it undoable 'mach.add_undo(['varassign',self.params[0],value])?
        #probably should clear undolist or give the option
        self.editor=None
        if text is None:
            return
        vn=self.params[0]
        #vs=self.diag_editor.diag.variables
        try:
            value=fromJSON(text)
        except:
            value=text
        if isinstance(value,str):
            value=value.replace('<br />','\n')
        self.source[vn]=value
        self.diag_editor.redraw_live_data()
        self.refresh()

class FormulaPresenter(BlockPresenter):
    def __init__(self, diag_editor,node):
        BlockPresenter.__init__(self,diag_editor,node,live_data=True)

class TableviewPresenterInfo:
    def __init__(self, presenter):
        self.presenter=presenter

    def nlines(self):
        return 1
    def display_line(self,_index):
        return self.presenter.params[0]

class TableViewPresenter(BlockPresenter):
    font=BubblFont().font
    def __init__(self,diag_editor,node):
        BlockPresenter.__init__(self,diag_editor,node,live_data=True)
        self.info=self #TableviewPresenterInfo(self)
        self.cache={}

        table=self.table
        if isinstance(table,RawTable):
            while len(self.params[2])<len(table.field_names):
                self.params[2].append(50)

            self.refresh()
        #self.editor=TableEditor(self.editor_window.canvas)


    @property
    def table(self):
        try:
            return self.diag_editor.diag.mach.database[self.params[0]]
        except:
            return None

    def live_update(self):
        #print('live update of table viewer')
        self.refresh()

    def draw_line(self,row_no,y,fields):
        x=self.xpos()
        self.canvas.create_text(x,y,text=row_no,fill='#000',
                                anchor='nw',tags=self.tags,font=self.font.font)
        def rescaled(v):
            return round(v*render_defaults.grid/18)

        x+=rescaled(40)

        for i,f in enumerate(fields):
            fd=cropped_string(f'{f}',
                              self.params[2][i],
                              self.font.font,
                              render_defaults.grid)

            if self.table.field_types[i] in ('num','int','float'):
                self.canvas.create_text(x+rescaled(self.params[2][i]-2),y,text=fd,fill='#000',
                                        anchor='ne',tags=self.tags,font=self.font.font)
            else:
                self.canvas.create_text(x,y,text=fd,fill='#000',
                                    anchor='nw',tags=self.tags,font=self.font.font)
            x+=rescaled(self.params[2][i])

    def refresh(self):
        #print('IMAGE VIEW Refreshing')
        x=self.xpos()
        y=self.ypos()
        self.delete_from_canvas()
        self.canvas.create_rectangle(x,y,x+self.scaled_width(),
                                     y+self.scaled_height(),
                                     outline='#000',
                                     fill=self.defn['colour'],
                                     tags=self.tags+(f'o{self.node_no}',))
        self.canvas.create_line(x,y+2*render_defaults.grid,
                                x+self.scaled_width(),y+2*render_defaults.grid,
                                fill='#555',tags=self.tags)

        self.canvas.create_text(x,y,text=self.params[0],anchor='nw',tags=self.tags,font=self.font.font)
        if not isinstance(self.table,RawTable):
            return
        self.draw_line('',y+render_defaults.grid,self.table.field_names)
        #print('range',range(1,self.node.dim[1]-1))
        #print('TABLEVIEW offset',self.params[1])
        for i in range(self.node.dim[1]-2):
            row_no=i+self.params[1]
            r=self.table[row_no]
            #print('row',r)
            if r is not None:
                self.draw_line(f'{row_no: 4}',y+(i+2)*render_defaults.grid,r.get_list())

    def edit(self,x,y,on_top=False,line_no=None):
        if self.table is None:
            return

        def finished_editing(update,offset,col_widths,width,height):
            if update:
                self.params[1]=offset
                self.params[2]=col_widths
                self.node.init['size'][0]=round(width/render_defaults.grid,3)
                self.node.init['size'][1]=height
            self.editor=None
            #self.refresh()
            self.diag_editor.redraw_live_data()

        if self.editor is None:
            x=self.diag_editor.sx()+self.xpos()
            y=self.diag_editor.sy()+self.ypos()
            self.editor=TableEditor(self.diag_editor.canvas,
                                    self.table, #todo here make table edits run-time undoable?
                                    finished_editing,
                                    offset=self.params[1],
                                    length=self.node.dim[1]-2,
                                    col_widths=self.params[2])
            if on_top:
                self.editor.window.attributes('-topmost',True)
        else:
            self.editor.window.attributes('-topmost',True)

    def handle_edit_buttons(self,command):
        if command=='close':
            self.node.dim[1]=self.editor.nrows()+2 #here use edvm
            self.params[1]=self.editor.offset
            self.params[2]=self.editor.get_col_widths()
            self.node.dim[0]=(40+sum(self.params[2]))/render_defaults.grid
            self.window.destroy()

        self.refresh()