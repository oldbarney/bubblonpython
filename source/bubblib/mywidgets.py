"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from bubblib.filedialog import get_file_dialog
from bubblib.iset import Iset


if __name__=='__main__':
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tkinter as tk
from tkinter import ttk, colorchooser

from .gutils import BubblFont, AutoScrollbar, darker, brighter, \
    length_for_pixels, pixels_for_length
from .uiserver import ui
tk.Label()

class PopupMenu:
    def __init__(self,parent,x,y,choices,callback,default=0):
        self.callback=callback
        self.m=tk.Menu(parent,tearoff=0,takefocus=True)
        for choice in choices:
            self.m.add_command(label=choice,command=lambda choice=choice:self.command(choice))
        self.m.tk_popup(x-6,y-6,entry=0)
        self.m.bind('<FocusOut>',lambda _event:self.command(None))

    def command(self,option):
        try:
            self.m.destroy()
        except:
            pass
        self.callback(option)

class TextInput:
    key=0

    @classmethod
    def get_style_key(cls,typ):
        cls.key+=1
        return f's{cls.key}.{typ}'
    def __init__(self,#parent,
                 canvas,x,y,
                 write_back_func,
                 history,
                 default='',
                 prompt=' ',
                 font=None,
                 colour=None,
                 fill=None,
                 length=15,
                 anchor='nw',
                 no_text_input=False,
                 button=None,
                 state='normal',
                 tkinter_file_dialog=False):
        self.style_keyc=TextInput.get_style_key('TCombox')
        self.style_keyl = TextInput.get_style_key('TLabel')

        self.tkinter_file_dialog=tkinter_file_dialog
        if font is None:
            font=BubblFont().font
        self.canvas=canvas
        #print('font=',font)
        self.write_back_func=write_back_func
        if colour is None or not ui.is_safe_colour(colour):
            colour='#000'
        if fill is None or not ui.is_safe_colour(fill):
            fill='#FFF'

        self.style_key=self.get_style_key('TLabel')
        self.style_keyc=self.get_style_key('TCombobox') #f'{colour}#{fill}.TCombobox'

        s=ttk.Style()
        s.configure(self.style_keyc,
                    background='#DDD',
                    fieldbackground=fill,
                    foreground='#000',
                    font=font
                    )
        #print('Style layout', s.layout(self.style_keyc))
        for el in ('Combobox.field',
                   'Combobox.downarrow',
                   'Combobox.textarea',
                   'Combobox.padding'):
            #print('element_options',el,s.element_options(el))
            pass
        #s.configure('TListbox',font=font.to_tuple())
        cid=canvas.create_text(x-2,y+3,text=prompt,anchor='ne',font=font,fill=colour)
        self.label=prompt

        #self.variable= tk.StringVar('') #value=default)
        self.variable=tk.StringVar(canvas,value=default)
        self._last_value=default


        frame=tk.Frame(canvas)
        self.combobox=ttk.Combobox(frame,
                                   textvariable=self.variable,
                                   width=length,
                                   background=fill,
                                   foreground=colour,
                                   font=font,
                                   style=self.style_keyc,
                                   values=history,
                                   state=state)
        self.combobox.grid(row=0,column=0)
        frame.columnconfigure(0,weight=0)
        frame.columnconfigure(1,weight=0)

        #self.variable.trace_add('write',lambda v,i,m:self.trace())
        self.combobox.bind('<FocusOut>', lambda event:self.write_back(True))
        self.combobox.bind('<Return>', lambda event:self.write_back(True))
        self.variable.trace_add('write',
                                  lambda v,i,m:self.write_back(False))

        if button is not None:
            if button=='colour':
                def extra():
                    parent = ui.root
                    ui.root.deiconify()
                    ui.root.lift()
                    ui.root.withdraw()
                    #print('Colour menu parent is ', parent)
                    default=self.variable.get()
                    if not ui.is_safe_colour(default):
                        default = '#888'

                    result = colorchooser.askcolor(
                        default,parent=self.combobox)  # ,alog(*self.current_xy(),parent,default,markups)
                    if result[0] is not None:
                        self.variable.set(result[1])
            elif button=='file':
                def extra():
                    def callback(result):
                        if result is not None:
                            self.variable.set(result)
                    get_file_dialog(self.variable.get(),
                               callback,
                               history=history,
                               use_tkinter=self.tkinter_file_dialog)
            elif button=='folder':
                def extra():
                    def callback(result):
                        if result is not None:
                            self.variable.set(result)
                    get_file_dialog(self.variable.get(),
                               callback,
                               directory=True,
                               history=history,
                               use_tkinter=self.tkinter_file_dialog)
            else:
                extra=None
            if extra is not None:
                tk.Button(frame,padx=3,pady=0,text='-',
                          background='#DDD',
                          foreground='#000',command=extra).grid(row=0,column=1)
        uid=canvas.create_window(x,y,window=frame,anchor=anchor)
        if no_text_input:
            self.combobox.config(state='readonly')
        self.uid=(uid,cid)

    @property
    def x(self):
        return int(self.canvas.coords(self.uid[0])[0])

    
    @x.setter
    def x(self,value):
        try:
            dx=int(value)-self.x
            self.canvas.move(self.uid[0],dx,0)
            self.canvas.move(self.uid[1],dx,0)
        except Exception as e:
            pass
            #print('Bad x setting in TextInput widget',e)

    @property
    def y(self):
        return int(self.canvas.coords(self.uid[0])[1])
    @y.setter
    def y(self,value):
        try:
            dy=int(value)-self.y
            self.canvas.move(self.uid[0],0,dy)
            self.canvas.move(self.uid[1],0,dy)
        except:
            pass  #print('Bad y setting in TextInput widget')

    @property
    def prompt(self):
        return self.label
    @prompt.setter
    def prompt(self,value):
        try:
            self.canvas.itemconfig(self.uid[1],text=value)
            self.label=value
        except:
            pass

    @property
    def colour(self):
        return '#000' #tk.Style(self.get_style_key()self.style['color']
    @colour.setter
    def colour(self,value):
        pass #self.style.configure()
    @property
    def fill(self):
        return '#FFF'
    @fill.setter
    def fill(self,value):
        pass




    def write_back(self,update_history):
        new_value=self.combobox.get()
        #print('TextInputWritingBack')
        self.write_back_func(new_value,update_history)

