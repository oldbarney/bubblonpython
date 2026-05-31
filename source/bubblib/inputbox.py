"""
Create and show a multi-field input box.
If modal, put in a toplevel window
otherwise return a frame
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import sys
from pprint import pprint

from bubblib.fontchooser import askfont, get_font
from bubblib.utils import print_

is_windows=sys.platform.lower().startswith('win')
import tkinter.ttk as ttk
import tkinter as tk
from tkinter import colorchooser

#from setuptools.windows_support import windows_only

from bubblib.filedialog import FileDialog, get_file_dialog
from bubblib.mywidgets import PopupMenu
from .gutils import icon
from .uiserver import ui



bg_col='#DDD'
def button(parent,client,text,index,row,col,icon_name=None,command=None,prefix='',state='normal',colspan=1):
    if icon_name is None:
        if command is None:
            command=prefix+text
        if state=='normal':
            result=tk.Button(parent,background=bg_col,text=text,state=state,command=lambda :client.button(command,index))
        else:
            result=tk.Button(parent,background=bg_col,text=text,state='disabled',command=lambda : client.button('dis',0))  #todo here make disable work
        #if state!='normal':
        #     result.state(['disabled'])
        result.grid(column=col,row=row,columnspan=colspan)
        #if state!='normal':
        #     result.state(['disabled'])

    else:
        if text=='':
            if command is None:
                command=prefix+icon_name
            else:
                command=prefix+command
            if state=='normal':
                result=tk.Button(parent,background=bg_col,height=20,image=icon(icon_name),compound=tk.LEFT,width=0,command=lambda :client.button(command,index))
            else:
                result=tk.Button(parent,background=bg_col,height=20,image=icon(icon_name),compound=tk.LEFT,width=0,command=lambda :client.button('dis',index))
            result.grid(ipadx=0,ipady=0,column=col,row=row,padx=0,pady=0)
        else:
            if command is None:
                command=prefix+text
            else:
                command=prefix+command
            result=tk.Button(parent,background=bg_col,image=icon(icon_name),text=text,compound=tk.LEFT,command=lambda :client.button(command,index))
            result.grid(column=col,row=row,columnspan=colspan,sticky='w')
    return result


class AuxInput:
    def __init__(self,
        parent,
        items,
        default,
        callback,
        resources=None,
        tk_file=False,
        table_var=None):
        if resources is None:
            resources={'table':[],
                     'fieldname':[],
                     'variable':[],
                     'global':[]}
        self.callback=callback
        self.resources=dict(resources)
        self.tk_file=tk_file
        self.default=default
        self.table_var=table_var
        x = ui.mx()
        y = ui.my()
        self.parent=parent
        PopupMenu(parent,x,y,items,self.process_item)

    def process_item(self, item):
        x = ui.mx()
        y = ui.my()
        if item== 'File':
            get_file_dialog('',
                            self.callback,
                            filter='All files:*',
                            use_tkinter=self.tk_file)
            return
        elif item== 'Image file':
            get_file_dialog(self.default,self.callback,
                            filter='Image files:*.jpg:*.png:*.bmp:*.jpeg:*.gif:'
                                   '*.JPG:*.PNG:*.BMP:*.JPEG:*.GIF,All files:*',
                            use_tkinter=self.tk_file)
            return
        elif item == 'Media file':
            get_file_dialog(self.default, self.callback,
                            filter='Media files:*.wav:*.mpeg:*.mpg:*.mp3:*.flac:*.voc:*.raw:*.au'
                                   '*.WAV:*.MPEG:*.MPG:*.MP3:*.FLAC:*.VOC:*.RAW:*.AU,All files:*',
                            use_tkinter=self.tk_file)
            return

        elif item== 'Colour':
            if ui.is_safe_colour(self.default):
                d=self.default
            else:
                d='#888'
            result = colorchooser.askcolor(d)  # ,alog(*self.current_xy(),parent,default,markups)
            if result[0] is not None:
                self.callback(result[1])
            return
        elif item== 'Table':
            items=self.resources['table']
        elif item== 'Variable':
            items=self.resources['variable']
        elif item== 'Field name':
            try:
                items=self.resources['fieldnames'][self.table_var.get()]
            except:
                items=[]
        elif item=='Media player':
            if is_windows:
                items=['vlc','mpv','mpv --no-video','ffplay','wmplayer','smplayer']
            else:
                items=['mpv','mpv --no-video','mplayer -ao alsa','vlc','aplay','smplayer']
        elif item== 'Global variable':
            items=self.resources['global']
        elif item== 'System resource':
            items=self.resources['system']
        elif item=='Font':
            result=get_font()
            if result is not None:
                self.callback(result)
            return
        else:
            items=[]
        #print('ITEMS IS',items)
        if items:
            PopupMenu(self.parent, x, y,items,self.callback)


def right_click_menu(combobox,resources,tk_file,table_var):
    def callback(value):
        if value is not None:
            combobox.insert('insert',value)
    AuxInput(combobox,
             ['Table','Field name','Variable','Global variable','System resource'],
             '',
             callback,
             resources,
             tk_file,
             table_var=table_var
             )

class InputBox(tk.Frame):
    '''
    general input dialog
    clients (callers) should bind this frame's "<<inputboxbutton>>" event to a handler which can determine the action
        by inspecting this object's attribute 'button_press' which is a tuple of the button command and index
    clients should close this dialog by calling this object's close_window() method
    defn is {'title':'title',
             'style':'style'
             'rows':[row,..]
             }

    row=[item,....]
    item is {'type':'<type>',...}
            {'type':'input','var':key,options:{'fill':<colour>,'font':<font>},contexts':[]}
            {'type':'choice','var':key,'choices':[choice,..]}
            {'type':'check','var':key}
            {'type':'label','text':text,'options':{'fill':<colour>,'font':<font>}}
            {'type':'button','text':text,'icon':icon,'prefix':str,'index':int,'disabled':bool, ['command':str] }
            {'type':'radio','var':key}
            {'type':'radio_row','var':key,'choices':[choice,...]}

    E.g. single line input
    {'title':<title>,
     'style':'',
     'rows':[{'type':'input','var':StringVar}],

    '''

    def __init__(self,parent,x,y,defn,button_callback,undoable=True,
                 cancelable=True,info_key=None,yes=False,
                 no=False,ok=True,
                 tkinter_file_dialog=False,
                 history=None,
                 resources=None,
                 on_top=True):
        self.parent=parent
        self.x=x
        self.y=y
        self.button_callback=button_callback
        self.undoable=undoable
        self.cancelable=cancelable
        self.info_key=info_key
        self.yes=yes
        self.no=no
        self.ok=ok
        self.tkinter_file_dialog=tkinter_file_dialog
        #self.modal=defn['modal']
        self.win=tk.Toplevel(parent,) #,bd=10,relief='raised')
        self.win.geometry(f'+{round(x)}+{round(y)}')
        if on_top:
            self.win.attributes('-topmost',True)
        #parent.transient(self.win)
        #self.win.wm_overrideredirect(True)
        #self.win.grid()
        self.win.protocol("WM_DELETE_WINDOW", lambda:self.button('esc',0))
        self.win.wm_title(defn['title'])
        #self.win.geometry(f"+{x}+{y}")
        #ttk.Frame.__init__(self,self.win, style=defn['style'],padding='3 3 3 3')
        tk.Frame.__init__(self,self.win, padx=3, pady=3,background=bg_col)
        self.grid(row=0,column=0,sticky='nsew')
        self.win.columnconfigure(0,weight=1)
        self.win.rowconfigure(0,weight=1)
        self.win['background']='#DDD'

        self.columnconfigure(0,weight=0)
        self.columnconfigure(1,weight=1)
        #self.sep=ttk.Separator(self).grid(row=0,rowspan=len(defn['items']),column=1)
        #print('INPUTBOXDEFN')
        #pprint(defn)
        #print('INPUTBOXDEFNED')
        self.history=history
        self.reload(defn,resources)
        self.button_press=None,None

    def reload(self,defn,resources=None):
        frame_row=0
        frame_size=0
        frame=None
        self.defn=defn
        table_var=None
        for b in self.winfo_children():
            b.destroy()

        for row_no,cols in enumerate(defn['rows']):
            #print('cols',cols)
            if frame is None or len(cols)!=frame_size: #Start a new frame
                frame_size=len(cols)
                frame_offset=row_no
                #print(f'defn[style] is >{defn["style"]}<')
                frame=tk.Frame(self,background=bg_col) #,style=defn['style'])
                frame.grid(row=frame_row,column=1,sticky='ew')
                frame_row+=1
                for col,item in enumerate(cols):
                    if item['type']=='input':
                        frame.columnconfigure(col,weight=item['weight'])
                        #print('CONFIG COL WEIGHT',col,item['weight'])
                        #if col==1:
                        #    frame.columnconfigure(col,weight=1)
                        #elif col==3:
                        #    frame.columnconfigure(col,weight=2)
                        #else:
                        #    frame.columnconfigure(col,weight=0)
            for col_no,item in enumerate(cols):
                thing=item['type']
                if 'options' in item:
                    options=item['options']
                else:
                    options={}
                if thing=='label':
                    if 'justify' in options:
                        justify=options['justify']
                        options=dict(options)
                        options.pop('justify')
                    else:
                        if col_no==0:
                            #print('Right Justify')
                            justify='right'
                        else:
                            justify='center'
                    if 'background' in options:
                        options=dict(options)
                        lbg_col =options.pop('background')
                    else:
                        lbg_col=bg_col
                    if justify=='right':
                        tk.Label(frame,background=lbg_col,text=item['text'],justify=justify,**options).grid(
                            column=col_no,row=row_no-frame_offset,sticky='e',pady=5,padx=(3,3))
                    else:
                        tk.Label(frame,background=lbg_col,text=item['text'],**options).grid(
                            column=col_no,row=row_no-frame_offset,pady=5,padx=(3,3))

                elif thing=='input':
                    local_frame=frame #Default
                    local_c=col_no
                    local_r=row_no-frame_offset
                    variable=item['var']
                    contexts=item['contexts']
                    if contexts and contexts[0].startswith('hkey'):
                        hkey=contexts[0][4:]
                        contexts=[]
                    elif 'file' in contexts:
                        hkey='file'
                    elif 'image_file' in contexts:
                        hkey='image_file'
                    elif 'colour' in contexts:
                        hkey='colour'
                    elif 'font' in contexts:
                        hkey = 'font'
                    else:
                        hkey='text'
                    if contexts:
                        print_('CONTEXTS',contexts)
                        local_frame=tk.Frame(frame,background=bg_col)
                        local_frame.columnconfigure(0,weight=1)
                        local_frame.columnconfigure(1,weight=0)
                        local_frame.grid(column=local_c,row=local_r,sticky='ew')
                        local_c=0
                        local_r=0
                    combobox=ttk.Combobox(local_frame,
                        textvariable=variable,
                        width=20*item['weight'],
                        values=self.history.get_list(hkey),
                        )
                    """entry=tk.Entry(local_frame,background='#FFF',
                              textvariable=variable,
                              **options)
                    entry.grid(
                        column=local_c,
                        row=local_r,
                        sticky=(tk.W,tk.E),
                        pady=5,
                        padx=(2,6))
                    #print('ATTEMPTING TO BIND RIGHTCLICK')
                    #entry.index()
                    entry.bind('<3>',
                               lambda event,contexts=contexts:
                                    self.button_callback(
                                        'rightclick',
                                        (entry,variable,contexts)),
                                        add=True
                               )"""
                    combobox.grid(row=local_r,column=local_c,sticky='ew',
                                  pady=5,padx=(2,6))
                    if resources is not None:
                        combobox.bind('<B3-ButtonRelease>',
                            lambda event,combobox=combobox:
                                right_click_menu(combobox,
                                                 resources,
                                                 self.tkinter_file_dialog,
                                                 table_var)
                        )

                    if contexts:
                        if 'truefalse' in contexts:
                            def update(value,variable=variable):
                                if value is not None:
                                    variable.set('True' if value=='Yes' else
                                                 'False')
                            tk.Button(local_frame,
                                image=icon('popupmenu'),
                                background=bg_col,
                                command=lambda:PopupMenu(
                                    local_frame,
                                    ui.mx(),
                                    ui.my(),
                                    ['Yes','No'],
                                    update)).grid(column=local_c+1,
                                                  row=local_r,
                                                  sticky=('w'),
                                                  pady=5)
                        else:
                            def write_back(value,variable,combobox,hkey):
                                if value is not None:
                                    if value!=variable.get():
                                        variable.set(value)
                                    self.history.add(hkey,value)
                                    newvals=self.history.get_list(hkey)
                                    combobox['values']=newvals
                            #combobox.bind('<FocusOut>', lambda event:self.write_back(True))
                            def just_update_history(value,khey):
                                self.history.add(hkey,value)
                            combobox.bind('<Return>',
                                lambda
                                    event,
                                    variable=variable,
                                    hkey=hkey
                                :just_update_history(variable.get(),hkey)
                            )
                            extra_menu=[]
                            if 'file' in contexts:
                                extra_menu.append('File')
                            if  'image_file' in contexts:
                                extra_menu.append('Image file')
                            if 'media_file' in contexts:
                                extra_menu.append('Media file')
                            if 'media_player' in contexts:
                                extra_menu.append('Media player')
                            if  'field' in contexts:
                                extra_menu.append('Field name')
                            if 'table' in contexts:
                                extra_menu.append('Table')
                                table_var=variable
                            if 'colour' in contexts:
                                extra_menu.append('Colour')
                            if 'font' in contexts:
                                extra_menu.append('Font')
                            if resources is not None:
                                extra_menu.append('Variable')
                                extra_menu.append('Global variable')
                                extra_menu.append('System resource')
                            tk.Button(local_frame,
                                image=icon('popupmenu'),
                                background=bg_col,
                                command=lambda
                                    variable=variable,
                                    combobox=combobox,
                                    extra_menu=extra_menu,
                                    hkey=hkey
                                :AuxInput(
                                    local_frame,
                                    extra_menu,
                                    variable.get(),
                                    lambda
                                        value,
                                        variable=variable,
                                        combobox=combobox,
                                        hkey=hkey
                                    :write_back(value,
                                                variable,
                                                combobox,
                                                hkey),
                                    table_var=table_var,
                                    resources=resources,
                                    tk_file=self.tkinter_file_dialog)).grid(
                                    column=local_c+1,
                                    row=local_r,
                                    sticky=('w'),
                                    pady=5)

                    frame.columnconfigure(0,weight=0)
                    #frame.columnconfigure(1,weight=0)

                    #self.variable.trace_add('write',lambda v,i,m:self.trace())
                    #self.combobox.bind('<FocusOut>', lambda event:self.write_back(True))
                    #self.combobox.bind('<Return>', lambda event:self.write_back(True))

                    #entry=tk.Entry(local_frame,background='#FFF',
                    #          textvariable=variable,
                    #          **options)
                    #entry.grid(
                    #    column=local_c,
                    #    row=local_r,
                    #    sticky=(tk.W,tk.E),
                    #    pady=5,
                    #    padx=(2,6))
                    #print('ATTEMPTING TO BIND RIGHTCLICK')
                    #entry.index()

                    #entry.bind('<3>',
                    #           lambda event,contexts=contexts:
                    #                self.button_callback(
                    #                    'rightclick',
                    #                    (entry,variable,contexts)),
                    #                    add=True
                    #           )






                elif thing=='check':
                    tk.Checkbutton(frame,background=bg_col,variable=item['var']).grid(column=col_no,row=row_no-frame_offset,padx='3',sticky=tk.W,pady=3)
                elif thing=='radio':
                    tk.Radiobutton(frame,background=bg_col,textvariable=item['var']).grid(column=col_no,row=row_no-frame_offset,padx='3',sticky=tk.W,pady=5)
                elif thing=='radio_row':
                    group=tk.Frame(framebackground=bg_col,)
                    group.grid(row=row_no-frame_offset,column=col_no,sticky=(tk.W,tk.E),pady=5)
                    for col,choice in enumerate(item['choices']):
                        ttk.Radiobutton(group,textvariable=item['var'],value=choice,text=choice).grid(column=col,row=0,padx='3',pady=5)
                elif thing=='choice':
                    cb=ttk.Combobox(frame,textvariable=item['var'])
                    cb.grid(column=col_no,row=row_no-frame_offset,sticky=('w'),pady=5)
                    cb['values']=item['choices']
                    cb.state(['readonly'])
                elif thing=='button':
                    if 'prefix' in item:
                        prefix=item['prefix']
                    else:
                        prefix=''

                    if 'command' in item:
                        command=item['command']
                    else:
                        command=None
                    key=item['text']
                    if 'icon' in item:
                        if item['disabled']:
                            state='disabled'
                        else:
                            state='normal'
                        button(frame,self,key,item['index'],row_no-frame_offset,
                               col_no,icon_name=item['icon'],command=command,state=state,
                               prefix=prefix)
                    else:
                        button(frame,self,key,item['index'],row_no-frame_offset,col_no,
                               command=command,prefix=prefix)

        buttons=tk.Frame(self,background=bg_col)#,style=defn['style'])
        buttons.grid(column=0,columnspan=4,row=frame_row,sticky=(tk.E,tk.W),pady=3,padx=3)
        cno=0
        if self.yes:
            button(buttons,self,'Yes',frame_row,0,cno,command='yes')
            cno+=1
        if self.no:
            button(buttons,self,'No',frame_row,0,cno,command='no')
            cno+=1
        if self.cancelable:
            button(buttons,self,'Cancel',frame_row,0,cno,command='esc')
            cno+=1
        if self.undoable:
            button(buttons,self,'Undo',frame_row,0,cno)
            cno+=1
        if self.info_key is not None:
            button(buttons,self,'Info',frame_row,0,cno,command='help')
            cno+=1
        if self.ok:
            button(buttons,self,'Ok',frame_row,0,cno,command='ok')
            cno+=1

    def button(self,command,index):
        if command=='dis':  #todo here - make disabled buttons genuinely disabled and remove this hack
            return
        #self.button_press=command,index
        #print('INPUT BOX BUTTON PRESS',command,index)
        self.button_callback(command,index)
        #self.update_idletasks()

        #self.event_generate("<<inputboxbutton>>",when="tail")
        #if command in ('ok','esc'):
        #    self.win.destroy()

    def close_window(self):
        self.win.destroy()

def main():
    #s = ttk.Style()
    #s.configure('Input.TFrame',borderwidth=5, relief='raised')
    pass

if __name__=='__main__':
    main()
"""
test_data={'title':'the title',
             'modal':True,
             'items':[('input','v1','v1prompt','v1val'),
                      ('input','v2','v2proooooooooompt','v2valllllllllll'),
                      ('check','v3','checkV3prompt','True'),
                      ],
             'style':'',#Input.TFrame',
           }
        event=args[0]
        print('x=',event.x_root,'y=',event.y_root)
        test_data['x']=event.x_root
        test_data['y']=event.y_root
        ui.register_event_receiver(self.desktop,'<<ok>>',self.ok,self)
        ui.register_event_receiver(self.desktop,'<<esc>>',self.esc,self)
        self.state='right_clicked'
        self.active_widget=ui.call(lambda:inputbox.InputBox(self.desktop,test_data))
        """