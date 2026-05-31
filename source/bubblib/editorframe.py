"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import tkinter as tk
import tkinter.ttk as ttk
from .gutils import small_icon

class EditorWindow:
    def __init__(self,parent_canvas,name,client_handler=None):
        self.canvas=parent_canvas
        #print('Editor window canvas is ',parent_canvas)
        #client_handler must process messages:'close'
        self.name=name
        self._uid=None
        #ttk.Frame.__init__(self,parent,borderwidth=6,relief='ridge')
        frame=ttk.Frame(parent_canvas,relief='raised',borderwidth=2)
        frame.columnconfigure(0,weight=1)
        frame.rowconfigure(0,weight=1)
        frame.rowconfigure(1,weight=1)
        titlebar=tk.Frame(frame)
        titlebar.grid(row=0,column=0,sticky='ew')
        titlebar.rowconfigure(0,weight=1)
        titlebar.columnconfigure(0,weight=1)
        titlebar.columnconfigure(1,weight=1)
        self.title=ttk.Label(titlebar,text=name)
        self.title.grid(row=0,column=0,sticky='w')
        button_frame=tk.Frame(titlebar)
        button_frame.grid(row=0,column=1,sticky='e')
        button_frame.rowconfigure(0,weight=1)
        button_frame.columnconfigure(0,weight=1)
        button_frame.columnconfigure(1,weight=1)
        button_frame.columnconfigure(2,weight=1)
        minimise_button=ttk.Button(
            button_frame,image=small_icon('minimise'),
            command=lambda name=name:client_handler('minimise',name),padding=0)
        minimise_button.grid(row=0,column=0)
        maximise_button=ttk.Button(
            button_frame,image=small_icon('ins'),
            command=lambda name=name:client_handler('maximise',name),padding=0)
        maximise_button.grid(row=0,column=1)
        close_button=ttk.Button(
            button_frame,image=small_icon('exit'),
            command=lambda name=name:client_handler('close',name),padding=0)
        close_button.grid(row=0,column=2)
        self.client_handler=client_handler
        self.frame=frame
        titlebar.bind('<1>', self.mouse_left_down)
        #button_frame.bind('<3>', self.mouse_right_down_event)
        titlebar.bind('<B1-ButtonRelease>', self.mouse_left_release)
        #button_frame.bind('<B2-ButtonRelease>', self.mouse_right_release_event)
        #button_frame.bind('<B3-ButtonRelease>', self.mouse_right_release_event)
        titlebar.bind('<Motion>', self.mouse_move)
        titlebar.bind('<Leave>', self.mouse_leave)
        self.titlebar=titlebar
        #button_frame.bind('<Enter>',self.mouse_enter)
        self.state=''
        self.got_mouse=False
        self.x_off=0
        self.y_off=0
        self.iconified_geom=None
        self._norm_geom= 0, 0, 0, 0
        self.minimised=False
        #button_frame.bind('<Double-Button-1>', self.double_mouse_press)

    @property
    def  uid(self):
        return self._uid
    @uid.setter
    def uid(self,value):
        self._uid=value

    @property
    def maximised(self):
        x,y,w,h=self.geometry()
        dw=abs(self.canvas.winfo_width()-w)
        dh=abs(self.canvas.winfo_height()-h)
        return x==0 and y==0 and dw<=4 and dh<=4

    def geometry_and_state(self):
        if self.minimised:
            result=list(self._norm_geom)
            result[3]=-result[3]    #flag minimised
            return tuple(result)
        if self.maximised:
            return self._norm_geom
        x,y=self.canvas.coords(self.uid)
        client=self.client_canvas()
        if client is None:
            w=h=0
        else:
            w=client.winfo_width()
            h=client.winfo_height()
        return (int(x),int(y),w,h)

    def geometry(self):
        if self.uid is None:
            return self._norm_geom
        try:
            x,y=self.canvas.coords(self.uid)
        except Exception as e:
            x=100
            y=100
        client=self.client_canvas()
        if client is None:
            w=h=0
        else:
            w=client.winfo_width()
            h=client.winfo_height()
        return (int(x),int(y),w,h)

    def mouse_enter(self,event):
        pass #print('ed mouse_enter')

    def client_canvas(self):
        for c in self.frame.winfo_children():
            if c.grid_info()['row']==1:
                return c
        return None

    def maximise(self):
        if self.maximised:
            x,y,w,h=self._norm_geom
            self.client_canvas().config(width=w, height=h)
            self.canvas.moveto(self.uid,x,y)
        else:
            self._norm_geom=self.geometry()
            cw=self.canvas.winfo_width()
            ch=self.canvas.winfo_height()
            self.client_canvas().config(width=cw, height=ch)
            self.canvas.moveto(self.uid,0,0)

    def minimise(self):
        if self.minimised:
            return
        self.minimised=True
        if not self.maximised:
            self._norm_geom=self.geometry()
        self.canvas.delete(self.uid)


    def unminimise(self,reposition=False):
        x,y,w,h=self._norm_geom
        #print('unminimised x is',x)
        self.client_canvas().config(width=w, height=h)
        if self.minimised:
            cid=self.canvas.create_window(x,y,window=self.frame,anchor='nw')
            self.uid=cid
            #print('new cid')
            self.minimised=False
            self.place_frame_on_canvas(x,y)
        elif reposition:
            self.place_frame_on_canvas(x,y)






    def mouse_left_down(self,event):
        #print('editor Frame mouse_left_down')
        if self.uid is None:
            #print('Attempt to handle mouse on minimised window')
            return
        self.got_mouse=True
        #coords=self.canvas.coords(self.uid)
        #print('editor Frame mouse_left_down coords',coords)
        self.x_off=event.x_root #-coords[0]
        self.y_off=event.y_root #-coords[1]
        #print(f'offsets {self.x_off} {self.y_off}')

    def mouse_left_release(self,event):
        #print('ed mouse_left_release')
        self.got_mouse=False

    def mouse_move(self,event):
        #print('mousemoveoneditorframe')
        if self.got_mouse:
            dx=event.x_root-self.x_off
            dy=event.y_root-self.y_off

            self.x_off=event.x_root
            self.y_off=event.y_root

            minx=-(self.frame.winfo_width()-128)
            miny=0
            maxx=self.canvas.winfo_width()-32
            maxy=self.canvas.winfo_height()-32
            coords=self.canvas.coords(self.uid)
            #print('canvas coords',coords)

            newx=coords[0]+dx
            newy=coords[1]+dy
            if newx>maxx:
                dx=0
            elif newx<minx:
                dx=0
            if newy>maxy:
                dy=0
            elif newy<miny:
                dy=0
            self.canvas.move(self.uid,dx,dy)

    def place_frame_on_canvas(self,x,y):
        minx=-(self.frame.winfo_width()-128)
        miny=0
        maxx=self.canvas.winfo_width()-32
        maxy=self.canvas.winfo_height()-32
        if x>maxx:
            x=maxx
        elif x<minx:
            x=minx
        if y>maxy:
            y=maxy
        elif y<miny:
            y=miny
        self.canvas.moveto(self.uid,x,y)

    def mouse_leave(self,event):
        pass #print('ed mouse_leave')


    def handle_close(self,name):
        if self.client_handler is not None:
            self.client_handler('close',name)


class Minimised(ttk.Frame):
    def __init__(self,parent,restore_handler):
        self.editors=''
        ttk.Frame.__init__(self,parent,borderwidth=0)
        self.handler=restore_handler
        self.update_state([])


    #@Slot(ExecutionState)
    def update_state(self,windows):
        #print('Minimised placing',windows)
        for b in self.winfo_children():
            b.destroy()
        for i,text in enumerate(windows):
            ttk.Button(self,text=text,command=lambda name=text:self.handler(name)).grid(row=0,column=i)
        if not windows:
            ttk.Label(self,text='').grid(row=0,column=0)