class Checkbox:
    key=0

    def __init__(self,#parent,
                 canvas,x,y,
                 write_back_func,
                 default=False,
                 prompt=' ',
                 font=None,
                 colour=None,
                 state='normal',
                 width=None,
                 fill='#DDD',
                 active_colour=None,
                 active_fill=None,
                 disabled_colour=None):
        if font is None:
            self._font=BubblFont()
        else:
            self._font=font
        self.canvas=canvas
        self.write_back_func=write_back_func
        colour=ui.valid_colour(colour,'#000')
        fill=ui.valid_colour(fill,'#CCC')
        active_colour=ui.valid_colour(active_colour,default=brighter(colour))
        active_fill = ui.valid_colour(active_fill, default=brighter(fill))
        disabled_colour=ui.valid_colour(disabled_colour,default=brighter(colour))

        self.variable=tk.IntVar(canvas,value=1 if default else 0)

        if width is not None:
            while width < self._font.width(prompt)+self._font.line_space*3//2:
                prompt+=' '
            while (width > self._font.width(prompt)+self._font.line_space*3//2
                    and prompt.endswith(' ')):
                prompt=prompt[:-1]

        self.checkbox=tk.Checkbutton(
            canvas,
            variable=self.variable,
            background=fill,
            foreground=colour,
            selectcolor=fill,
            activeforeground=active_colour,
            activebackground=active_fill,
            command=self.write_back,
            font=self._font.font,
            state=state,
            text=prompt,
            justify='left',
            disabledforeground=disabled_colour,
            bd=1,
            relief='raised'
            #style=style_keyc,
        )
        #self.variable.trace_add('write',lambda v,i,m:self.trace())

        self.uid=canvas.create_window(x,y,window=self.checkbox,anchor='nw')

    @property
    def x(self):
        return int(self.canvas.coords(self.uid)[0])
    @x.setter
    def x(self,value):
        try:
            self.canvas.moveto(self.uid,int(value),self.y)
        except:
            pass  #print('Bad x setting in Checkbox widget')

    @property
    def y(self):
        return int(self.canvas.coords(self.uid)[1])
    @y.setter
    def y(self,value):
        try:
            self.canvas.moveto(self.uid,self.x,int(value))
        except:
            pass #print('Bad y setting in Checkbox widget')

    @property
    def width(self):
        try:
            return self._font.width(str(self.checkbox['text']
                                        ))+3*self._font.line_space//2
        except Exception as e:
            pass #      print('CANNOT read checkbox width:',e)

    @width.setter
    def width(self,value):
        try:
            while int(value)< self.width and str(self.checkbox['text'])[-1:]==' ':
                self.checkbox['text']=str(self.checkbox['text'])[:-1]
            while int(value)<self.width:
                self.checkbox['text']+=' '
        except Exception as e:
            pass      #print('FAILED to get CHECKBOX width:',e)

    @property
    def prompt(self):
        return self.checkbox['text']
    @prompt.setter
    def prompt(self,value):
        self.checkbox['text']=value

    def write_back(self):
        self.write_back_func(self.variable.get()==1)

    @property
    def colour(self):
        return self.checkbox['foreground']
    @colour.setter
    def colour(self,value):
        try:
            self.checkbox['foreground']=value
        except:
            pass # print('Checkbox colour invalid')

    @property
    def active_colour(self):
        return self.checkbox['activeforeground']
    @active_colour.setter
    def active_colour(self,value):
        try:
            self.checkbox['activeforeground']=value
        except:
            pass # print('Checkbox colour invalid')

    @property
    def disabled_colour(self):
        return self.checkbox['disabledforeground']

    @disabled_colour.setter
    def disabled_colour(self, value):
        try:
            self.checkbox['disabledforeground'] = value
        except:
            pass  # print('Checkbox colour invalid')

    @property
    def fill(self):
        return self.checkbox['background']
    @fill.setter
    def fill(self,value):
        try:
            self.checkbox['background']=value
            self.checkbox['selectcolor']=value
        except:
            pass #  print('Checkbox fill invalid')

    @property
    def active_fill(self):
        return self.checkbox['activebackground']
    @active_fill.setter
    def active_fill(self,value):
        try:
            self.checkbox['activebackground']=value
        except:
            pass # print('Checkbox colour invalid')



