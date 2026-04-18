"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"

if __name__=='__main__':
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import tkinter as tk
from tkinter import ttk
from .gutils import ensure_top_level_on_screen, icon

class Menu:
    menu_style=ttk.Style()
    menu_style.configure('popup.TMenu',borderwidth=5, relief='raised')

    '''
    defn is {'title':'title',
             'modal':True,
             'items':[str,..],
             'style':"",
             }
    calls back client_handler on selection or closing
    '''
    def __init__(self,parent,x,y,items,client_handler,title='',
                 modal=False,style='',options={}):
        #print('popupmenu options',options)
        self.parent=parent
        self.window=tk.Toplevel()
        #self.window.overrideredirect(1)
        self.window.protocol("WM_DELETE_WINDOW",
                             lambda:self.command(None))
        self.window.attributes('-topmost', True)
        #x+=parent.winfo_x()
        #y+=parent.winfo_y()
        self.window.geometry(f'+{x}+{y}')
        self.container=ttk.Frame(
            self.window,
            style=style,
            borderwidth=2,
            relief='raised',
            padding='2 2 2 2')
        self.frame=ttk.Frame(
            self.container,
            style=style,
            borderwidth=5,
            relief='ridge',
            padding='2 2 2 2')
        self.client_handler=client_handler
        self.modal=modal
        if title!='':
            ttk.Label(self.container,
                      text=title,
                      justify='center').grid(column=0,row=0,sticky='ew')
            #self.window.wm_title(title)
        for i,text in enumerate(items):
            ttk.Button(self.frame,
                       text=text,
                       command=lambda text=text:self.command(text),
                       **options).grid(column=0,row=i,sticky='ew')
        self.frame.grid(row=1,column=0,sticky='ew')
        ttk.Button(self.container,text='Cancel',
                   image=icon('exit'),
                   compound=tk.LEFT,
                   command=lambda:self.command(None)
                  ).grid(column=0,row=2,sticky='ew')
        self.container.grid()
        #ui.root.update_idletasks()
        ensure_top_level_on_screen(self.window)
        if modal:
            self.window.grab_set_global()

    def command(self,item):
        self.window.destroy()
        self.client_handler(item)

    def close(self):
        self.window.destroy()

    def help(self,*args):
        self.parent.event_generate("<<help>>", when="tail")

def main():
    #s = ttk.Style()
    #s.configure('Input.TFrame',borderwidth=5, relief='raised')
    def handle(mess):
        nonlocal root
        print(mess)
        if mess is None or mess=='exit':
            root.destroy()

    test_defn={'title':'the title',
             'modal':True,
             'items':['v1','v2','v3','checkV3prompt','True','exit'],
             'style':'',#Input.TFrame',
             'x':200,
             'y':200
             }
    root=tk.Tk()
    Menu(root,test_defn,handle)
    root.mainloop()

if __name__=='__main__':
    main()
