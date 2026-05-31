"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import os
import threading
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from glob import glob
import time

from .iset import Iset
from .logger import Logger
from .thumbnails import ThumbnailManager
from .tkfiledialog import TkFileDialog
from .uiserver import ui
from .utils import home, desktop, documents, downloads, log, print_
from .gutils import icon, BubblFont, ctrl, shift
from .popupchoice import PopupChoice
from .sizeableheader import SizeableHeader, ColumnSpec

default_history=[]

#["save", "title", "x", "y", "extension", "multi", "dir", "history"],

zoom_widths={0:{'icon':60,'font':10,'width':100},
             -1:{'icon':20,'font':6,'width':40},
             1:{'icon':100,'font':14,'width':150}
             }

class IconArea:
    def __init__(self, dialog, canvas, mouse_func, font):
        self.dialog = dialog
        self.mouse_func = mouse_func
        self.font = font

        self.canvas = canvas
        self.icon_cache=set()
        # log('multicolumn canvas made')
        # log('Got columns')
        self.selection=Iset()
        self.scheduled_redraw=None
        self.drawing=False
        self.interrupted=threading.Event()
        #todo here mouse_wheel

    def bind_mouse(self):
        self.canvas.bind('<1>', self.mouse_left)
        self.canvas.bind('<2>', self.mouse_right)
        self.canvas.bind('<3>', self.mouse_right)
        #self.canvas.bind('<B1-ButtonRelease>', self.mouse_left_up)
        #self.canvas.bind('<B2-ButtonRelease>', self.mouse_right_up)
        #self.canvas.bind('<B3-ButtonRelease>', self.mouse_right_up)
        self.canvas.bind('<MouseWheel>', self.mouse_wheel)  # Windows
        self.canvas.bind('<4>', self.up_one)
        self.canvas.bind('<5>', self.down_one)

    def icon_func(self,ind):
        icon_width=zoom_widths[self.dialog.zoom_level]['icon']
        try:
            if self.dialog.data[ind][0] == 0:
                return icon('folder',icon_size=icon_width)
            if self.dialog.data[ind][1] in self.selection:
                return icon('ok',icon_size=icon_width)
            return self.dialog.thumbnail_manager.get_thumbnail(
                self.dialog.path + self.dialog.data[ind][1],icon_width)
        except IndexError:
            return icon('blankpage')

    def change_offset(self,delta):
        self.dialog.apply_delta(delta * self.ncols())

    def up_one(self,*_args):
        self.change_offset(-1)

    def down_one(self,*_args):
        self.change_offset(1)

    def mouse_wheel(self,event):
        if event.delta >= 0:
            delta = event.delta // 120
        else:
            delta = -(-event.delta // 120)
        self.change_offset(delta)

    def mouse_left_up(self, event):
        r, c = self.rc_from_mouse(event)
        self.mouse_func('left', r, c)

    def mouse_left(self, event):
        tind=self.canvas.find_closest(event.x,event.y)
        tags=self.canvas.gettags(tind)
        try:
            ind=int(tags[1])
            self.dialog.file_select(self.dialog.data[ind][:2],event)
        except:
            print_('mouse_left_on_nothing')

    def mouse_move(self, event):
        r, c = self.rc_from_mouse(event)
        self.mouse_func('move', r, c)

    def mouse_right(self, event):
        log('mouse_right on columns')
        r, c = self.rc_from_mouse(event)
        self.mouse_func('right', r, c)

    def mouse_right_up(self, event):
        r, c = self.rc_from_mouse(event)
        self.mouse_func('rightup', r, c)

    def resize(self):
        self.redraw_all(self.dialog.offset)

    def ncols(self):
        widths = zoom_widths[self.dialog.zoom_level]
        width = widths['width']
        return self.canvas.winfo_width() // width

    def nrows(self):
        widths = zoom_widths[self.dialog.zoom_level]
        width = widths['width']
        return min(self.canvas.winfo_height()//width+1,
                   (len(self.dialog.data)-self.dialog.offset)+1)


    def redraw_all(self, offset):
        if self.scheduled_redraw is not None:
            self.dialog.window.after_cancel(self.scheduled_redraw)
        self.scheduled_redraw=self.dialog.window.after(50,
            lambda offset=offset:self.do_redraw_all(offset))

    def do_redraw_all(self,offset):
        self.scheduled_redraw=None
        self.dialog.slider['resolution'] = self.ncols()
        widths=zoom_widths[self.dialog.zoom_level]
        icon_size = widths['icon']
        font = BubblFont(f'sanserif,{widths["font"]}')
        width = widths['width']

        def get_disp_str(fn):
            if font.width(fn)<=width:
                return fn
            x=len(fn)
            while font.width(fn[:x])>width:
                x-=1
            res=fn[:x]+'\n'
            fn=fn[x:]
            x = len(fn)
            while font.width(fn[:x]) > width:
                x -= 1
            return res+fn[:x]

        # self.canvas['height']=self.font.line_space*(len(self.data)+1)
        # row nos
        n_cols=self.ncols()
        n_rows=self.nrows()
        self.canvas.delete('all')
        for r in range(n_rows):
            for c in range(n_cols):
                ind=c+r*n_cols+offset
                if ind>=len(self.dialog.data):
                    self.drawing=False
                    return
                if self.interrupted.is_set():
                    self.interrupted.clear()
                    return
                x=round(c*self.canvas.winfo_width()/n_cols)
                y=r*width
                icon=self.icon_func(ind)
                self.icon_cache.add(icon)

                if any(ind==self.dialog.get_index_of_selection(sel) for
                        sel in self.dialog.selection):
                    self.canvas.create_rectangle(
                        x,y,x+width,y+width,width=3,
                        outline='#F00',tags=('icon',f'{ind}'))

                self.canvas.create_image(x+2,y+2,image=icon,anchor='nw',
                                         tags=('icon',f'{ind}'))
                self.canvas.create_text(
                    x+2,
                    y+width-font.line_space*2,
                    text=get_disp_str(self.dialog.data[ind][1]),
                    font=font.font,
                    tags=('icon',f'{ind}'),
                anchor='nw')
        self.drawing=False

    def ensured_visible(self,index):
        offset=self.dialog.offset
        nc=self.ncols()
        if offset>index:
            self.dialog.apply_delta(index-offset)
            return True
        maxv=(self.nrows()-1)*nc+offset
        if maxv<index:
            self.dialog.apply_delta(nc*((index-maxv+nc-1)//nc))
            return True
        return False

class Column:
    def __init__(self, parent_canvas, column_spec, font):
        self.parent_canvas = parent_canvas
        self.column_spec = column_spec
        self.font = font
        self.icon_cache=set()

    def redraw(self, x1, x2, line_height, data, offset, nrows):
        # log('Redrawing column')

        col = self.column_spec.column_index
        if self.column_spec.range_right:
            x = x2 - 2
            anchor = 'ne'
        else:
            x = x1 + 2
            anchor = 'nw'
        width = x2 - x1 - 2
        disp_func = self.column_spec.display_func
        icon_func=self.column_spec.icon_func
        canvas = self.parent_canvas

        if icon_func is None:
            for i, row_no in enumerate(
                Iset(range(offset, min(offset + nrows,len(data))))):
                canvas.create_text(
                    x,i*line_height,
                    text=self.font.cropped(disp_func(data[row_no][col]),width),
                    anchor=anchor)
        else:
            #log('THERE IS A RECT FUNC')
            for i, row_no in enumerate(
                Iset(range(offset, min(offset + nrows,len(data))))):
                #log('doing row',i,row[col])
                y=i*line_height
                icon=icon_func(row_no)
                if icon is not None:
                    #print('ICON is',icon)
                    self.icon_cache.add(icon)
                    self.parent_canvas.create_image(x-2,y,image=icon,
                                                    anchor='nw')
                    text=self.font.cropped(disp_func(data[row_no][col]),width-line_height)
                    self.parent_canvas.create_rectangle(
                        x-2+line_height,y,
                        x+2+self.font.width(text)+line_height,y+line_height-1,
                        fill='#FFE',tag=f'r{i}')
                    self.parent_canvas.create_text(
                        x+line_height,y,
                        text=text,
                        anchor='nw',tag=f'r{i}')
                else:
                    text=self.font.cropped(disp_func(data[row_no][col]),width)
                    self.parent_canvas.create_text(
                        x,y,
                        text=text,
                        anchor='nw')

class Columns:
    def __init__(self, dialog, canvas, mouse_func, font,header_frame):
        self.dialog = dialog
        self.header_frame = header_frame
        self.mouse_func = mouse_func
        self.font = font

        self.canvas = canvas

        # log('multicolumn canvas made')
        self.line_height = font.line_space + 4
        self.columns = [Column(canvas, spec, font=self.font)
                        for spec in header_frame.column_specs]

        # log('Got columns')
        self.scheduled_redraw=None
        self.drawing= False
        self.data = None

    def bind_mouse(self):
        self.canvas.bind('<1>', self.mouse_left)
        self.canvas.bind('<2>', self.mouse_right)
        self.canvas.bind('<3>', self.mouse_right)
        self.canvas.bind('<B1-ButtonRelease>', self.mouse_left_up)
        self.canvas.bind('<B2-ButtonRelease>', self.mouse_right_up)
        self.canvas.bind('<B3-ButtonRelease>', self.mouse_right_up)
        self.canvas.bind('<Motion>', self.mouse_move)
        self.canvas.bind('<MouseWheel>', self.dialog.mouse_wheel)  # Windows
        self.canvas.bind('<4>',self.dialog.up_one)
        self.canvas.bind('<5>',self.dialog.down_one)

    def mouse_item(self,event):
        items=self.canvas.tag_find()

    def rc_from_mouse(self, event):
        x = round(self.canvas.canvasx(event.x))
        y = round(self.canvas.canvasy(event.y))
        r = self.dialog.offset + y // self.line_height
        for i in range(len(self.header_frame.column_specs)):
            if self.header_frame.x_coords[i] > x:
                c = i - 1
                break
        else:
            c = len(self.header_frame.column_specs) - 1
        return r, c

    def mouse_left(self, event):
        log('mouse_left on columns')
        r, c = self.rc_from_mouse(event)
        self.mouse_func('left', r, c,event)

    def mouse_left_up(self, event):
        r, c = self.rc_from_mouse(event)
        self.mouse_func('leftup', r, c,event)

    def mouse_move(self, event):
        r, c = self.rc_from_mouse(event)
        self.mouse_func('move', r, c,event)

    def mouse_right(self, event):
        log('mouse_right on columns')
        r, c = self.rc_from_mouse(event)
        self.mouse_func('right', r, c,event)

    def mouse_right_up(self, event):
        r, c = self.rc_from_mouse(event)
        self.mouse_func('rightup', r, c,event)

    def resize(self, newxs, newws):
        self.redraw_all(self.dialog.offset)

    def redraw_all(self, offset):
        if self.scheduled_redraw is not None:
            self.dialog.window.after_cancel(self.scheduled_redraw)
        self.scheduled_redraw = self.dialog.window.after(50,
            lambda offset=offset: self.do_redraw_all(offset))

    def do_redraw_all(self,offset):
        self.scheduled_redraw=None
        self.dialog.data_canvas.delete('all')
        for col in self.columns:
            col.icon_cache.clear()
        nrows = round(
            self.dialog.data_canvas.winfo_height() / self.line_height + 0.5)
        #print('REDRAW ALL 1')
        for i, (x1,
                x2,
                column) in enumerate(zip(self.header_frame.x_coords,
                                         self.header_frame.right_x_coords,
                                         self.columns)):
            column.redraw(x1, x2, self.line_height, self.dialog.data, offset,
                          nrows)

        length = nrows * self.line_height
        for x in self.header_frame.right_x_coords:
            self.dialog.data_canvas.create_line(x, 0,
                                                x, length,
                                                fill='#777')
        length = self.header_frame.right_x_coords[-1]
        for y in range(nrows):
            self.dialog.data_canvas.create_line(0, y * self.line_height,
                                                length, y * self.line_height,
                                                fill='#777')
        self.drawing=False

    def ensured_visible(self,index):
        offset=self.dialog.offset
        if offset>index:
            self.dialog.apply_delta(index-offset)
            return True
        nrows = round(
            self.dialog.data_canvas.winfo_height() / self.line_height + 0.5)
        maxv=nrows+offset-1
        if maxv<index:
            self.dialog.apply_delta(index-maxv+1)
            return True
        return False

class FileDialog:
    def __init__(self, default, callback,
                 saveas=False,
                 directory=False,
                 multiple=False,
                 history=default_history,
                 show_hidden=False,
                 icon_view=False,
                 filter='All files:*',
                 widths=[200, 50, 80, 150],
                 title=None,
                 thumbnail_manager=None):

        if isinstance(default,(list,tuple)):
            if default:
                default=[os.path.abspath(el) for el in default]
                if not directory and os.path.isdir(default[0]):
                    path=default[0]+os.sep
                else:
                    path=os.path.split(default[0])[0]+os.sep
                self.selection=[el[len(path):]
                                for el in default
                                    if el.startswith(path)
                                    and el!=path]
            else:
                path=os.getcwd()+os.sep()
                self.selection=[]
        else:
            self.selection=[]
            path=os.path.abspath(default)
            if os.path.isfile(path):
                #print('FD ITSA A FILE',path)
                self.selection.append(os.path.basename(path))
                #print('SEL',self.selection[0])
                path=path[:-len(self.selection[0])]
                #print('THE FILES PATH IS',path)
            else:
                #print('FD ITS NOT A FILE',path)
                if not os.path.isdir(path):
                    path=os.getcwd()

        if not path.endswith(os.sep):
            path+=os.sep
        self.path=None
        self.state='up'
        self.key_rc = 0,0
        self.data=[]
        self.callback=callback
        if thumbnail_manager is not None:
            self.thumbnail_manager=thumbnail_manager
        else:
            self.thumbnail_manager=ThumbnailManager()
        self.window=window=tk.Toplevel()
        if title is None:
            if saveas:
                title='Save as'
            else:
                if multiple:
                    title='File selection'
                else:
                    title='Open'
        window.title(title)
        window.protocol("WM_DELETE_WINDOW", self.window_closed)
        window.attributes('-topmost',True)
        window.columnconfigure(0,weight=0)
        window.columnconfigure(1,weight=1)
        window.rowconfigure(0,weight=1)
        window.rowconfigure(1,weight=0)
        self.directory=directory
        self.history=history
        self.multiple=multiple
        self.sorted_ascending=set()

        self.result=tk.StringVar()
        self.path_buttons=[]

        self.side_panel=tk.Frame(window,borderwidth=1,relief='solid')
        self.side_panel.grid(row=0,column=0,stick='nsew')

        tk.Button(self.side_panel,text='Home',relief='raised',borderwidth=2,
                  command=lambda:self.set_path(home())).grid(
                    row=0,column=0,sticky='n')
        tk.Button(self.side_panel,text='Desktop',relief='raised',borderwidth=2,
                  command=lambda:self.set_path(desktop())).grid(
                    row=1,column=0,sticky='n')
        tk.Button(self.side_panel,text='Documents',relief='raised',borderwidth=2,
                  command=lambda:self.set_path(documents())).grid(
                    row=2,column=0,sticky='n')
        tk.Button(self.side_panel,text='Downloads',relief='raised',borderwidth=2,
                  command=lambda:self.set_path(downloads())).grid(
                    row=3,column=0,sticky='n')

        tk.Button(self.side_panel,text='Recent files',relief='raised',borderwidth=2,
                  command=self.choose_history).grid(
                    row=4,column=0,sticky='n')

        self.icon_view=icon_view
        self.zoom_level=0
        self.icon_view_check=tk.BooleanVar(None,icon_view)
        self.icon_view_button=tk.Button(
            self.side_panel,text='Change View',relief='raised',borderwidth=2,
            command=lambda:self.set_view(not self.icon_view))
        self.icon_view_button.grid(row=5,column=0,sticky='n')

        #log('show_hidden',type(show_hidden),show_hidden)

        self.hidden_check=tk.BooleanVar(None,bool(show_hidden))
        tk.Checkbutton(self.side_panel,text='Show hidden',
                       variable=self.hidden_check,
                       command=self.load_folder).grid(
                    row=6,column=0,sticky='nw')

        self.create_folder_button=tk.Button(
            self.side_panel,text='Create Folder',image=icon('ins'),
            compound=tk.LEFT,relief='raised',borderwidth=2,
            command=self.create_folder)
        self.create_folder_button.grid(row=7,column=0,sticky='n')

        self.main_panel=tk.Frame(self.window,borderwidth=1,relief='solid',padx=3,pady=3)
        self.main_panel.grid(column=1,row=0,sticky='nsew')
        self.main_panel.columnconfigure(0,weight=1)
        #self.main_panel.columnconfigure(1,weight=0)

        self.main_panel.rowconfigure(0,weight=0)
        self.main_panel.rowconfigure(1,weight=0)
        self.main_panel.rowconfigure(2,weight=1)


        self.path_frame=tk.Frame(self.main_panel,borderwidth=1,relief='solid')
        self.path_frame.grid(row=0,column=0,sticky='new')

        #log('Path_frame initialised')

        headers=self.headers(widths)
        #log('got header specs')

        self.header_frame=SizeableHeader(self.main_panel,
                                         self.header_callback,
                                         headers)

        self.header_frame.grid(row=1,column=0,sticky='nw')

        #log('Header frame initialised')

        self.file_frame=tk.Frame(self.main_panel,height=400,borderwidth=1,relief='solid')
        #self.file_frame['height']=400
        self.file_frame.grid(column=0,row=2,sticky='nsew')
        self.file_frame.rowconfigure(0,weight=1)
        self.file_frame.columnconfigure(0,weight=1)
        self.file_frame.columnconfigure(1,weight=0)
        self.data_canvas = tk.Canvas(self.file_frame,
                                     borderwidth=1,
                                     height=398,
                                     relief='solid')
        self.data_canvas.grid(row=0, column=0, sticky='nsew')
        self.window.bind('<Up>', lambda event: self.up(False))
        self.window.bind('<Down>', lambda event: self.down(False))
        self.window.bind('<Left>', lambda event: self.up(False))
        self.window.bind('<Right>', lambda event: self.down(False))
        self.window.bind('<Next>', lambda event: self.pg_dn(False))
        self.window.bind('<Prior>', lambda event: self.pg_up(False))
        self.window.bind('<Home>', lambda event: self.home(False))
        self.window.bind('<End>', lambda event: self.end(False))

        self.window.bind('<Shift-Up>', lambda event: self.up(True))
        self.window.bind('<Shift-Down>', lambda event: self.down(True))
        self.window.bind('<Shift-Left>', lambda event: self.up(True))
        self.window.bind('<Shift-Right>', lambda event: self.down(True))
        self.window.bind('<Shift-Next>', lambda event: self.pg_dn(True))
        self.window.bind('<Shift-Prior>', lambda event: self.pg_up(True))
        self.window.bind('<Shift-Home>', lambda event: self.home(True))
        self.window.bind('<Shift-End>', lambda event: self.end(True))

        #self.window.bind('<Return>', lambda event: self.enter())
        self.window.bind('<Escape>', lambda _event: self.window_closed())

        self.icon_data_display=IconArea(self,self.data_canvas,self.icon_mouse,BubblFont())
        self.data_display=Columns(self,
                             self.data_canvas,
                             self.mouse,
                             BubblFont(),
                             self.header_frame
                          )

        self.data_display.bind_mouse()
        if isinstance(filter,str):
            if filter=='':
                filter="All files:*"
            filter=filter.split(',')
        self.filters=filter
        self.filter=tk.StringVar(None,self.filters[0])
        self.filter.trace('w',lambda *_args,self=self:self.load_folder())

        self.slider_frame = tk.Frame(self.file_frame)
        self._slider_pos = tk.IntVar(value=0) #todo here, bring default selected item into view
        self._slider_pos.trace_add('write', self.slider_moved)
        self.slider = tk.Scale(self.slider_frame,
                               variable=self._slider_pos,
                               from_=0,
                               to=1,
                               resolution=1,
                               showvalue=False,
                               length=360)
        self.slider_frame.grid(row=0, column=1, sticky='ns')

        #self.slider_frame.bind('<Configure>', self.resize_slider)

        self.slider.bind('<MouseWheel>', self.mouse_wheel)  # Windows
        self.slider.bind('<4>',self.up_one)
        self.slider.bind('<5>',self.down_one)
        self.slider.grid(row=0, column=0, sticky='n')

        #log('data display frame initialised')

        self.bottom_panel=tk.Frame(self.window)
        self.bottom_panel.grid(row=1,column=0,columnspan=2,sticky='ew')

        self.bottom_panel.columnconfigure(0,weight=0)
        self.bottom_panel.columnconfigure(1,weight=1)
        self.bottom_panel.rowconfigure(0,weight=0)
        self.bottom_panel.rowconfigure(1,weight=0)
        self.bottom_panel.rowconfigure(2,weight=0)


        #if isinstance(filter,str):
        #    if filter=='':
        #        filter="All files:*"
        #    filter=filter.split(',')
        #self.filters=filter
        #self.filter=tk.StringVar(None,self.filters[0])
        #self.filter.trace('w',lambda *_args,self=self:self.load_folder())


        tk.Label(self.bottom_panel,text='Files of type:').grid(
            column=0,row=0,sticky='e'
        )

        ttk.Combobox(self.bottom_panel,textvariable=self.filter,
            values=list(self.filters),postcommand=self.load_folder).grid(
            row=0,column=1,sticky='ew')

        tk.Label(self.bottom_panel,text='Filename:').grid(
            column=0,row=1,sticky='e')


        self.input=tk.Entry(self.bottom_panel,textvariable=self.result,borderwidth=1,relief='solid')
        self.input.grid(column=1,row=1,sticky='we')

        buttons=tk.Frame(self.bottom_panel,padx=3,pady=3)
        buttons.grid(row=2,column=0,columnspan=2,sticky='e')
        buttons.columnconfigure(0,weight=0)
        buttons.columnconfigure(1,weight=0)
        tk.Button(buttons,text='Cancel',relief='raised',borderwidth=2,
                  command=self.esc).grid(row=0,column=0,sticky='e')
        tk.Button(buttons,text='Ok',relief='raised',borderwidth=2,
                  command=self.ok).grid(row=0,column=1,sticky='e')
        self.window.bind('<Configure>',lambda _event:self.resize_slider(),add=True)
        self.data_canvas.bind('<Configure>',lambda _event:self.draw_all())

        self.path=path
        self.set_path(path)
        if not self.multiple:
            if self.selection:
                self.result.set(self.selection[0])
        self.draw_all()
        self.window.update()
        self.set_view(self.icon_view)
        self.history_chooser=None


    def get_index_of_selection(self,item):
        for i,d in enumerate(self.data):
            if d[1]==item:
                return i
        return 0

    def ensured_visible(self):
        #return True if data_display redrawn to make selection visible
        if self.selection:
            index=self.get_index_of_selection(self.selection[0])
            if self.icon_view:
                return self.icon_data_display.ensured_visible(index)
            else:
                return self.data_display.ensured_visible(index)
        else:
            return False



    @property
    def offset(self):
        return self._slider_pos.get()

    @offset.setter
    def offset(self,value):
        #print('setting offset to',value)
        self._slider_pos.set(value)
        self.draw_all()
        #print('set offset',value,time.perf_counter())

    def header_callback(self,action,*args):
        if action=='clicked':
            #log('calling sort')
            self.sort(args[0])
        elif action=='resizing':
            self.data_display.resize(args[0],args[1])
        elif action=='resized':
            self.data_display.resize(args[0],args[1])
            #self.data_display.redraw_all(self.data,[self.header_index(i) for i in range(len(self.headers()))])

    def headers(self,widths):
        def icon_func(row,self=self):
            try:
                if self.data[row][0]==0:
                    return icon('folder')
                if self.data[row][1] in self.selection:
                    return icon('ok')
                return self.thumbnail_manager.get_thumbnail(
                     self.path+self.data[row][1])
            except IndexError:
                print_('IndexError')
                return None

        result=[
            ColumnSpec('Name',1,widths[0],icon_func=icon_func),
            ColumnSpec('Ext',2,widths[1]),
            ColumnSpec('Size',3,widths[2],
                       display_func=lambda x:f'{x}',
                       range_right=True),
            ColumnSpec('Date',4,widths[3],
                       display_func=lambda t:time.ctime(int(t)))
            ]
        return result

    def draw_all(self,caller=None):
        # log('redraw all')
        #if caller is not None:
        #    print('draw_all called by',caller)
        #print('DRAWING ALL')
        if self.icon_view:
            self.icon_data_display.redraw_all(self.offset)
        else:
            self.data_display.redraw_all(self.offset)

    def update_hls(self,r,c,b):
        pass

    def icon_mouse(self,action,):
        #todo here
        pass

    def mouse(self, action, r, c,event):
        if r >= len(self.data):
            return
        if action == 'move':
            if self.state in ('down', 'oncell', 'onlineno'):
                self.update_hls(r, c,True)
                self.draw_all('mouse moved on cell etc')
            return
        if action in ('left','right'):
            self.file_select(self.data[r][:2],event)

    def up(self, shift):
        r, c = self.key_rc
        if r > 0:
            r -= 1
            self.update_hls(r, c, not shift)
            self.draw_all()

    def down(self, shift):
        r, c = self.key_rc
        if r < len(self.data):
            r += 1
            self.update_hls(r, c, not shift)
            self.draw_all()

    def pg_up(self, shift):
        r, c = self.key_rc
        if r > 0:
            r = max(0, r - (self.nrows() - 1))
            self.update_hls(r, c, not shift)
            self.draw_all()

    def pg_dn(self, shift):
        r, c = self.key_rc
        if r < len(self.data):
            r = min(len(self.data), r + self.nrows() - 1)
            self.update_hls(r, c, not shift)
            self.draw_all()

    def home(self, shift):
        r, c = self.key_rc
        if r == self.offset:
            if r == 0:
                return
            else:
                r = 0
        else:
            r = self.offset
        self.update_hls(r, c, not shift)
        self.draw_all()

    def end(self, shift):
        r, c = self.key_rc
        if r == len(self.data):
            return
        if r == self.offset + self.nrows() - 1:
            r = len(self.data)
        else:
            r = self.offset + self.nrows() - 1
        self.update_hls(r, c, not shift)
        self.draw_all()

    def mouse_wheel(self, event):  # todo here apply ctrl and shift modifiers
        if self.icon_view:
            self.icon_data_display.mouse_wheel(event)
            return
        delta=event.delta
        if delta>=0:
            delta//=120
        else:
            delta = -(-delta//120)
        self.apply_delta(delta)

    def up_one(self, *_args):
        if self.icon_view:
            self.icon_data_display.up_one()
            return
        self.apply_delta(-1)

    def down_one(self, event):
        if self.icon_view:
            self.icon_data_display.down_one()
            return
        self.apply_delta(1)

    def apply_delta(self,delta):
        new_offset = self.offset + delta
        self.offset = min(len(self.data) - 1, max(0, new_offset))


    def slider_moved(self, p1, p2, p3):
        self.draw_all()

    def resize_slider(self, *args):
        #log('resizing slider')
        self.slider['length'] = int(self.data_canvas.winfo_height())-12
        try:
            self.slider['to'] = len(self.data) - 1
        except Exception as e:
            log('Unable to set length of slider',e,level=Logger.INFO)

    def line_height(self):
        return self.font.line_space + 4

    def nrows(self):
        h = (int(self.main_frame.winfo_height())
             - int(self.header_frame.winfo_height()))

        return h // self.line_height() + 1

    def choose_history(self):
        #log('hsitory so far is',self.history)
        if len(self.history)>=1:
            def callback(index):
                if index is not None:
                    self.set_path(self.history[index])
            self.history_chooser=PopupChoice(self.side_panel,
                        None,
                        None,
                        self.history,
                        client_handler=callback,
                        title='Recent file selections')

    def set_view(self,icon_view):
        self.icon_view = icon_view
        if self.icon_view:
            self.header_frame.grid_forget()
            self.icon_data_display.bind_mouse()
            self.slider['resolution']=self.icon_data_display.ncols()
        else:
            self.header_frame.grid(row=1, column=0, sticky='nw')
            self.data_display.bind_mouse()
            self.slider['resolution'] = 1
        if not self.ensured_visible():
            self.draw_all()
        log('change view')

    def file_select(self,pars,event):
        #log('pars',pars)
        is_file,name=pars
        if is_file:
            self.result.set(name)
            if self.multiple:
                if shift(event):
                    if self.selection:
                        fr=self.get_index_of_selection(self.selection[-1])
                        to=self.get_index_of_selection(name)
                        if to<fr:
                            to,fr=fr,to
                        for ind in range(fr,to+1):
                            name=self.data[ind][1]
                            if name not in self.selection:
                                self.selection.append(name)
                    else:
                        self.selection.append(name)
                elif ctrl(event):
                    if name in self.selection:
                        self.selection.remove(name)
                    else:
                        self.selection.append(name)
                else:
                    self.selection.clear()
                    self.selection.append(name)
                self.draw_all()
            else:
                self.selection.clear()
                self.selection.append(name)
                self.draw_all()
        else:
            self.set_path(self.path+name+os.sep)

    def set_path(self,path):
        if path.startswith('//'):
            path=path[1:]
        log('setting path to',path)

        path=os.path.abspath(path)
        if os.path.isfile(path):
            #log('its a file')
            name=os.path.basename(path)
            path=path[:-len(name)]
        elif os.path.isdir(path):
            if not path.endswith(os.sep):
                path+=os.sep
            name=''
        else:
            path=os.getcwd()+os.sep
            name=''
        self.result.set(name)
        if self.path!=path:
            self.selection.clear()
        self.path=path
        self.load_folder(path)
        self.get_path_parts()

    def create_folder(self):
        win=None
        def callback(value):
            if value is not None:
                try:
                    os.makedirs(self.path+value)
                    self.set_path(self.path+value)
                except Exception as e:
                    log(f'failed to make directory:{e}',level=Logger.INFO)
            win.destroy()
        variable=tk.StringVar()
        win=tk.Toplevel(self.create_folder_button)
        tk.Label(win,text='New folder name:').grid(row=0,column=0)
        tk.Entry(win,textvariable=variable,width=30).grid(
            row=0,column=1,sticky='ew',padx=(0,10))
        buttons=tk.Frame(win)
        buttons.grid(row=1,column=0,columnspan=2)
        tk.Button(buttons,text='Cancel',
                  command=lambda:callback(None)).grid(row=0,column=0,sticky='e')
        tk.Button(buttons,text='Ok',
                  command=lambda:callback(variable.get())).grid(
                    row=0,column=1,sticky='e')

    def esc(self):
        self.window.destroy()
        self.thumbnail_manager.clear_cache()
        self.close_history()
        self.callback(None)

    def ok(self):
        self.window.destroy()
        self.thumbnail_manager.clear_cache()
        self.close_history()
        if self.multiple:
            result=[self.path+name for name in self.selection]
            self.callback(result)
        else:
            self.callback(self.path+self.result.get())

    def path_button(self,i):
        self.set_path(os.sep.join(b['text'] for b in self.path_buttons[:i+1])+os.sep)
        self.selection.clear()
        self.load_folder(self.path)
        #self.window.update_idletasks()

    def get_path_parts(self):
        #log('getting path parts')
        parts=Path(self.path).absolute().parts
        #log('parts got is',parts)
        for i,(p,b) in enumerate(zip(list(parts),list(self.path_buttons))):
            #log('ipb',i,p,b['text'])
            if p!=b['text']:
                #log('no match at p')
                for _di in range(i,len(self.path_buttons)):
                    self.path_buttons.pop().destroy()
                break
            else:
                b.configure(background='#FC8')

        for i in range(len(self.path_buttons),len(parts)):
            b=tk.Button(self.path_frame,
                        text=parts[i],
                        background='#FC8',
                        command=lambda i=i:self.path_button(i))
            b.grid(row=0,column=i)
            self.path_buttons.append(b)
        for i in range(len(parts),len(self.path_buttons)):
            self.path_buttons[i].configure(background='#CCC')
        #self.window.update_idletasks()

    def load_folder(self,folder=None,reset_offset=True):
        log('LOAD FOLDER')
        if reset_offset:
            self.offset=0
        if folder is None:
            folder=self.path
        #start=time.perf_counter()
        #log('loading folder',f'>{folder}<')
        hide_hidden=not self.hidden_check.get()
        dir_only=self.directory
        if not Path(folder).is_dir():
            #log('Folder does not exist')
            return
        #log(f'#1 {time.perf_counter()-start:.4f}')
        glob_strings=self.filter.get().split(':')
        if len(glob_strings)>1: #remove name
            glob_strings=glob_strings[1:]
        includes=set()
        for glob_string in glob_strings:
            if glob_string.startswith('@i'):    #ignore case
                glob_string=''.join(f'[{c.lower()}{c.upper()}]'
                                    if c.isalpha() else c for c in glob_string[2:])
            includes|=set(glob(folder+glob_string))
            #log('includes')
            def func(name):
                #log('globbed include func')
                return (folder+name) in includes
            include_func=lambda name:func(name)
        #log(f'#2 {time.perf_counter()-start:.4f}')

        data=[]
        for entry in os.scandir(folder):
            if hide_hidden and entry.name.startswith('.'): #todo add windows specific stuff here
                continue
            stat=entry.stat()

            try:
                t=stat.st_birthtime
            except:
                t=stat.st_ctime
            ext=entry.name.split('.')
            if len(ext)==1:
                ext=''
            else:
                ext='.'+ext[-1]
            if entry.is_file():
                if not dir_only:
                    if include_func(entry.name):
                        data.append([True,entry.name,ext,stat.st_size,t])
            else:
                try:
                    data.append([False,entry.name,'',len(os.listdir(entry.path)),t])
                except PermissionError:
                    pass

        #log(f'#3 {time.perf_counter()-start:.4f}')

        #Alphabetical order but starting with Caps before l/c
        data.sort(key=lambda x:[x[0],x[1][:1].lower()+x[1]])
        #log(f'#4 {time.perf_counter()-start:.4f}')
        self.data=data
        self.resize_slider()

        #self.data_display.set_data(data)
        #log(f'#5 {time.perf_counter()-start:.4f}')
        #print('LOADDDED folder')
        log('LOADED folder',f'>{folder}<')
        self.draw_all('load_folder')

    def sort(self,index_in):
        index=self.header_frame.column_specs[index_in].column_index
        log(f'sorting index from {index_in} to {index}',self.sorted_ascending)
        if index in self.sorted_ascending:
            #log(f'reverse sorting on column {index}')
            try:
                self.data.sort(key=lambda x:x[index][:1].lower()+x[index],reverse=True)
            except TypeError:
                self.data.sort(key=lambda x:x[index],reverse=True)

            self.data.sort(key=lambda x:x[0])
            self.sorted_ascending.remove(index)
        else:
            #log(f'sorting on column {index}')
            try:
                self.data.sort(key=lambda x:x[index][:1].lower()+x[index])
            except TypeError:
                self.data.sort(key=lambda x:x[index])
            self.data.sort(key=lambda x:x[index])
            self.data.sort(key=lambda x:x[0])
            self.sorted_ascending.add(index)
        self.draw_all('sort')

    def window_closed(self):
        self.window.destroy()
        self.thumbnail_manager.clear_cache()
        self.close_history()
        self.callback(None)

    def close(self,do_callback=False):
        self.window.destroy()
        self.close_history()
        if do_callback:
            self.callback(None)

    def close_history(self):
        if self.history_chooser is not None:
            self.history_chooser.close()
            self.history_chooser=None


def get_file_dialog(
                 default,
                 callback,
                 saveas=False,
                 directory=False,
                 multiple=False,
                 history=default_history,
                 show_hidden=False,
                 icon_view=False,
                 filter='All files:*',
                 widths=[200, 50, 80, 150],
                 use_tkinter=False,
                 title=None):

    log('Use Tkinter = ',use_tkinter)

    if use_tkinter:
        return TkFileDialog(
            default,
            callback,
            saveas,
            directory,
            multiple,
            filter=filter,
            title=title)
    return FileDialog(default,
            callback,
            saveas,
            directory,
            multiple,
            history,
            show_hidden,
            icon_view,
            filter,
            widths,
            title=title)