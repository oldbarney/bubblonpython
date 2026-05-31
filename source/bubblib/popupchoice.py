"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from tkinter import ttk
import tkinter as tk

from bubblib.gutils import darker, BubblFont, icon, AutoScrollbar, \
    xywh_from_geom

class PopupChoice:
    menu_style=ttk.Style()  #todo here - subclass ttk.frame,use labels,etc.
    menu_style.configure('popup.TMenu',borderwidth=3, relief='raised')
    #def __init__(self,parent,x,y,items,ysize=grid_size,width=None,icons=None,colours=None,title=None,client_handler=None):

    def __init__(self,parent,x,y,items,colours=None,
                 highlight='#AAA',fill='#FFF',colour='#000',
                 default=None,client_handler=None,
                 title='',length=None,multi=False,modal=False,font=None):
        """
        :param parent: Window over which choices will be displayed
        :param x: Screen position
        :param y: Screen position
        :param items: List of objects to choose from who's __str__() method is used to present the choice
        :param fill: default background and border colour of non-selected items
        :param colour: colour of displayed text
        :param client_handler: function(item) where item is None, or integer or Iset for Cancel,Single selection or Multi selection
        :param title:
        :param length: Initial number of display lines
        :param multi: whether multiple selections allowed
        :param modal:
        :param font:
        """

        #print('mywidgets popup choice length',length)

        if x is None:
            x = parent.winfo_pointerx() # - ui.root.winfo_rootx()
        #elif parent is not None:
        #    x+=parent.winfo_x()

        if y is None:
            y = parent.winfo_pointery() # - ui.root.winfo_rooty()
        #elif parent is not None:
        #    y+=parent.winfo_y()

        if length is None:
            length=10

        self.window=tk.Toplevel(borderwidth=3,relief='raised')
        self.window.wm_title(title)
        #self.window.overrideredirect(1)
        self.window.protocol("WM_DELETE_WINDOW", lambda:self.esc())
        self.window.attributes('-topmost',True)
        self.window.columnconfigure(0,weight=1)
        self.window.columnconfigure(1,weight=0)
        self.window.rowconfigure(0,weight=1)
        self.window.rowconfigure(1,weight=1)

        #x+=parent.winfo_x()
        #y+=parent.winfo_y()
        self.fill=fill
        self.colour=colour
        if colours is None or len(colours)!=len(items):
            self.colours=[fill]*len(items)
            self.highlights=[highlight]*len(items)
        else:
            self.colours=colours
            self.highlights=[darker(colour) for colour in colours]
        self.multi=multi
        if multi:
            #print('multi default is',default)
            if default is None:
                self.result=set()
            else:
                try:
                    self.result=set(default)
                except:
                    self.result=set()
        else:
            self.result=None

        self.items=items
        self.font= BubblFont(font)
        self.item_height=self.font.line_space+5

        buttons=ttk.Frame(self.window,borderwidth=2)
        buttons.grid(column=0,row=1,columnspan=2,sticky='ews')#,columnspan=2)
        buttons.columnconfigure(0,weight=1)
        width=self.font.width('Cancel Ok Ok'+title)
        width=max([width]+[self.font.width(item) for item in items])
        height=(self.item_height)*(2+length)

        if multi:  #Here put these buttons in a frame
            esc=ttk.Button(buttons,image=icon('exit'),command=self.esc)
            esc.grid(column=0,row=0,sticky='w')
            ttk.Button(buttons,text='Ok',width=3,image=icon('ok'),compound=tk.LEFT,command=self.ok).grid(column=1,row=0,sticky='e')
        else:
            esc=ttk.Button(buttons,text='Cancel',image=icon('exit'),compound=tk.LEFT,command=self.esc)
            esc.grid(column=0,row=0,columnspan=2,sticky='ew')

        self.window.geometry(f'{width+40}x{height}+{x}+{y}')

        self.vsb = AutoScrollbar(self.window, orient=tk.VERTICAL)
        self.vsb.grid(row=0, column=1, sticky='ns')

        self.canvas=tk.Canvas(self.window,
                              #height=height-self.item_height,
                              yscrollcommand=self.vsb.set)
        self.canvas.grid(row=0, column=0,sticky='nsew')
        self.vsb.config(command=self.canvas.yview)

        self.window.grid_rowconfigure(0,weight=1)
        self.window.grid_rowconfigure(1,weight=0)
        self.window.grid_columnconfigure(0,weight=1)

        self.client_handler=client_handler
        self.modal=modal
        self.items=items


        #if self.multi:  #Here put these buttons in a frame
        #    ttk.Button(self.container,image=gutils.icons['exit'],compound=tk.LEFT,command=lambda:self.command(None)).grid(column=0,row=scroll_row+1)
        #    ttk.Button(self.container,text='Ok',image=gutils.icons['ok'],compound=tk.LEFT,command=lambda:self.command(None)).grid(column=1,row=scroll_row+1)
        #else:
        #    ttk.Button(self.container,text='Cancel',image=gutils.icons['exit'],compound=tk.LEFT,command=lambda:self.command(None)).grid(column=0,row=scroll_row+1,sticky='s')

        #self.canvas.create_window(0, 0, anchor='nw', window=self.frame)

        self.redraw_all(width+40)

        #self.window.update_idletasks()

        self.canvas.bind('<Configure>', lambda *args:self.redraw_all(None))
        #self.window.bind('<FocusOut>',lambda event:self.esc())
        self.canvas.bind('<Up>',lambda event:self.up())
        self.canvas.bind('<Down>',lambda event:self.down())
        self.canvas.bind('<Return>',lambda event:self.Ok())
        self.canvas.bind('<Escape>',lambda event:self.esc())
        self.canvas.bind('<End>',lambda event:self.end())
        self.canvas.bind('<Home>',lambda event:self.home())
        self.canvas.bind('<Next>',lambda event:self.pg_dn())
        self.canvas.bind('<Prior>',lambda event:self.pg_up())
        self.canvas.bind('<Escape>',lambda event:self.esc())
        self.canvas.bind('<4>',lambda event:self.up())
        self.canvas.bind('<5>',lambda event:self.down())

        if modal:
            self.window.grab_set_global()
        self.canvas.focus_set()

    def redraw_all(self,width=None):
        self.canvas.delete('row')
        if width==None:
            width= xywh_from_geom(self.window.geometry())[2]
        for i,(item,colour,highlight) in enumerate(zip(self.items,self.colours,self.highlights)):
            self.add_choice(str(item),i,colour,highlight,width)

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def add_choice(self, text,index,colour,highlight,width):
        canvas=self.canvas
        tag=f't_{index}'
        hltag=f'f_{index}'
        canvas.tag_bind(hltag,'<1>',lambda event,index=index:self.click(index,event.state&4==4),add=True)
        canvas.tag_bind(tag,'<1>',lambda event,index=index:self.click(index,event.state&4==4),add=True)
        tags='row',tag
        if self.multi and index in self.result:
            fill=highlight
        else:
            fill=colour
        y1=index*self.item_height
        y2=y1+self.item_height
        x1=0
        x2=width
        canvas.create_rectangle(x1,y1,x2,y2,fill=fill,outline='',tags=(hltag,)+tags)
        canvas.create_text(x1+2,y1+2, text=text,tags=tags,anchor='nw',font=self.font.font,fill=self.colour)

    def ok(self):
        self.close()
        self.client_handler(self.result)

    def step(self):
        return 1/len(self.items)

    def up(self):
        y=self.canvas.yview()[0]
        self.canvas.yview_moveto(y-self.step())
        #self.vsb.set(self.vsb.get()[0]-self.step(),self.vsb.get()[1]-self.step())
    def down(self):
        y=self.canvas.yview()[0]
        self.canvas.yview_moveto(y+self.step())
    def home(self):
        self.canvas.yview_moveto(0)
    def end(self):
        self.canvas.yview_moveto(1)
    def pg_dn(self):
        y=self.canvas.yview()[0]
        self.canvas.yview_moveto(y+self.step()*10)
    def pg_up(self):
        y=self.canvas.yview()[0]
        self.canvas.yview_moveto(y-self.step()*10)

    def esc(self):
        self.close()
        self.client_handler(None)

    def click(self,item,ctrl=False):
        if not self.multi:
            self.close()
            self.client_handler(item)
            return 'break'

        if ctrl:
            if self.multi:
                hltag=f'f_{item}'
                if item in self.result:
                    self.result.remove(item)
                    self.canvas.itemconfigure(hltag,fill=self.colours[item])
                else:
                    self.result.add(item)
                    self.canvas.itemconfigure(hltag,fill=self.highlights[item])
            return 'break'
        else:
            for i in self.result:
                hltag=f'f_{i}'
                self.canvas.itemconfigure(hltag,fill=self.colours[item])
            hltag=f'f_{item}'
            self.canvas.itemconfigure(hltag,fill=self.highlights[item])
            self.result=set((item,))
            return 'break'
    def close(self):
        self.window.destroy()

    def help(self,*args):
        #print('info',args)
        self.parent.event_generate("<<help>>", when="tail")
