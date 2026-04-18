"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import tkinter as tk

from PIL import Image

from . import gutils
from .blockfactory import markups_dict
from .bubblevent import ButtonEvent, ScrollerEvent, \
    MouseEvent, WindowEvent, InputEvent, CheckboxEvent, RadioEvent, ChoiceEvent, \
    TextEdEvent, DropEvent, MenuEvent
from .displaything import DispThing, TextDispThing, RectangleDispThing, \
    ImageDispThing, EllipseDispThing, ArcDispThing, \
    PolygonDispThing, LineDispThing, ButtonDispThing, \
    ScrollbarDispThing, InputDispThing, CheckboxDispThing, \
    RadioDispThing, ChoiceDispThing, TextEdDispThing, thing_map
from .historymanager import History
from .iset import Iset
from .keyhandler import PageKeyHandler
from .logger import Logger
from .table import RawTable
from .uiserver import ui
from .utils import print_

if ui.has_dnd:
    from tkinterdnd2 import DND_FILES, DND_TEXT, DND_FILES, COPY
else:
    DND_FILES=DND_TEXT=DND_FILES=COPY=None

from .gutils import BubblFont, xywh_from_geom, point_inside_coords, \
    AutoScrollbar, canvas_to_PIL_image

page_contents_field_names=["thing:str",
                           "x:num",
                           "y:num",
                           "width:num",
                           "height:num",
                           #"colour:str",
                           #"fill:str",
                           #"active_colour:str",
                           #"active_fill:str",
                           "tags:str",
                           #"filename:str",
                           #"text:str",
                           "points",
                           "dxys",
                           #"justify:str",
                           #"line_width:int",
                           #"rotate:float",
                           #"joins:str",
                           #"ends:str",
                           #"nl:int",
                           #"anchor:str",
                           #"font:str",
                           #"value:float",
                           #"low:float",
                           #"high:float",
                           #"clip",
                           #"enabled",
                           #"prompt",
                           #"items"
                            ]


class PageContentsTable(RawTable):
    def __init__(self, page):
        self._page = page
        RawTable.__init__(self, 'PAGE:' + page.name,page_contents_field_names)

    @property
    def blank_row(self):
        return None

    def __len__(self):
        return len(self._page.items)

    def ok_swap_fields(self, row, values: dict):
        # return a list of previous values for field updates
        #log(f'thing swapping fields:{values}')
        thing = self._page.items[row]
        for f in values:
            # noinspection PyBroadException
            try:
                v=values[f]
                values[f]=getattr(thing,f,None)
                setattr(thing,f,v)
            except:
                pass
        return True

    def get_row(self,index):
        return self._page.items[index]

    def remove_row(self,index,undoable=True):
        try:
            return self._page.remove_item(self.get_row(index).uid,undoable)
        except:
            pass

    def insert_row(self,ind,row,undoable=True):  #not allowed
        pass