class RadioGroup:
    key=0
    def __init__(self,#parent,
                 canvas,x,y,
                 write_back_func,
                 items,
                 value='',
                 prompt='',
                 font=None,
                 colour=None,
                 fill=None,
                 active_colour=None,
                 active_fill=None,
                 enabled=True,
                 length=None):
        try:
            if font is None:
                font=BubblFont(font)
            self._font=font
            self.canvas=canvas
            self.write_back_func=write_back_func
            colour=ui.valid_colour(colour,'#000')
            fill=ui.valid_colour(fill,'#CCC')

            self.variable=tk.StringVar()
            self.variable.set(value)
            self.prompt=prompt
            self.buttons=[]
            self._enabled=enabled

            self.frame=tk.Frame(canvas,
                bd=2,
                background=fill,
                padx=3,
                pady=2,
                relief='raised'

            )

            if isinstance(items,str):
                self.items=items.split(',')
            else:
                self.items=list(items)
            #if len(items)>1:
            #    maxl=max(len(prompt),max(len(item) for item in items))
            #    for i,item in enumerate(items):
            #        items[i]=(item+' '*maxl)[:maxl]
            if length is None:
                self._length=max(len(self.prompt)-4,
                                 max(len(item) for item in self.items))
            else:
                self._length=length
            if prompt!='':
                button_offset=1
                tk.Label(self.frame,bd=0,activeforeground=colour,
                         background=fill,activebackground=fill,
                         text=prompt,anchor='nw',
                         #font=self._font.get_bold()).grid(column=0,row=0,sticky='w')
                         font = self._font.font).grid(column=0, row=0, sticky='w')

            else:
                button_offset=0
            for i,item in enumerate(self.items,button_offset):
                button=tk.Radiobutton(self.frame,
                                text=item,
                                variable=self.variable,
                                command=lambda text=item:self.write_back_func(text),
                                value=item,
                                background=fill,
                                highlightthickness=0,
                                foreground=colour,
                                activeforeground=active_colour,
                                activebackground=active_fill,
                                font=self._font.font,padx=0,pady=0,
                                state='normal' if self._enabled else 'disabled',
                                justify='left',
                                borderwidth=0,
                                anchor='w',
                                width=self._length
                                )
                button.grid(column=0,row=i,sticky='w')
                self.buttons.append(button)
            self.uid=canvas.create_window(x,y,window=self.frame,anchor='nw')
        except Exception as e:
            print('RADIOFAIL',e)

    @property
    def x(self):
        return int(self.canvas.coords(self.uid)[0])
    @x.setter
    def x(self,value):
        try:
            self.canvas.moveto(self.uid,int(value),self.y)
        except:
            pass #     print('Bad x setting in Radio widget')

    @property
    def y(self):
        return int(self.canvas.coords(self.uid)[1])
    @y.setter
    def y(self,value):
        try:
            self.canvas.moveto(self.uid,self.x,int(value))
        except:
            pass #   print('Bad y setting in Radio widget')

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self,value):
        try:
            for bt in self.buttons:
                bt['width']=value
            self._length=value
        except:
            pass #  print('illegal setting of radio length')

    @property
    def height(self):
        return self.frame.winfo_height()

    @height.setter
    def height(self,value):
        pass  #print('illegal setting of radio height')

    @property
    def value(self):
        return self.variable.get()

    @value.setter
    def value(self,_value):
        if _value=='' or _value in self.items:
            self.variable.set(_value)

    @property
    def colour(self):
        result = self.frame['foreground']
        # print('RADIO FILL is',result)
        return result

    @colour.setter
    def colour(self, value):
        if ui.is_safe_colour(value):
            #self.frame.config(foreground=value)
            for button in self.buttons:
                button.config(foreground=value)

    @property
    def fill(self):
        result=self.frame['background']
        #print('RADIO FILL is',result)
        return result
    @fill.setter
    def fill(self,value):
        if ui.is_safe_colour(value):
            self.frame.config(background=value)
            for button in self.buttons:
                button.config(background=value)


    @property
    def active_colour(self):
        try:
            return self.buttons[0]['activeforeground']
        except:
            return self.colour

    @active_colour.setter
    def active_colour(self, value):
        if ui.is_safe_colour(value):
            for button in self.buttons:
                button['activeforeground']=value

    @property
    def active_fill(self):
        try:
            return self.buttons[0]['activebackground']
        except:
            return self.fill
    @active_fill.setter
    def active_fill(self, value):
        if ui.is_safe_colour(value):
            for button in self.buttons:
                button['activebackground']=value

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self,value):
        if value:
            for button in self.buttons:
                button['state']='normal'
            self.variable.set(self.variable.get())
        else:
            for button in self.buttons:
                button['state']='disabled'

