"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from tkinter import StringVar, ttk, filedialog
from .popupmenu import Menu
from .gutils import BubblFont
from .inputbox import InputBox
from .popupchoice import PopupChoice
from .table import RawTable
from .uiserver import ui
from .utils import get_raw_val_from_kvlist, get_val_from_kvlist, \
    text_lines_from_html, log


class InputDialog:
    def __init__(self, callback, x,y, varnames,hkey,markups,
                 tkinterfiledialog=False,
                 history=None):    #todo here add help
        self.callback=callback
        title=get_raw_val_from_kvlist('title',markups,'Input')
        prompts=get_raw_val_from_kvlist('prompts',markups,None)
        if prompts is None or len(prompts)!=len(varnames):
            prompts=varnames
        defaults=get_raw_val_from_kvlist('defaults',markups,None)
        self.variables=[StringVar(None, d) for d in defaults]
        try:
            x=int(get_val_from_kvlist('x',markups,x))
        except ValueError:
            pass
        try:
            y=int(get_val_from_kvlist('y',markups,y))
        except ValueError:
            pass

        line_style={}
        prompt_style={}

        font=get_raw_val_from_kvlist('font',markups,None)
        if font is not None:
            prompt_style['font']=line_style['font']=BubblFont(font).font
        colour=get_raw_val_from_kvlist('colour',markups,None)
        if colour is not None:
            prompt_style['foreground']=line_style['foreground']=colour
        fill=get_raw_val_from_kvlist('fill',markups,None)
        if fill is not None:
            ttk.Style().configure('alert.TFrame',background=fill)
            style_name='alert.TFrame'
            prompt_style['background']=line_style['background']=fill
        else:
            style_name=''
        prompt_colour=get_raw_val_from_kvlist('colour',markups,None)
        if prompt_colour is not None:
            prompt_style['foreground']=prompt_colour
        rows=[[{'type':'label','text':prompt,**prompt_style},  #todo here add history buttons
               {'type':'input','var':variable,'weight':1,'contexts':[f'hkey{hkey}_{vn}'],**line_style}
              ] for (prompt,variable,vn) in zip(prompts, self.variables, varnames)
             ]
        defn={'title':title,'rows':rows,'modal':False,'style':style_name}
        self.input_box=InputBox(None,x,y,defn,self.button_press,
                               tkinter_file_dialog=tkinterfiledialog,history=history)
    def close(self):
        self.input_box.close_window()

    def show_help(self):
        log('Showing help')

    def button_press(self,command,index):
        log('InputBlock button press',command,index)
        if command in ('ok','esc'):
            #self.input_box.unbind("<<inputboxbutton>>",self.button_press)
            self.close()
            if command=='ok':
                self.callback([v.get() for v in self.variables])
            else:
                self.callback(None)
        if command=='Undo':
            log('Undo')
            return
        elif command=='Info':
            self.show_help()
            return

class AlertDialog:
    def __init__(self, callback, x,y, message, markups,tkinter_file_dialog=False,history=None): #todo here - add help
        self.callback=callback
        title=get_raw_val_from_kvlist('title',markups,'Alert!')
        try:
            x=int(get_val_from_kvlist('x',markups,x))
        except ValueError:
            pass
        try:
            y=int(get_val_from_kvlist('y',markups,y))
        except ValueError:
            pass
        line_style={}
        font=get_raw_val_from_kvlist('font',markups,None)
        if font is not None:
            line_style['font']=BubblFont(font).font
        colour=get_raw_val_from_kvlist('colour',markups,None)
        if colour is not None:
            line_style['foreground']=colour
        fill=get_raw_val_from_kvlist('fill',markups,None)
        if fill is not None:
            ttk.Style().configure('alert.TFrame',background=fill)
            style_name='alert.TFrame'
            line_style['background']=fill
        else:
            style_name=''
        line_style['justify']='left'
        message_lines=text_lines_from_html(message)

        rows=[[{'type':'label','text':text,'options':line_style}] for text in message_lines]
        defn={'title':title,'rows':rows,'modal':False,'style':style_name}
        self.input_box=InputBox(None,x,y,defn,
                               self.button_press,
                               undoable=False,cancelable=False,
                               tkinter_file_dialog=tkinter_file_dialog,
                               history=history)

    def close(self):
        self.input_box.close_window()

    def button_press(self,command,index):
        log('InputBlock button press',command,index)
        self.close()
        self.callback()