class BubblPage:
    undos=[]
    history_manager=History()

    def __init__(self, mach, name='output',title=None,
                 x=30,y=30,width=640,height=480,
                 paper='#D0F8FF',ink='#000',font=None,
                 closeable=True,fixed_size=False,scrollable=False,focus=False,
                 menu=None,fullscreen=False,markups=None,
                 left_margin=None,top_margin=None,cursor='arrow',on_top=False):
        self._mach = mach
        self.name = f'{name}'
        self._closeable=closeable
        self._fixed_size=fixed_size
        self._scrollable=scrollable
        self._fullscreen=fullscreen
        self._fullscreen_timeout=None
        self._font= BubblFont(font)

        if left_margin is None:
            left_margin=mach.config[('left_print_margin',0)]
        if top_margin is None:
            top_margin=mach.config[('top_print_margin',0)]
        try:
            self.left_margin=int(left_margin)
        except (ValueError,TypeError):
            self.left_margin=0
        try:
            self.top_margin=int(top_margin)
        except (ValueError,TypeError):
            self.top_margin=0

        self.dragged=None
        self.mime=DND_TEXT
        #log('font is',self.font)
        if title is None:
            self.title=self.name
        else:
            self.title=f'{title}'
        self._contents_table = PageContentsTable(self)
        self.cx = 0
        self.cy = 0
        self.mx = 0
        self.my = 0
        self.uid_map={}
        try:
            width=int(width)
        except:
            width=640
        try:
            height=int(height)
        except:
            height=480
        try:
            x=int(x)
        except:
            x=40
        try:
            y=int(y)
        except:
            y=40
        window=tk.Toplevel(ui.root,)
        window.title(f'{self.title}')
        window.protocol("WM_DELETE_WINDOW", self.window_closed)
        if on_top:
            window.attributes('-topmost',True)
        self.window=window
        self._paper=ui.valid_colour(paper,'#EEF')
        self.ink=ui.valid_colour(ink,'#000')
        if fixed_size:
            window.geometry(f'+{x}+{y}')
            self.canvas=tk.Canvas(window,background=self.paper,
                                  width=width,height=height,
                                  borderwidth=0,
                                  highlightthickness=0,
                                  cursor=cursor)
            self.canvas.grid(row=0,column=0)
            window.columnconfigure(0,weight=1)
            window.rowconfigure(0,weight=1)
            window.resizable(False,False)
        elif scrollable:
            window.geometry(f'{min(width,640)}x{min(height,480)}+{x}+{y}')
            window.columnconfigure(0,weight=1)
            window.rowconfigure(0,weight=1)
            window.columnconfigure(1,weight=0)
            window.rowconfigure(1,weight=0)
            window.grid_columnconfigure(0,weight=1)
            window.grid_rowconfigure(0,weight=1)
            window.grid_columnconfigure(1,weight=0)
            window.grid_rowconfigure(1,weight=0)
            self.vsb=AutoScrollbar(window,orient=tk.VERTICAL)
            self.hsb=AutoScrollbar(window,orient=tk.HORIZONTAL)
            self.vsb.grid(row=0,column=1,sticky='ns')
            self.hsb.grid(row=1,column=0,sticky='ew')
            self.canvas=tk.Canvas(window,
                                  background=self.paper,
                                  width=width,height=height,
                                  yscrollcommand=self.vsb.set,
                                  xscrollcommand=self.hsb.set,
                                  borderwidth=0,
                                  highlightthickness=0)
            self.vsb.config(command=self.canvas.yview)
            self.hsb.config(command=self.canvas.xview)
            self.canvas.grid(row=0,column=0,sticky='nsew')

            def set_scroll_region(*args):
                scrollregion=((0,0,self.canvas['width'],self.canvas['height']))
                self.canvas.config(scrollregion=scrollregion)
            self.window.bind('<Configure>',set_scroll_region)
        else:
            window.geometry(f'{width}x{height}+{x}+{y}')
            window.grid_rowconfigure(0,weight=1)
            window.grid_columnconfigure(0,weight=1)
            self.canvas=tk.Canvas(window,background=self.paper,
                                  borderwidth=0,
                                  highlightthickness=0)
            self.canvas.grid(row=0,column=0,rowspan=2,columnspan=2,sticky='nsew')
            self.canvas.bind('<Configure>',
                             lambda event:self._mach.queue_event(
                                 WindowEvent('WinSize',self)))
        self.canvas.bind('<1>',lambda event:self.mouse_event(event,'MouseDn',button='left'))
        self.canvas.bind('<2>',lambda event:self.mouse_event(event,'MouseDn',button='middle'))
        self.canvas.bind('<3>',lambda event:self.mouse_event(event,'MouseDn',button='right'))

        self.canvas.bind('<B1-ButtonRelease>',lambda event:self.mouse_event(event,'MouseUp',button='left'))
        self.canvas.bind('<B2-ButtonRelease>',lambda event:self.mouse_event(event,'MouseUp',button='middle'))
        self.canvas.bind('<B3-ButtonRelease>',lambda event:self.mouse_event(event,'MouseUp',button='right'))
        self.canvas.bind('<Motion>', lambda event:self.mouse_event(event,'MouseMv'))
        #self.canvas.bind('<Leave>', self.mouse_leave_event)
        #self.canvas.bind('<Enter>',self.mouse_enter_event)
        self.canvas.bind('<Double-Button-1>', lambda event:self.mouse_event(event,'MouseDbl',button='left'))
        self.canvas.bind('<Double-Button-2>', lambda event:self.mouse_event(event,'MouseDbl',button='right'))

        self.canvas.bind('<MouseWheel>', lambda event:self.mouse_event(event,'MouseWh',offset=round(event.delta/120)))
        self.canvas.bind('<4>', lambda event:self.mouse_event(event,'MouseWh',offset=-1))
        self.canvas.bind('<5>', lambda event:self.mouse_event(event,'MouseWh',offset=1))
        if ui.has_dnd:
            self.canvas.drop_target_register(DND_FILES, DND_TEXT)
            self.canvas.dnd_bind('<<Drop>>', self.dnd_drop)
            #self.canvas.dnd_bind('<<DropEnter>>', self.dnd_drop_enter)
            #self.canvas.dnd_bind('<<DropLeave>>', self.dnd_drop_leave)
            #self.canvas.dnd_bind('<<DropPosition>>', self.dnd_drop_position)
            self.canvas.drag_source_register(1, DND_TEXT)
            self.canvas.dnd_bind('<<DragInitCmd>>', self.dnd_drag_start)

        #self.canvas.drop_target_register(DND_FILES, DND_TEXT)
        #self.canvas.dnd_bind('<<Drop>>', self.dnd_drop)
        #self.canvas.dnd_bind('<<DropEnter>>', self.dnd_drop_enter)
        #self.canvas.dnd_bind('<<DropLeave>>', self.dnd_drop_leave)
        #self.canvas.dnd_bind('<<DropPosition>>', self.dnd_drop_position)
        #self.canvas.drag_source_register(1, DND_TEXT)
        #self.canvas.dnd_bind('<<DragInitCmd>>', self.dnd_drag_start)
        # self.canvas.dnd_bind('<<DragEndCmd>>',lambda event:log('DrageEndCmd',event.data))
        self.key_handler=PageKeyHandler(self)
        window.option_add('*tearOff', False)
        self._menu=menu
        if menu is not None:
            self._add_menu(menu)
        self.items=[]
        self.focus=focus
        initial_x=markups['x'] if markups and 'x' in markups else x
        initial_y=markups['y'] if markups and 'y' in markups else y
        self.window.update()
        self.x_offset = self.window.winfo_x() - initial_x
        self.y_offset = self.window.winfo_y() - initial_y
        if markups is not None:
            self.markups=markups
            #self.window.after_idle(lambda markups=markups:self.set_markups(markups))

    def set_markups(self,markups):
        if markups is not None:
            self.markups=markups

    def get_pil(self,background=False,monochrome=False):
        return canvas_to_PIL_image(self.canvas,
                                   background=background,
                                   monochrome=monochrome)

    @property
    def on_top(self):
        return False
    @on_top.setter
    def on_top(self,value):
        if value:
            self.window.attributes('-topmost',True)

    @property
    def fullscreen(self):
        return self._fullscreen_timeout is not None

    @fullscreen.setter
    def fullscreen(self,value):
        #For safety full screen mode needs to be renewed every 5 seconds
        if value:
            if self._fullscreen_timeout is not None:
                self.window.after_cancel(self._fullscreen_timeout)
            else:
                self.window.attributes('-fullscreen',True)
            self._fullscreen_timeout=self.window.after(5000,
                self._fullscreen_off)
        else:
            if self._fullscreen_timeout is not None:
                self.window.after_cancel(self._fullscreen_timeout)
            self._fullscreen_off()

    def _fullscreen_off(self):
        self._fullscreen_timeout = None
        self.window.attributes('-fullscreen', False)

    @property
    def contents(self):
        result=[]
        for row in self:
            try:
                result.append(row.get_builder())
            except Exception as e:
                print_('FAILED to get contents',e)
        return result

    def scaled_contents(self,scale):
        result=[]
        for row in self:
            try:
                result.append(row.get_scaled_builder(scale))
            except Exception as e:
                print_('FAILED to get scaled contents',e)
        return result

    @contents.setter
    def contents(self,contents):
        self.add_things(contents,self._mach.undoable)

    @property
    def menu(self):
        return self._menu

    @menu.setter
    def menu(self,value):
        if value==self.menu:
            return
        if isinstance(value,list) and all (
            isinstance(v,(str,list)) for v in value):
            self._add_menu(value)

    def _add_menu(self,menu):
        menubar = tk.Menu(self.window)
        for topmenu in menu:
            if isinstance(topmenu,str):
                menubar.add_command(
                    label=topmenu,command=lambda item=topmenu:
                                            self._menu_selected(item))
            else:
                submenu=tk.Menu(menubar)
                menubar.add_cascade(menu=submenu,label=topmenu[0])
                for com in topmenu[1:]:
                    submenu.add_command(
                        label=com,
                        command=lambda item=[topmenu[0],com]:
                                       self._menu_selected(item))
        self.window['menu']=menubar
        self._menu=menu

    def tagged(self,tag):
        for item in self.items:
            if tag in item.tags:
                return item

    def _menu_selected(self,item):
        self._mach.queue_event(MenuEvent(self,item))

    def __str__(self):
        return f'Page:{self.name} containing {len(self._contents_table)} items'

    def __iter__(self):
        return self.items.__iter__()

    def __getitem__(self,item):
        try:
            return self.items[item]
        except IndexError:
            return None

    def __len__(self):
        return len(self.items)

    def dnd_drop(self,event):
        #log('type', event.type)
        #log('types', ui.root.splitlist(event.type))
        #log('data',event.data)
        self._mach.queue_event(DropEvent(self,event))
        return COPY

    def dnd_drop_enter(self):
        return

    def dnd_drop_leave(self):
        return

    def dnd_drop_position(self):
        return

    def dnd_drag_start(self,event):
        #print('DND drag start')
        if self.dragged is None:
            return None
        return COPY, (self.mime,), self.dragged

    def key_event_event(self,event,action,button=None):
        bubbl_event=MouseEvent(
            action,
            round(self.canvas.canvasx(event.x)),
            round(self.canvas.canvasy(event.y)),
            self,
            button
        )
        self._mach.queue_event(bubbl_event)

    def proxy_mouse_event(self,source,event,action,button=None):
        #log('PROXY SOURCE',event.y,source.y,source)
        try:
            event.x+=source.x
            event.y+=source.y
        except Exception: #as e:
            return #print('MOUSE_PROXY EVENT exception',e) #cludge to mask exception
        self.mouse_event(event,action,button=button)

    def mouse_event(self,event,action,offset=None,button=None):
        mx=self.canvas.canvasx(event.x)
        my=self.canvas.canvasy(event.y)
        ctrl=gutils.ctrl(event)
        shift=gutils.shift(event)
        alt_gr=gutils.alt_gr(event)
        alt=gutils.alt(event)

        if action in (
            'MouseDn',
            'MouseDbl') and self._mach.current_page is not self:
            #log('OFF PAGE',self._mach.current_page.name,self.name)
            off_page_event=MouseEvent(
                'OffPage',round(mx),round(my),self,button,
                ctrl=ctrl,
                alt=alt,
                alt_gr=alt_gr,
                shift=shift
            )
            self._mach.queue_event(off_page_event)
        bubbl_event=MouseEvent(
            action,round(mx),round(my),self,button,offset=offset,
            ctrl=ctrl,
            alt=alt,
            alt_gr=alt_gr,
            shift=shift
        )
        self._mach.queue_event(bubbl_event)

    def save_message(self,filename,scale=2,width=None,height=None,
                     x=None,y=None,portrait=True,
                     monochrome=False):
        """
        Print the contents of the canvas to a postscript
file. Valid options: colormap, colormode, file, fontmap,
height, pageanchor, pageheight, pagewidth, pagex, pagey,
rotate, width, x, y.

        :param filename:
        :param scale:
        :param width:
        :param height:
        :param x:
        :param y:
        :param portrait:
        :param monochrome:
        :return:
        """


        jpg=(filename.lower().endswith('.jpeg') or
             filename.lower().endswith('.jpg'))
        #dest=BytesIO()
        pars={}
        if monochrome:
            pars['colormode']='gray'
        else:
            pars['colormode']='color'

        if width is None:
            width=self.canvas.winfo_width()
        if height is None:
            height=self.canvas.winfo_height()
        #if

        try:
            self.canvas.postscript(file=filename+'.eps',
                                   colormode='color',
                                   pagewidth=int(width*scale),
                                   pageheight=int(height*scale)
                                   )
            image=Image.open(filename+'.eps') #BytesIO(dest),formats=('eps',))
            image.load(transparency=not jpg)
            image.convert()
            #os.remove(filename+'.eps')
            image.save(filename)
            return 'Ok'
        except Exception as e:
            return f'{e}'

    def window_closed(self):
        if self._closeable:
            self._mach.remove_page(self.name,undoable=self._mach.undoable)
        else:
            self._mach.queue_event(WindowEvent('WinClose',self))

    @property
    def markups(self):
        return {field:getattr(self,field) for field in (
            'x','y','width','height',
            'ink','paper','title',
            'closeable','fixed_size','scrollable','font','cursor')}

    @markups.setter
    def markups(self,page_markups):  #poss here make undoable
        for m in page_markups:
            try:
                setattr(self, m, page_markups[m])
            except Exception as e:
                self._mach.log('Invalid page markup', e, level=2)

    @property
    def mouse_over(self):
        x=self.mx
        y=self.my
        return Iset((i for i,item in
                     enumerate(self.items) if item.contains_point(x,y)),
                    indexed=self.items)

    def point_over(self,x,y):
        return Iset(list(i for i,item in
             enumerate(self.items) if item.contains_point(x,y)),
            indexed=self.items)

    def update(self,mups):
        for mup in mups:
            #log('page.update',mup,mups)
            try:
                setattr(self,mup,mups[mup])
            except AttributeError:
                self._mach.log('cannot set attrib',mup,level=Logger.INFO)

    @property
    def x(self):
        try:
            return self.window.winfo_x()-self.x_offset
        except:
            return self.window.winfo_x()

    @x.setter
    def x(self,value):
        _x,y,_w,_h= xywh_from_geom(self.window.winfo_geometry())
        try:
            self.window.geometry(f'+{value}+{y}')
        except Exception as e:
            self._mach.runtime_error(f'Invalid page x:{e}')

    @property
    def y(self):
        try:
            return self.window.winfo_y()-self.y_offset
        except:
            return self.window.winfo_y()

    @y.setter
    def y(self,value):
        x,_y,_w_,h= xywh_from_geom(self.window.winfo_geometry())
        try:
            self.window.geometry(f'+{x}+{value}')
        except Exception as e:
            self._mach.runtime_error(f'Invalid page y:{e}')

    @property
    def height(self):
        #ui.call(ui.root.update_idletasks)
        if self.scrollable:
            return self.canvas['height']
        if self.fixed_size:
            return self.canvas.winfo_height()
        return self.window.winfo_height()

    @height.setter
    def height(self,value):
        #yin=self.y
        #ui.call(ui.root.update_idletasks)
        try:
            value=int(value)
        except ValueError:
            return
        if self.fixed_size:
            return
        if self.scrollable:
            self.canvas['height']=value
        else:
            x,y,w,_h= xywh_from_geom(self.window.winfo_geometry())
            try:
                self.window.geometry(f'{w}x{value}+{x}+{y}')
            except Exception as e:
                self._mach.runtime_error(f'Invalid page height:{e}')
            self.window['height']=value

    @property
    def width(self):
        #ui.call(ui.root.update_idletasks)
        if self.scrollable:
            return self.canvas['width']
        if self.fixed_size:
            return self.canvas.winfo_width()
        return self.window.winfo_width()

    @width.setter
    def width(self,value):
        try:
            value=int(value)
        except ValueError:
            return
        if self.fixed_size:
            return
        if self.scrollable:
            self.canvas['width']=value
        else:
            x,y,_w,h= xywh_from_geom(self.window.winfo_geometry())
            try:
                self.window.geometry(f'{value}x{h}+{x}+{y}')
            except Exception as e:
                self._mach.runtime_error(f'Invalid page width:{e}')

    @property
    def paper(self):
        return self._paper

    @paper.setter
    def paper(self, colour):
        try:
            self.canvas.configure(background=colour)
            self._paper = colour
        except Exception as e:
            self._mach.runtime_error(f'invalid color for page paper:{e}')

    @property
    def closeable(self):
        return self._closeable

    @closeable.setter
    def closeable(self, closeable):
        self._closeable = bool(closeable)

    @property
    def fixed_size(self):
        return self._fixed_size
    @fixed_size.setter
    def fixed_size(self,value):
        self._mach.log('Cannot change fixed size',level=Logger.INFO)

    @property
    def scrollable(self):
        return self._scrollable

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self,value):
        try:
            self._font= BubblFont(value)
        except Exception as e:
            self._mach.runtime_error(f'PAGE font invalid assignment:{e}')

    @property
    def cursor(self):
        return self.canvas['cursor']

    @cursor.setter
    def cursor(self,value):
        try:
            self.canvas['cursor']=value
        except Exception as e:
            self._mach.log(f'Failed to set cursor:{e}')

    def refresh(self):
        pass
        #self.window.update_idletasks()

    def add_things(self,things,undoable):
        for spec in things:
            thing=spec['thing']
            constructor=thing_map[thing]
            kwargs={ arg:spec[arg]
                        for arg in spec
                            if arg in constructor.fields
                            and arg!='thing'
                   }
            self.add_thing(undoable,constructor,**kwargs)

    def add_thing(self,undoable,constructor,**kwargs):
        if '' in kwargs:
            kwargs.pop('')
        if undoable:
            cx=self.cx
            cy=self.cy
        thing=constructor(self,**kwargs)
        self.items.append(thing)
        if isinstance(thing.uid,int):
            self.uid_map[thing.uid]=thing
        else:
            for uid in thing.uid:
                self.uid_map[uid]=thing
        if undoable:
            thing._creator=self._mach.diag.name,self._mach.node
            BubblPage.undos.append((self.name,'del',thing.uid,cx,cy))
            self._mach.add_undo(["page"])

    def add_text_thing(self,undoable,**kwargs):
        self.add_thing(undoable,TextDispThing,**kwargs)

    def add_button_thing(self,undoable,**kwargs):
        self.add_thing(undoable,ButtonDispThing,**kwargs)

    def add_rect_thing(self,undoable,**kwargs):
        self.add_thing(undoable,RectangleDispThing,**kwargs)

    def add_ellipse_thing(self,undoable,**kwargs):
        self.add_thing(undoable,EllipseDispThing,**kwargs)

    def add_arc_thing(self,undoable,**kwargs):
        self.add_thing(undoable,ArcDispThing,**kwargs)

    def add_polygon_thing(self,undoable,**kwargs):
        self.add_thing(undoable,PolygonDispThing,**kwargs)

    def add_line_thing(self,undoable,**kwargs):
        self.add_thing(undoable,LineDispThing,**kwargs)

    def add_image_thing(self,undoable,**kwargs):
        self.add_thing(undoable,ImageDispThing,**kwargs)

    def add_scrollbar_thing(self,undoable,**kwargs):

        #log('ADDING SCROLBAR DISPTHING',kwargs)
        self.add_thing(undoable,ScrollbarDispThing,**kwargs)

    def add_input_thing(self,undoable,**kwargs):
        self.add_thing(undoable,InputDispThing,**kwargs)

    def add_texted_thing(self,undoable,**kwargs):
        self.add_thing(undoable,TextEdDispThing,**kwargs)

    def add_choice_thing(self,undoable,**kwargs):
        self.add_thing(undoable,ChoiceDispThing,**kwargs)

    def add_checkbox_thing(self,undoable,**kwargs):
        self.add_thing(undoable,CheckboxDispThing,**kwargs)

    def add_radio_thing(self,undoable,**kwargs):
        self.add_thing(undoable,RadioDispThing,**kwargs)

    def add_generic_thing(self,undoable,**kwargs):
        self.add_thing(undoable,DispThing,**kwargs)

    def remove_item(self,uid,undoable):
        if isinstance(uid,int):
            item=self.uid_map.pop(uid)
        else:
            for i in uid:
                item=self.uid_map.pop(i)
        self.items.remove(item)
        if undoable:
            BubblPage.undos.append((self.name,
                               'ins',
                               type(item),
                               item.get_markups()))
            self._mach.add_undo(["page"])
        uids=item.uid
        if isinstance(uids,tuple):
            for uid in uids:
                self.canvas.delete(uid)
        else:
            self.canvas.delete(uids)

    def insert_item(self,index,item,undoable=False):
        if index<0 or index>len(self.items):
            index=len(self.items)
        uid=item.uid
        if isinstance(uid,int):
            self.uid_map[item.uid]=item
        else:
            for _uid in uid:
                self.uid_map[_uid]=item
        if undoable:
            BubblPage.undos.append((self.name,'del',uid,self.cx,self.cy))
            self._mach.add_undo(["page"])
        self.items.insert(index,item)
        self.restore_stacking_order(index)

    def restore_stacking_order(self,index):
        for i in range(index,len(self.items)):
            self.canvas.lift(self.items[i].uid)

    def undoably_clear_page(self):
        #log('page Undoably clearing page')
        to_remove=list(self.items)
        #log('Undoably clearing 1')
        to_remove.reverse()
        #log('Undoably clearing 2')
        BubblPage.undos.append('block')
        #log('Undoably clearing 3')
        for item in to_remove:
            #log('item to undoably remove is',item)
            #log('UNDOABLYREMOVEITEMMARKUPS',item.get_markups())
            try:
                BubblPage.undos.append((self.name,
                                   'ins',
                                   type(item),
                                   item.get_markups()))
        #log('Undoably clearing 4')
            except Exception as e:
                self._mach.log(f'Unable to add undo for {item.thing}: {e}',
                               level=Logger.INFO)
        BubblPage.undos.append('endblock')
        self._mach.add_undo(["page"])
        #log('Set up undos')
        for item in to_remove:
            uids=item.uid
            if isinstance(uids,tuple):
                for uid in uids:
                    self.canvas.delete(uid)
            else:
                self.canvas.delete(uids)
        self.uid_map.clear()
        self.items.clear()
        self.cx=0
        self.cy=0

    def clear_page(self):
        to_remove=list(self.items)
        #log('unUndoably clearing 1')
        to_remove.reverse()
        #log('unUndoably clearing 2')
        for item in to_remove:
            uids=item.uid
            if isinstance(uids,tuple):
                for uid in uids:
                    self.canvas.delete(uid)
            else:
                self.canvas.delete(uids)
        self.uid_map.clear()
        self.items.clear()
        self.cx=0
        self.cy=0

    @property
    def table(self):
        return self._contents_table

    @property
    def ui(self):
        return self.uid_map

    @property
    def focus(self):
        #log('page focus',self.canvas.focus_get())
        #log('self.canvas',self.canvas)
        return self.canvas.focus_get()==self.canvas

    @focus.setter
    def focus(self,value):
        if value:
            self.canvas.focus_set()

    @property
    def image(self):
        return self.get_pil(True)

    def dispatch_scroll_event(self,scroll_bar_item):
        try:
            self._mach.queue_event(ScrollerEvent(
                                        self,
                                        scroll_bar_item,
                                        scroll_bar_item.value,
                                        scroll_bar_item.tags))
        except Exception as e:
            self._mach.log(f'FAILED to dispatch scroll event {e}',level=Logger.INFO)

    def dispatch_input_event(self, input_disp_thing):
        try:
            self._mach.queue_event(InputEvent(
                                       self,
                                       input_disp_thing,
                                       input_disp_thing.value,
                                       input_disp_thing.tags)
                                  )
        except Exception as e:
            self._mach.log(f'FAILED to dispatch input event {e}',level=Logger.INFO)

    def dispatch_texted_event(self, texted_thing):
        try:
            self._mach.queue_event(TextEdEvent(
                                       self,
                                       texted_thing,
                                       texted_thing.value,
                                       texted_thing.tags)
                                  )
        except Exception as e:
            self._mach.log(f'FAILED to dispatch texted event {e}',level=Logger.INFO)

    def dispatch_choice_event(self, choice_disp_thing):
        try:
            self._mach.queue_event(ChoiceEvent(
                                       self,
                                       choice_disp_thing,
                                       choice_disp_thing.value,
                                       choice_disp_thing.tags)
                                  )
        except Exception as e:
            self._mach.log(f'FAILED to dispatch choice event {e}',level=Logger.INFO)

    def dispatch_checkbox_event(self, checkbox_thing):
        try:
            self._mach.queue_event(CheckboxEvent(
                                       self,
                                       checkbox_thing,
                                       checkbox_thing.value,
                                       checkbox_thing.tags)
                                  )
        except Exception as e:
            self._mach.log(f'FAILED to dispatch checkbox event {e}',level=Logger.INFO)

    def dispatch_radio_event(self, radio_thing):
        try:
            self._mach.queue_event(RadioEvent(
                                       self,
                                       radio_thing,
                                       radio_thing.value,
                                       radio_thing.tags )
                                  )
        except Exception as e:
            self._mach.log(f'FAILED to dispatch radio event {e}',level=Logger.INFO)

    def dispatch_button_event(self,button_item):
        try:
            self._mach.queue_event(
                ButtonEvent(self,
                            button_item,
                            button_item.text,
                            button_item.tags
                           )
            )
        except Exception as e:
            self._mach.log(f'FAILED to dispatch button event {e}',level=Logger.INFO)

    @classmethod
    def ok_undo(cls,mach):
        #log('PAGE UNDO')
        if len(BubblPage.undos)==0:
            cls._mach.log('No more undos',level=Logger.INFO)
            return False
        #(page_name,cmd,index,par)

        cmd=BubblPage.undos.pop()
        print_('PAGE UNDO cmd',cmd)
        if cmd=='endblock':
            while BubblPage.undos[-1]!='block':
                if not cls.ok_undo(mach):
                    return False
            else:
                cls.undos.pop()
                return True
        (page,cmd,*args)=cmd
        page=mach.pages[page]
        if cmd=='ins':
            constructor=args[0]
            kwargs=args[1]
            #log('UNDOING BY ADDING TO PAGE')
            page.add_thing(False,constructor,**kwargs)
            return True
        elif cmd=='del': #page,del,index,cx,cy
            page.remove_item(args[0],False)
            page.cx=args[1]
            page.cy=args[2]
            return True

class StdOutPage:
    def __init__(self):
        self.name = 'STDOUT'
        self.cx=50
        self.cy=50
        self.x=0
        self.y=0

    def add_output(self, text):
        print(text)

    def get_markups(self):
        return {}

    def update(self,markups):
        pass

stdoutpage = StdOutPage()

#c=tk.Canvas(None)
#c.create_image()