class RuntimeErrorDialog:
    def __init__(self,message,callback):
        self.callback=callback
        self.win=win=tk.Toplevel(ui.root)
        win.title('Runtime Error')
        win.protocol("WM_DELETE_WINDOW", lambda:self.exit('default'))

        win.grid_columnconfigure(0,weight=1)
        win.grid_rowconfigure(0,weight=1)
        win.grid_rowconfigure(1,weight=0)
        can=tk.Canvas(win,width=640,height=480)
        can.grid(row=0,column=0,sticky='nsew')
        can.create_text(5,5,anchor='nw',justify='left',font=BubblFont('monospace,10').font,text=message)
        #tk.Label(win,text=self.message,justify='left',font='monospace').grid(row=0,column=0,sticky='nsew')
        frame=tk.Frame(win,borderwidth=3,relief='flat')
        frame.grid(row=1,column=0,sticky='ew')
        tk.Button(frame,text='Edit instruction',background='#fcc',command=lambda :self.exit('edinst')).grid(row=0,column=0)
        #tk.Button(frame,text='Ignore (follow default link)',background='#fcc',command=lambda :exit('default')).grid(row=0,column=2)

    def exit(self,result):
        self.win.destroy()
        self.callback(result)

class PopupInfo:
    def __init__(self,parent,block):
        self.block=block
        text=block.__doc__
        if text is None:
            text=block.__class__.__name__+'\n-No documentation available'
        lines=text.split('\n')
        title=lines[0]
        rest='\n'.join(lines[1:])
        font=BubblFont('monospace,10')
        w=max(font.width(line) for line in lines)+20
        h=font.line_space*(len(lines)+1)

        #print('w=',w,'h=',h)
        self.win=tk.Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.geometry(f'{w}x{h}+{max(20,ui.mx()-20)}+{max(0,ui.my()-40)}')
        self.win.protocol("WM_DELETE_WINDOW", self.destroy)
        self.canvas=tk.Canvas(self.win)
        self.canvas.grid(row=0,column=0,stick='nsew')
        self.win.grid_rowconfigure(0,weight=1)
        self.win.grid_columnconfigure(0,weight=1)
        self.canvas.create_text(w/2,10,anchor='n',text=title,fill='#505')
        self.canvas.create_text(10,30,anchor='nw',text=rest,font=font.font)
        self.win.bind('<Leave>',self.destroy)

    def destroy(self,event=None):
        self.win.destroy()