class AskUserDialog:
    def __init__(self, callback, x,y, message, markups,
                 tkinterfiledialog=False): # todo here add help
        self.callback=callback
        self.result='esc'
        title=get_raw_val_from_kvlist('title',markups,'Question')
        try:
            x=int(get_val_from_kvlist('x',markups,x))
        except ValueError:
            pass
        try:
            y=int(get_val_from_kvlist('y',markups,y))
        except ValueError:
            pass
        line_style={}
        font=get_raw_val_from_kvlist('font',markups,None)
        if font is not None:
            line_style['font']=BubblFont(font).font
        colour=get_raw_val_from_kvlist('colour',markups,None)
        if colour is not None:
            line_style['foreground']=colour
        fill=get_raw_val_from_kvlist('fill',markups,None)
        if fill is not None:
            ttk.Style().configure('alert.TFrame',background=fill)
            style_name='alert.TFrame'
            line_style['background']=fill
        else:
            style_name=''
        message_lines=text_lines_from_html(f'{message}')
        rows=[[{'type':'label','text':text,'options':line_style}] for text in message_lines]
        defn={'title':title,'rows':rows,'modal':False,'style':style_name}
        self.input_box=InputBox(None,x,y,defn,
                                self.button_press,
                                undoable=False,
                                cancelable=True,yes=True,no=True,ok=False,
                                tkinter_file_dialog=tkinterfiledialog)

    def close(self):
        self.input_box.close_window()

    def show_help(self):
        log('Showing help')

    def button_press(self,command,index):
        log('AskUserBlock button press',command,index)
        self.result=command
        self.close()
        self.callback(command)

class ChoiceDialog:
    def __init__(self,parent,callback,choices,markups,x=None,y=None):
        self.callback=callback
        self.offset=0
        try:
            x=int(get_val_from_kvlist('x',markups,x))
        except Exception:
            x=None
        try:
            y=int(get_val_from_kvlist('y',markups,y))
        except Exception:
            y=None
        try:
            length=int(get_val_from_kvlist('length',markups,None))
        except Exception:
            length=None

        self.multi=bool(get_val_from_kvlist('multiple',markups,False))

        title=get_raw_val_from_kvlist('title',markups,'')
        font=get_raw_val_from_kvlist('font',markups,None)
        default=get_val_from_kvlist('default',markups,None)
        colours=get_val_from_kvlist('colours',markups,None)

        if isinstance(choices,str):
            choices=choices.split(',')
        elif isinstance(choices,RawTable):
            field=get_raw_val_from_kvlist('field',markups,choices.field_names[0])
            if field not in choices.field_names:
                field=choices.field_names[0]
            choices=[getattr(row,field) for row in choices]
        else:
            try:
                choices=list(choices)
            except:
                choices=[choices]

        if self.multi:
            try:
                #print('getting multi default')
                default=set(i for i in default)
                #print('got multi default',default)
            except Exception as e:
                #print('didnt get default',e)
                default=set()
        else:
            try:
                default=int(default)
            except:
                default=None
        self.choice=PopupChoice(parent,x,y,choices,
                            client_handler=callback,
                            title=title,
                            multi=self.multi,
                            colours=colours,
                            default=default,
                            font=font,
                            length=length)

    def close(self):
        self.choice.close()

class ColourMenuDialog:
    pass

def menu_dialog(parent,callback,x,y,items,markups):
        #print('menudialog markups',markups)
    try:
        x=int(get_val_from_kvlist('x',markups,x))
    except ValueError:
        pass
    try:
        y=int(get_val_from_kvlist('y',markups,y))
    except ValueError:
        pass
    options={}
    window_options={}

    font=get_raw_val_from_kvlist('font',markups,None)
    title=get_raw_val_from_kvlist('title',markups,'')
    window_options['title']=title
    if font is not None:
        ttk.Style().configure('menu.TButton',font=BubblFont(font).font)
        options['style']='menu.TButton'
    colour=get_raw_val_from_kvlist('colour',markups,None)
    if colour is not None:
        ttk.Style().configure('menu.TButton',foreground=colour)
        options['style']='menu.TButton'
    fill=get_raw_val_from_kvlist('fill',markups,None)
    if fill is not None:
        ttk.Style().configure('menu.TFrame',background=fill)
        style_name='menu.TFrame'
        window_options['style']=style_name
        ttk.Style().configure('menu.TButton',background=fill)
        options['style']='menu.TButton'
    window_options['options']=options
    #print('modaldialogwindowoptionys',window_options)
    return Menu(parent, x, y, items, callback,**window_options)