class HoverTextPresenter:
    def __init__(self,editor,block):
        self.block=block
        self.editor=editor
        text=block.__doc__
        if text is None:
            text=block.__class__.__name__+'\n-No documentation available'
        lines=text.split('\n')
        title=lines[0]
        rest='\n'.join(lines[1:])
        font=BubblFont('monospace,10')
        w=max(font.width(line) for line in lines)+20
        h=font.line_space*(len(lines)+1)

        #print('w=',w,'h=',h)
        self.win=tk.Toplevel(editor.canvas)
        self.win.overrideredirect(True)
        self.win.geometry(f'{w}x{h}+{max(20,ui.mx()-20)}+{max(0,ui.my()-40)}')
        self.win.protocol("WM_DELETE_WINDOW", self.destroy)
        self.canvas=tk.Canvas(self.win)
        self.canvas.grid(row=0,column=0,stick='nsew')
        self.win.grid_rowconfigure(0,weight=1)
        self.win.grid_columnconfigure(0,weight=1)
        self.canvas.create_text(w/2,10,anchor='n',text=title,fill='#505')
        self.canvas.create_text(10,30,anchor='nw',text=rest,font=font.font)
        self.win.bind('<Leave>',self.destroy)

    def destroy(self,event=None):
        self.win.destroy()


class SelectionBox:
    """
        Puts a scrollable list of selectable items on a page
        Selecting items generates BUBBL events
        :param parent_canvas: Window over which choices will be displayed
        :param x: Screen position
        :param y: Screen position
        :param items: List of objects (or cs-string) to choose from who's
            __str__() method is used to present the choice
        :param client_handler: function(item) where item is None, or integer
            or Iset for Esc,Single selection or Multi selection
        :param multi: whether multiple selections allowed
        :param fill: default background and border colour of non-selected items
        :param colour: colour of displayed text
        :param title:
        :param length: Initial number of display lines
        :param font:
        """
    def __init__(self, parent_canvas, x, y,
                 items,
                 client_handler,
                 multi=False,
                 colours=None,
                 highlights=None,
                 fill='#FFF',
                 colour='#000',
                 default=None,
                 title='',
                 length=10,
                 width=None,
                 enabled=True,
                 font=None):

        #print('mywidgets popup choice length',length)

        if x is None:
            x = parent_canvas.winfo_pointerx() # - ui.root.winfo_rootx()
        #elif parent is not None:
        #    x+=parent.winfo_x()

        if y is None:
            y = parent_canvas.winfo_pointery() # - ui.root.winfo_rooty()
        #elif parent is not None:
        #    y+=parent.winfo_y()

        if length is None:
            length=10
        self._length=length
        self.frame=tk.LabelFrame(parent_canvas,borderwidth=3,relief='raised',text=title)
        self.frame.columnconfigure(0,weight=1)
        self.frame.columnconfigure(1,weight=0)
        self.frame.rowconfigure(0,weight=1)

        #x+=parent.winfo_x()
        #y+=parent.winfo_y()
        self.fill=ui.valid_colour(fill,'#FFF')
        self.colour=ui.valid_colour(colour,'#000')
        self._colours=colours
        self._highlights=highlights
        self.multi=multi
        self.title=title


        if isinstance(items,str):
            items=items.split(',')
        self._items=items=list(items)

        if multi:
            #print('multi default is',default)
            if default is None:
                self.result=Iset(indexed=self.items)
            else:
                try:
                    self.result=Iset(default,indexed=items)
                except:
                    self.result=Iset(indexed=self.items)
        else:
            self.result=None

        if font is None:
            self.font= BubblFont()
        else:
            self.font=BubblFont(font)
        self.item_height=self.font.line_space

        if width is None:
            width=max([self.font.width(title)]+[self.font.width(item) for item in items])+self.font.line_space

        self.vsb = AutoScrollbar(self.frame, orient=tk.VERTICAL)
        self.vsb.grid(row=0, column=1, sticky='ns')

        self.canvas=tk.Canvas(self.frame,
                              width=width,
                              height=self.font.line_space*(self.length),
                              yscrollcommand=self.vsb.set)
        self.canvas.grid(row=0, column=0,sticky='nsew')
        self.vsb.config(command=self.canvas.yview)

        self.client_handler=client_handler
        self._enabled=not enabled
        self.enabled=enabled
        self.redraw_all(width+40)
        self.uid=parent_canvas.create_window(x,y,window=self.frame,anchor='nw')

    @property
    def enabled(self):
        return self._enabled
    @enabled.setter
    def enabled(self,value):
        if value:
            if not self._enabled:
                self.enable()
        else:
            if self._enabled:
                self.disable()

    def enable(self):
        #print('ENABLING SELECTION BOX')
        self.canvas.bind('<Configure>', lambda *args:self.redraw_all(None))
        self.canvas.bind('<Up>',lambda event:self.up())
        self.canvas.bind('<Down>',lambda event:self.down())
        self.canvas.bind('<Return>',lambda event:self.Ok())
        self.canvas.bind('<End>',lambda event:self.end())
        self.canvas.bind('<Home>',lambda event:self.home())
        self.canvas.bind('<Next>',lambda event:self.pg_dn())
        self.canvas.bind('<Prior>',lambda event:self.pg_up())
        self.canvas.bind('<Escape>',lambda event:self.esc())
        self.canvas.bind('<4>',lambda event:self.up())
        self.canvas.bind('<5>',lambda event:self.down())

        for i in range(len(self.items)):
            tag=f't_{i}'
            hltag=f'f_{i}'
            self.canvas.tag_bind(hltag,'<1>',lambda event,index=i:self.click(index,event.state&4==4),add=True)
            self.canvas.tag_bind(tag,'<1>',lambda event,index=i:self.click(index,event.state&4==4),add=True)

        self.canvas.focus_set()
        self.vsb.state='normal'
        self._enabled=True

    def disable(self):
        #print('DISABLING SELECTION BOX')
        #self.canvas.unbind('<Configure>')
        self.canvas.unbind('<Up>')
        self.canvas.unbind('<Down>')
        self.canvas.unbind('<Return>')
        self.canvas.unbind('<End>')
        self.canvas.unbind('<Home>')
        self.canvas.unbind('<Next>')
        self.canvas.unbind('<Prior>')
        self.canvas.unbind('<Escape>')
        self.canvas.unbind('<4>')
        self.canvas.unbind('<5>')
        self.vsb.state='disabled'
        for i in range(len(self.items)):
            tag=f't_{i}'
            hltag=f'f_{i}'
            self.canvas.tag_unbind(hltag,'<1>')
            self.canvas.tag_unbind(tag,'<1>')
        self._enabled=False

    def redraw_all(self,width=None):
        self.canvas['height']=self.item_height*(self._length)
        self.canvas.delete('row')
        if width==None:
            width=self.width+40
        for i,(item,colour,highlight) in enumerate(zip(self.items,self.colours,self.highlights)):
            self.add_choice(str(item),i,colour,highlight,width)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        if self._enabled:
            self.enable()

    def add_choice(self, text,index,colour,highlight,width):
        canvas=self.canvas
        tag=f't_{index}'
        hltag=f'f_{index}'
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

    @property
    def length(self):
        return self._length
    @length.setter
    def length(self,value):
        if value!=self._length:
            self._length=value
            self.redraw_all()

    @property
    def width(self):
        return self.canvas.winfo_width()+(
            24 if self.vsb in self.frame.winfo_children()
            else 0)
    @width.setter
    def width(self,value):
        try:
            self.canvas['width']=int(value)-(
                24 if self.vsb in self.frame.winfo_children()
                    else 0)
        except:
            pass # print('Invalid setting of chooser width')

    @property
    def height(self):
        return self.canvas.winfo_height()+self.font.line_space*3//2

    @height.setter
    def height(self,value):
        try:
            self.canvas['height']=max(int(value)-self.font.line_space*3//2,
                                      2*(self.font.line_space+3))
        except:
            pass  # print('illegal choice height assignment')

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

    def click(self,item,ctrl=False):
        if not self.multi:
            for i in range(len(self.items)):
                hltag = f'f_{i}'
                if i==item:
                    self.canvas.itemconfigure(
                        hltag,
                        fill=self.highlights[i])
                else:
                    self.canvas.itemconfigure(
                        hltag, fill=self.colours[i])

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
                self.client_handler(self.result)
            return 'break'
        else:
            for i in self.result:
                hltag=f'f_{i}'
                self.canvas.itemconfigure(hltag,fill=self.colours[item])
            hltag=f'f_{item}'
            self.canvas.itemconfigure(hltag,fill=self.highlights[item])
            self.result=set((item,))
            self.client_handler(self.result)

    @property
    def colours(self):
        if self._colours is None or len(self._colours)!=len(self.items):
            return [self.fill]*len(self.items)
        return self._colours

    @colours.setter
    def colours(self,values):
        try:
            self._colours=list(values)
        except:
            self._colours=None

    @property
    def highlights(self):
        if self._highlights is None or len(self._highlights)!=len(self.items):
            return [darker(colour) for colour in self.colours]
        return self._highlights

    @highlights.setter
    def highlights(self,values):
        try:
            self._highlights=list(values)
        except:
            self._highlights=None

    @property
    def items(self):
        return self._items
    @items.setter
    def items(self,values):
        try:
            self._items=list(values)
            self.redraw_all()
        except Exception as e:
            pass  #  print('Failed to change SelectionBox items',e)

def main():
    root = tk.Tk()
    canvas=tk.Canvas(root,width=500,height=400)
    canvas.pack()

    def write_back(value):
        #root.update_idletasks()
        #print('written back',value)
        return 'break'

    TextInput(#root,
              canvas,120,30,
              write_back,
              ['THESE','this','that'],
              default='entry',
              prompt='This',
              colour='#047',
              font=BubblFont('Monospace:20')
              )

    TextInput(#root,
              canvas,120,70,
              lambda value:write_back('No2.'+value),
              ['THESE','this','that','and some more','amd nmpde','and more'],
              fill='#AA0',
              default='entry',
              prompt='This')

    TextInput(#root,
              canvas, 120, 150,
              lambda value:write_back('No2.'+value),
              ['THESE','this','that','and some more','amd nmpde','and more'],
              default='entry',
              font=BubblFont('Monospace:25'),
              length=10)

    RadioGroup(canvas,
               200,300,
               write_back,
               'choice 1,Choice 2,Ch3',
               prompt='Choose')

    def popup(message):
        if message is None:
            print('Done')
        else:
            print('Chosen',message)

    canvas.bind('<3>',
                lambda event:PopupMenu(canvas,
                                       event.x_root,
                                       event.y_root,
                                       ['This','That','The other'],
                                       popup))

    print(tk.font.names())
    root.mainloop()



if __name__=='__main__':
    main()