"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import tkinter as tk

from PIL import ImageFont,Image

from . import logger
from .gutils import get_image, BubblFont, minxy, length_for_pixels, \
    pixels_for_length, brighter, point_inside_coords, BUBBLImage, shape_points, \
    colour
from .mywidgets import TextInput, Checkbox, RadioGroup, SelectionBox
from .texteditor import TextEditorWidget
from .uiserver import ui
from .utils import log, AffineTransform, get_anchor_offsets_to_nw, scaled_kwargs

class DispThing: #Essentially a table row
    '''
    This class should be subclassed by displayable things (e.g. text)
    all attributes including those modifiable by markups, but not necessarily
    all run-time modifiable properties, should be put in __init__.
    This class implements a superset of properties for all sub-classes
    which should be overridden as necessary.
    Subclasses should declare a class variable 'fields' which is a tuple of
    run-time changeable/meaningful properties via table update code.
    '''
    pil_draw=None
    pil_scale=1

    def __init__(self,page,thing,tags):
        self.page=page
        self.canvas=page.canvas
        self._thing=thing
        self.uid=None
        self._nl=False
        self._image=None
        self._width=0
        self._height=0
        self._tags=tags
        self._filename=None
        self._clip=None
        self._value=None
        self._low=0
        self._high=100
        self._font=None
        self._button=None
        self._enabled=True
        self._creator=None

    def log(self,*args,level=1,**kwargs):
        self.page._mach.log('Page',self.page.name,':',self.thing,*args,level=level,**kwargs)

    def pil_render(self):
        pass

    def get_builder(self):
        #result={}
        #for fld in self.__class__.fields:
        #    print('FIELD',fld)
        #    result[fld]=getattr(self,fld)
        return {fld:getattr(self,fld) for fld in self.__class__.fields}

    def get_scaled_builder(self,scale):
        return scaled_kwargs(scale,self.get_builder())

    def bind_mouse_events(self, source):
        page=self.page
        source.bind('<1>', lambda event:page.proxy_mouse_event(self, event, 'MouseDn', 'left'),add=True)
        source.bind('<2>', lambda event:page.proxy_mouse_event(self, event, 'MouseDn', 'middle'),add=True)
        source.bind('<3>', lambda event:page.proxy_mouse_event(self, event, 'MouseDn', 'right'),add=True)
        source.bind('<B1-ButtonRelease>', lambda event:page.proxy_mouse_event(self, event, 'MouseUp', 'left'),add=True)
        source.bind('<B2-ButtonRelease>', lambda event:page.proxy_mouse_event(self, event, 'MouseUp', 'middle'),add=True)
        source.bind('<B3-ButtonRelease>', lambda event:page.proxy_mouse_event(self, event, 'MouseUp', 'right'),add=True)
        source.bind('<Motion>', lambda event:page.proxy_mouse_event(self, event, 'MouseMv'),add=True)

    def runtime_error(self,mess,e):
        self.page._mach.runtime_error(f'{mess}:{e}')

    def pil_points(self):
        scale=DispThing.pil_scale
        return tuple(round(p*scale) for p in self.points)

    def get_markups(self):
        #print('DISPTHING get_markups,fields',self._thing,self.fields)
        result={}
        for field in self.fields[1:]:
            #print('get markup field',field)
            result[field]=getattr(self,field)
        return result

        #return {field:getattr(self,field) for field in self.fields[1:]}

    @property
    def thing(self):
        return self._thing
    @thing.setter
    def thing(self,value):
        pass

    @property
    def x(self):
        return int(self.canvas.coords(self.uid)[0])

    @x.setter
    def x(self,value):
        try:
            dx=int(value)-self.x
            if dx!=0:
                self.canvas.move(self.uid,dx,0)
        except ValueError:
            self.log(f'illegal value assigned to {self.thing}.x',level=2)
    @property
    def y(self):
        return int(self.canvas.coords(self.uid)[1])
    @y.setter
    def y(self,value):
        try:
            dy=int(value)-self.y
            if dy!=0:
                self.canvas.move(self.uid,0,dy)
        except ValueError:
            self.log(f'illegal value assigned to {self.thing}.y',level=2)

    @property
    def justify(self):
        return self.canvas.itemcget(self.uid,'justify')
    @justify.setter
    def justify(self,value):
        try:
            self.canvas.itemconfig(self.uid,justify=value)
        except Exception as e:
            self.log('Illegal assignment to DISPLAY thing justify',value,e,level=2)

    @property
    def line_width(self):
        return self.canvas.itemcget(self.uid,'width')
    @line_width.setter
    def line_width(self,value):
        try:
            self.canvas.itemconfig(self.uid,width=int(value))
        except Exception as e:
            self.log('Illegal assignment to DISPLAY thing line_width',value,e,level=2)

    @property
    def width(self):  #override in text and polygons
        return self._width
    @width.setter
    def width(self,value):
        try:
            self._width=int(value)
        except Exception as e:
            self.log('Illegal assignment to DispThing.width',e,level=2)
    @property
    def height(self):
        return self._height
    @height.setter
    def height(self,value):
        try:
            self._height=int(value)
        except Exception as e:
            self.log('Illegal assignment to DispThing.height',value,e,level=2)
    @property
    def colour(self):  #to be overridden in text items
        return self.canvas.itemcget(self.uid,'outline')

    @colour.setter
    def colour(self,value):
        if value=='' or ui.is_safe_colour(value):
            self.canvas.itemconfig(self.uid,outline=value)
    @property
    def fill(self):
        return self.canvas.itemcget(self.uid,'fill')
    @fill.setter
    def fill(self,value):
        if value=='' or ui.is_safe_colour(value):
            self.canvas.itemconfig(self.uid,fill=value)

    @property
    def active_colour(self):  #to be overridden in text items
        return self.canvas.itemcget(self.uid,'activeoutline')

    @active_colour.setter
    def active_colour(self,value):
        if value=='' or ui.is_safe_colour(value):
            self.canvas.itemconfig(self.uid,activeoutline=value)
    @property
    def active_fill(self):
        return self.canvas.itemcget(self.uid,'activefill')
    @active_fill.setter
    def active_fill(self,value):
        if value=='' or ui.is_safe_colour(value):
            self.canvas.itemconfig(self.uid,activefill=value)

    @property
    def rotate(self):
        return self.canvas.itemcget(self.uid,'angle')
    @rotate.setter
    def rotate(self,value):
        try:
            self.canvas.itemconfig(self.uid,angle=float(value))
        except Exception as e:
            self.log('Illegal assignment to DISPLAY thing rotate',value,e,level=2)
    @property
    def points(self):
        try:
            result=self.canvas.coords(self.uid)
            return [round(p) for p in result]
        except Exception as e:
            self.log('POINTS not there',e,level=2)
    @points.setter
    def points(self,value):
        try:
            self.canvas.coords(self.uid,*value)
        except Exception as e:
            self.log('Illegal assignment to DISPLAY thing points',value,e,level=2)
    @property
    def dxys(self):
        points=self.points
        return [points[i+2]-points[i] for i in range(0,len(points)-2)]
    @dxys.setter
    def dxys(self,value):
        try:
            points=self.points[:2]+[0]*len(value)
            for i,v in enumerate(value):
                points[i+2]=points[i]+v
            self.points=points
        except Exception as e:
            self.log('Illegal assignment to DISPLAY thing dxys',level=2)
    @property
    def dxs(self):
        points=self.points
        return [points[i+2]-points[i] for i in range(0,len(points)-2,2)]
    @property
    def dys(self):
        points=self.points
        return [points[i+2]-points[i] for i in range(1,len(points)-2,2)]
    @property
    def joins(self):
        return self.canvas.itemcget(self.uid,'joinstyle')
    @joins.setter
    def joins(self,value):
        if value==round:
            value='round'
        self.canvas.itemconfig(self.uid,joinstyle=value)
    @property
    def ends(self):
        return self.canvas.itemcget(self.uid,'capstyle')
    @ends.setter
    def ends(self,value):
        if value==round:
            value='round'
        self.canvas.itemconfig(self.uid,capstyle=value)
    @property
    def text(self):
        #print('GETTING DISPTHING text')
        return self.canvas.itemcget(self.uid,'text')
    @text.setter
    def text(self,value):
        try:
            self.canvas.itemconfig(self.uid,text=value)
        except Exception as e:
            self.log('Illegal assignment to DISPLAY thing text',value,e,level=2)
    @property
    def nl(self):
        return self._nl
    @nl.setter
    def nl(self,value):
        self._nl=bool(value)
    @property
    def font(self):
        return str(self._font)
    @font.setter
    def font(self,value):
        self._font=BubblFont(value)
        try:
            self.canvas.itemconfig(self.uid,font=self._font.font)
        except Exception as e:
            self.log('Illegal font assignment',e,level=2)

    @property
    def image(self):
        return self._image
    @image.setter
    def image(self,value):
        if isinstance(value,Image.Image):
            value=BUBBLImage(value)
        try:
            self.canvas.itemconfig(self.uid,image=value.get_image_for_canvas())
            self.canvas.lift(self.uid)
            self._image=value
        except Exception as e:
            self.log('Bad Image assignment to display thing:',e,level=2)

    @property
    def tags(self):
        return self._tags
    @tags.setter
    def tags(self,value):
        self._tags=value

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self,value):
        pass

    @property
    def anchor(self):
        if isinstance(self.uid,tuple):
            return self.canvas.itemcget(self.uid[0],'anchor')
        return self.canvas.itemcget(self.uid,'anchor')
    @anchor.setter
    def anchor(self,value):
        if isinstance(self.uid,tuple):
            try:
                self.canvas.itemcconfig(self.uid[0],anchor=value)
            except:
                pass
        try:
            self.canvas.itemconfig(self.uid,anchor=value)
        except:
            pass

    @property
    def clip(self):
        return self._clip
    @clip.setter
    def clip(self,value):
        self._clip=value

    def get_list(self):
        return [str(getattr(self,f)) for f in self.fields]


    @property
    def value(self):
        return self._value
    @value.setter
    def value(self,value):
        self._value=value

    @property
    def prompt(self):
        return ''
    @prompt.setter
    def prompt(self,value):
        pass

    @property
    def button(self):
        return self._button

    @button.setter
    def button(self,value):
        if value in ('colour','file','folder',None):
            self._button=value

    def length_from_width(self,width):
        try:
            width=int(width)
        except:
            return 1
        return max(1,length_for_pixels(width,self._font.font))

    def width_from_length(self,length):
        try:
            length=int(length)
        except:
            return 10
        return pixels_for_length(max(1,length),self._font.font)

    @property
    def enabled(self):
        return self._enabled
    @enabled.setter
    def enabled(self,value):
        try:
            self._enabled=bool(value)
        except:
            pass

    def contains_point(self,x,y):
        #print(f'{self.thing} {x},{y} {self.x},{self.y} {self.width},{self.height}',
        #      x in range(self.x,self.x+self.width),
        #      y in range(self.y,self.y+self.height))

        w=x-self.x
        if w<0 or w>self.width:
            return False
        h=y-self.y
        return h>=0 and h<=self.height

class TextDispThing(DispThing):
    fields=('thing','x','y','tags','text','colour','fill','active_colour',
            'active_fill','font','rotate','anchor','nl','justify')
    def __init__(self, page, text='', x=None, y=None, colour=None,fill=None,
                 active_colour=None,active_fill=None,
                 font=None, rotate=0, nl=False, justify='left',anchor='nw',
                 tags='',xo=None,yo=None):
        DispThing.__init__(self,page,'text',tags)
        if anchor not in ('n','ne','e','se','s','sw','w','nw','center'):
            self.log('BAD Anchor TextDispThing',anchor,text,level=2)
            anchor='nw'
        try:
            text=str(text)
        except Exception as e:
            text=f'Invalid {e}'

        if font is None:
            self._font=page.font
        else:
            self._font=BubblFont(font)
        colour=ui.valid_colour(colour,default=page.ink)
        active_colour=ui.valid_colour(active_colour,default=brighter(colour))
        #print('font is ',self.font)
        if x is None:
            x=page.cx
        else:
            try:
                x=int(x)
            except Exception as e:
                self.log('x',e,level=2)
                x=0

        if y is None:
            y=page.cy
        else:
            try:
                y=int(y)
            except Exception as e:
                self.log('illegal y',e,level=2)
                y=0

        if ui.is_safe_colour(fill):
            active_fill=ui.valid_colour(active_fill,default=brighter(fill))
            try:
                polypoints=self._polypoints(x,y,text,rotate,anchor)
            except Exception as e:
                print('POLYPOINTS EXCEPTION',e)
            bguid=self.canvas.create_polygon(
                *polypoints,
                fill=fill,
                activefill=active_fill)
        else:
            bguid=None
        uid=self.canvas.create_text(
                              x,
                              y,
                              text=text,
                              angle=rotate,
                              fill=colour,
                              activefill=active_colour,
                              font=self._font.font,
                              anchor=anchor,
                              justify=justify)
        if bguid is None:
            self.uid=uid
        else:
            self.uid=(uid,bguid)
        #print('text coords',canvas.coords(self.uid))

        self.nl=nl
        if nl:
            page.cy+=self._font.line_space*(text.count('\n')+1)
            page.cx=0
        else:
            page.cy=self.y
            page.cx=self.x+self._font.width(text)

    def _polypoints(self,x,y,text,rotate,anchor):
        width = self._font.font.measure(text)
        height = self._font.line_space * (text.count('\n')+1)
        dx, dy = get_anchor_offsets_to_nw(anchor,width,height)
        trans = AffineTransform(rotate=rotate, cxy=(x, y))
        x-=dx
        y-=dy
        polypoints = (x, y,
                      x + width, y,
                      x + width, y + height,
                      x , y + height)
        #print('POLYPOINTS', polypoints)
        polypoints = trans.transform(*polypoints)
        #print('trans POLYPOINTS', polypoints)
        return polypoints

    @property
    def anchor(self):
        if isinstance(self.uid,tuple):
            return self.canvas.itemcget(self.uid[0],'anchor')
        return self.canvas.itemcget(self.uid,'anchor')

    @anchor.setter
    def anchor(self,value):
        if isinstance(self.uid,tuple):
            try:
                self.canvas.itemcconfig(self.uid[0],anchor=value)
                self.canvas.coords(self.uid[1],
                                   self._polypoints(
                                       self.x,self.y,
                                       self.text,self.rotate,value
                                   ))
            except:
                pass
        else:
            try:
                self.canvas.itemconfig(self.uid,anchor=value)
            except:
                pass

    @property
    def font(self):
        return str(self._font)
    @font.setter
    def font(self,value):
        old_font=self._font
        self._font=BubblFont(value)
        uid = self.uid
        if isinstance(uid, tuple):
            try:
                self.canvas.itemconfig(uid[0],font=self._font.font)
                self.canvas.coords(self.uid[1],
                               self._polypoints(
                                   self.x, self.y,
                                   self.text, self.rotate, value
                               ))
            except Exception as e:
                self._font=old_font
                self.log('Illegal font assignment',e,level=2)
        else:
            try:
                self.canvas.itemconfig(uid,font=self._font.font)
            except Exception as e:
                print('FONT ERROR', e)
                self.font=old_font
                self.log('Illegal font assignment',e,level=2)

    @property
    def rotate(self):
        uid=self.uid
        if isinstance(uid,tuple):
            uid=uid[0]
        return float(self.canvas.itemcget(uid,'angle'))
    @rotate.setter
    def rotate(self,value):
        try:
            value=float(value)
        except Exception as e:
            self.log('Illegal assignment to DISPLAY thing rotate',value,e,level=2)
            return

        uid=self.uid
        if isinstance(uid,tuple):
            self.canvas.itemconfig(uid[0],angle=value)
            self.canvas.coords(uid[1],
                               self._polypoints(
                                   self.x,self.y,
                                   self.text, self.rotate, value
                               ))
        else:
            self.canvas.itemconfig(uid,angle=float(value))

    @property
    def justify(self):
        uid=self.uid
        if isinstance(uid,tuple):
            uid=uid[0]
        return self.canvas.itemcget(uid,'justify')
    @justify.setter
    def justify(self,value):
        uid=self.uid
        if isinstance(uid,tuple):
            uid=uid[0]
        try:
            self.canvas.itemconfig(uid,justify=value)
        except Exception as e:
            self.log('Illegal assignment to DISPLAY thing justify',value,e,level=2)

    @property
    def x(self):
        uid=self.uid
        if isinstance(uid,tuple):
            uid=uid[0]
        return int(self.canvas.coords(uid)[0])
    @x.setter
    def x(self,value):
        uid=self.uid
        try:
            dx=int(value)-self.x
            if dx!=0:
                if isinstance(uid,tuple):
                    self.canvas.move(self.uid[0], dx, 0)
                    self.canvas.move(self.uid[1], dx, 0)
                else:
                    self.canvas.move(self.uid,dx,0)
        except ValueError:
            self.log(f'illegal value assigned to {self.thing}.x',type(value),value,level=2)

    @property
    def y(self):
        uid=self.uid
        if isinstance(uid,tuple):
            uid=uid[0]
        return int(self.canvas.coords(uid)[1])
    @y.setter
    def y(self,value):
        uid=self.uid
        try:
            dy=int(value)-self.y
            if dy!=0:
                if isinstance(uid,tuple):
                    self.canvas.move(self.uid[0], 0, dy)
                    self.canvas.move(self.uid[1], 0, dy)
                else:
                    self.canvas.move(self.uid,0,dy)
        except ValueError:
            self.log(f'illegal value assigned to {self.thing}.x',type(value),value,level=2)


    @property
    def width(self):
        return max(self._font.width(el) for el in self.text.split('\n'))

    @width.setter
    def width(self,value):
        self.log('Illegal assignment to TextDispThing.width',level=2)

    @property
    def height(self):
        return self._font.line_space*(self.text.count('\n')+1)

    @height.setter
    def height(self,height):
        self.log('Illegal assignment to DISPLAY text thing height',level=2)

    @property
    def text(self):
        uid=self.uid
        if isinstance(uid,tuple):
            uid=uid[0]
        return self.canvas.itemcget(uid,'text')
    @text.setter
    def text(self,value):
        value=f'{value}'
        uid=self.uid
        if isinstance(uid,tuple):
            self.canvas.itemconfig(uid[0],text=value)
            self.canvas.coords(uid[1],self._polypoints(
                self.x,self.y,
                value,self.rotate,self.anchor
            ))
        else:
            self.canvas.itemconfig(uid, text=value)

    @property
    def points(self):
        return [round(p) for p in self._polypoints(self.x,self.y,self.text,self.rotate,self.anchor)]

    @property
    def colour(self):  #to be overridden in text items
        uid = self.uid
        if isinstance(uid, tuple):
            uid = uid[0]
        return self.canvas.itemcget(uid,'fill')

    @colour.setter
    def colour(self,value):
        if value!=self.colour:
            uid = self.uid
            if isinstance(uid, tuple):
                uid = uid[0]
            self.canvas.itemconfig(uid,fill=value)

    @property
    def active_colour(self):  #to be overridden in text items
        uid = self.uid
        if isinstance(uid, tuple):
            uid = uid[0]
        return self.canvas.itemcget(uid,'activefill')

    @active_colour.setter
    def active_colour(self,value):
        if value!=self.active_colour:
            uid = self.uid
            if isinstance(uid, tuple):
                uid = uid[0]
            if value=='' or ui.is_safe_colour(value):
                self.canvas.itemconfig(uid,activefill=value)

    @property
    def fill(self):
        try:
            return self.canvas.itemcget(self.uid[1],'fill')
        except:
            return None


    @fill.setter
    def fill(self,value):
        try:
            self.canvas.itemconfig(self.uid[1],fill=value)
        except:
            pass

    @property
    def active_fill(self):
        try:
            return self.canvas.itemcget(self.uid[1],'activefill')
        except:
            return None

    @active_fill.setter
    def active_fill(self,value):
        try:
            self.canvas.itemconfig(self.uid[1],activefill=value)
        except:
            pass

    def contains_point(self, x, y):
        return point_inside_coords(x, y, self.points)

    def pil_render(self):
        points=self.pil_points()
        pars=self.get_builder()
        #DispThing.pil_draw.




class ButtonDispThing(DispThing):
    fields=('thing','x','y','tags','text','colour','fill','active_colour','active_fill','font','disabled_colour')
    def __init__(self, page, text='', x=None, y=None, colour=None,fill=None,
                 active_colour=None,active_fill=None,
                 disabled_colour=None,
                 font=None, image=None,anchor='nw',enabled=True,width=None,
                 tags=[]):
        #print('CREATING BUTTON')
        DispThing.__init__(self,page,'button',tags)
        if x is None:
            x=page.cx
        else:
            try:
                x=int(x)
            except Exception as e:
                self.log('illegal x',e,level=2)
                x=0

        if y is None:
            y=page.cy
        else:
            try:
                y=int(y)
            except Exception as e:
                self.log('illegal y',e,level=2)
                y=0
        if font is None:
            self._font=page.font
        else:
            self._font=BubblFont(font)
        if width is None:
            width={}
        else:
            width={'width':length_for_pixels(width,self._font.font)}
        #print('font is ',self.font)
        if colour is None or not ui.is_safe_colour(colour):
            colour=page.ink
        if disabled_colour is None or not ui.is_safe_colour(disabled_colour):
            disabled_colour=brighter(colour)

        fill=ui.valid_colour(fill,default='#BBB')
        active_colour=ui.valid_colour(active_colour,default=brighter(colour))
        active_fill=ui.valid_colour(active_fill,default=brighter(fill))

        #style.configure('DIS.TButton',background=fill,foreground=colour,
        #                       activeforeground=active_colour,
        #                       activebackground=active_fill,
        #                       font=self._font.font
        #                       )

        self.button_thing=tk.Button(self.canvas,
                              text=text,
                              #image=icon('new',20),
                               #width=self._font.font.measure(text)+6,
                               #height=self._font.line_space+6,
                               #image=image,
                               command=lambda : page.dispatch_button_event(self),
                               pady=0,padx=2,
                               borderwidth=2,
                               background=fill,
                               foreground=colour,
                               activeforeground=active_colour,
                               activebackground=active_fill,
                               disabledforeground=disabled_colour,
                               font=self._font.font,
                               state='normal' if enabled else 'disabled',
                                **width
                               #style='DIS.TButton',
                               #state='normal' if enabled else 'disabled'

                               )
        #self.button.config(width='100',height='30')
        self.uid=self.canvas.create_window(x,y,
                                      window=self.button_thing,
                                      anchor=anchor)
        #self.button.config(width='100',height='30')
        #print('text coords',canvas.coords(self.uid))
        self.bind_mouse_events(self.button_thing)


    @property
    def text(self):
        return self.button_thing.cget('text')
    @text.setter
    def text(self,value):
        try:
            self.button_thing.config(text=value)
        except Exception as e:
            self.log('failed to change text',e,level=2)

    @property
    def enabled(self):
        return self.button_thing['state']!='disabled'
    @enabled.setter
    def enabled(self,value):
        try:
            self.button_thing['state']='normal' if value else 'disabled'
        except Exception as e:
            self.log('failed to change button enabled',e,level=2)


    @property
    def width(self):
        result=self.button_thing.cget('width')
        #print('button interim width',result)
        if result==0:
            result=self._font.width(self.button_thing['text']
                                    )+self._font.line_space*2//3
        else:

            result=pixels_for_length(result,
                                     self._font.font)+self._font.line_space*2//3
        #print('button width result',result)
        return result

    @width.setter
    def width(self,value):
        try:
            self.button_thing['width']=length_for_pixels(
                int(value)-self._font.line_space*2//3,self._font.font)
        except Exception as e:
            self.log('Illegal assignment to ButtonDispThing.width',e,level=2)

    @property
    def height(self):
        return self._font.line_space+4
    @height.setter
    def height(self,value):
        self.log('setting button height',level=2)

    @property
    def colour(self):  #to be overridden in text items
        return self.button_thing.cget('foreground')

    @colour.setter
    def colour(self,value):
        if value!=self.colour:
            if ui.is_safe_colour(value):
                self.button_thing.config(foreground=value)


    @property
    def disabled_colour(self):  # to be overridden in text items
        return self.button_thing.cget('disabledforeground')

    @disabled_colour.setter
    def disabled_colour(self, value):
        if value != self.disabled_colour:
            if ui.is_safe_colour(value):
                self.button_thing.config(disabledforeground=value)

    @property
    def fill(self):  #to be overridden in text items
        try:
            return self.button_thing.cget('background')
        except:
            return None

    @fill.setter
    def fill(self,value):
        if value!=self.colour:
            if ui.is_safe_colour(value):
                try:
                    self.button_thing.config(background=value)
                except:
                    pass
    @property
    def active_colour(self):  #to be overridden in text items
        return self.button_thing.cget('activeforeground')

    @active_colour.setter
    def active_colour(self,value):
        if ui.is_safe_colour(value):
            self.button_thing.config(activeforeground=value)
    @property
    def active_fill(self):
        return self.button_thing.cget('activebackground')
    @active_fill.setter
    def active_fill(self,value):
        if ui.is_safe_colour(value):
            self.button_thing.config(activebackground=value)

    @property
    def points(self):
        return [self.x,self.y,self.x+self.width,self.y+self.height]

    @property
    def height(self):
        return self._font.line_space+8

    @height.setter
    def height(self,height):
        self.log('Illegal assignment to DISPLAY button thing height',level=2)


class ScrollbarDispThing(DispThing):
    fields=('thing','x','y','orientation','width','height','tags','low','high',
            'step','value','colour','fill','active_colour','enabled')
    def __init__(self, page, x=None, y=None, colour=None,fill=None,enabled=True,
                 low=0,high=100,step=1,value=None,tags=[],width=100,
                 active_colour=None,orientation='horizontal',height=100,
                 anchor='nw'):
        #print('CREATING Scrollbar')
        if isinstance(low+high+step,int):
            self._variable= tk.IntVar()
            self._low=low
            self._high=high
            self.step=step
            try:
                self._variable.set(int(value))
            except:
                self._variable.set(low)
        else:
            self._variable= tk.DoubleVar()
            try:
                self._low=float(low)
            except:
                self._low=0
            try:
                self._high=float(high)
            except:
                self._high=100
            try:
                self.step=float(step)
            except:
                self.step=((self._high-self._low)/100)
            try:
                self._variable.set(float(value))
            except:
                self._variable.set(self._low)

        DispThing.__init__(self,page,'scrollbar',tags)
        self.log('lhs',low,high,step,type(low),type(high),type(step))

        colour=ui.valid_colour(colour,page.ink)
        fill=ui.valid_colour(fill,default='#BBB')
        active_colour=ui.valid_colour(active_colour,default=brighter(colour))


        if x is None:
            x=page.cx
        else:
            try:
                x=int(x)
            except Exception as e:
                self.log('illegal x',e,level=2)
                x=0

        if y is None:
            y=page.cy
        else:
            try:
                y=int(y)
            except Exception as e:
                self.log('illegal y',e,level=2)
                y=0

        if orientation=='horizontal':
            try:
                length=int(width)
            except:
                length=100
        else:
            try:
                length=int(height)
            except:
                length=100

        self.scroller=tk.Scale(page.window,
                                length=length,
                                from_=low,
                                to=high,
                                orient=orientation,
                                showvalue=False,
                                troughcolor=fill,
                                background=colour,
                                activebackground=active_colour,
                                variable=self._variable,
                                state='normal' if enabled else 'disabled'
                               )
        self.scroller.bind('<Prior>',lambda *args:self.process_key(self.scroller.get()-self.step))
        self.scroller.bind('<Next>',lambda *args:self.process_key(self.scroller.get()+self.step))
        #self.scroller.bind('<Up>',lambda *args:self.process_key(self.scroller.get()-self.step))
        #self.scroller.bind('<Down>',lambda *args:self.process_key(self.scroller.get()+self.step))
        #self.scroller.bind('<Home>',lambda *args:self.process_key(self.low))
        #self.scroller.bind('<End>',lambda *args:self.process_key(self.high))
        self.scroller.bind('<KP_Left>',lambda *args:self.process_key(self.scroller.get()-1),'+')
        self.scroller.bind('<KP_Right>',lambda *args:self.process_key(self.scroller.get()+1),'+')
        self.scroller.bind('<KP_Prior>',lambda *args:self.process_key(self.scroller.get()-self.step))
        self.scroller.bind('<KP_Next>',lambda *args:self.process_key(self.scroller.get()+self.step))
        self.scroller.bind('<KP_Home>',lambda *args:self.process_key(self.low))
        self.scroller.bind('<KP_End>',lambda *args:self.process_key(self.high))
        self.bind_mouse_events(self.scroller)
        self.uid=self.canvas.create_window(page.cx if x is None else x,
                                      page.cy if y is None else y,
                                      window=self.scroller,
                                      anchor=anchor)
        #ui.root.update_idletasks()
        self._variable.trace_add('write',
                                  lambda v,i,m:page.dispatch_scroll_event(self))

    def process_key(self,new_value):
        self.scroller.set(new_value)
        return 'break'

    def value_changed(self,_var,_ind_,_mode,page):
        page.dispatch_scroll_event(self)

    @property
    def orientation(self):
        return str(self.scroller['orient'])

    @orientation.setter
    def orientation(self,value):
        if value in ('vertical','horizontal'):
            self.scroller['orient']=value
        else:
            self.log('Illegal orientation value',level=2)

    @property
    def height(self):
        if self.orientation=='vertical':
            return int(self.scroller['length'])
        return self.page.font.line_space

    @height.setter
    def height(self,value):
        if self.orientation=='vertical':
            self.scroller['length']=int(value)
        else:
            self.log('Cannot change scroller height',level=2)

    @property
    def width(self):
        if self.orientation=='horizontal':
            return int(self.scroller['length'])
        return self.page.font.line_space

    @width.setter
    def width(self,value):
        if self.orientation=='horizontal':
            self.scroller['length']=int(value)
        else:
            self.log('Cannot change scroller width',level=2)

    @property
    def enabled(self):
        return self.scroller['state']!='disabled'
    @enabled.setter
    def enabled(self,value):
        try:
            self.scroller['state']='normal' if value else 'disabled'
        except Exception as e:
            self.log('failed to change scroller enabled',e,level=2)


    @property
    def colour(self):  #to be overridden in text items
        return self.scroller.cget('background')

    @colour.setter
    def colour(self,value):
        if value!=self.colour:
            if ui.is_safe_colour(value):
                self.scroller.config(background=value)


    @property
    def fill(self):  #to be overridden in text items
        try:
            return self.scroller.cget('troughcolor')
        except:
            return None

    @fill.setter
    def fill(self,value):
        if value!=self.colour:
            if ui.is_safe_colour(value):
                try:
                    self.scroller.config(troughcolor=value)
                except:
                    pass
    @property
    def active_colour(self):
        return self.scroller.cget('activebackground')
    @active_colour.setter
    def active_colour(self,value):
        if ui.is_safe_colour(value):
            self.scroller.config(activebackground=value)

    @property
    def value(self):
        return self._variable.get()
    @value.setter
    def value(self,value):
        try:
            self._variable.set(value)
        except Exception as e:
            self.log(f'Failed to update scrollbar variable',e,level=2)

    @property
    def low(self):
        return self._low
    @low.setter
    def low(self,value):
        try:
            self.scroller.config(from_=value)
            self._low=value
        except Exception as e:
            self.log('Unable to set scroller from_',e,level=2)
        #todo here - replace scroller to change this value
        pass

    @property
    def high(self):
        return self._high
    @high.setter
    def high(self,value):
        try:
            self.scroller.config(to=value)
            self._high=value
        except Exception as e:
            self.log('Unable to set scroller to',e,level=2)

class InputDispThing(DispThing):
    fields=('thing','x','y','prompt','value','colour','fill','font','tags',
            'history','width','button','enabled')
    def __init__(self, page, prompt=None,value='',
                 x=None, y=None, colour=None,fill=None,
                 font=None,
                 history='INPUT',
                 width=100,
                 button=None,
                 enabled=True,
                 tags=[]
                 ):
        #print('CREATING TextInput')
        self.history_key=history
        history_list=page.history_manager.get_list(history)
        DispThing.__init__(self,page,'input',tags)
        self._value=value
        if font is None:
            self._font=page.font
        else:
            self._font=BubblFont(font)
        #print('font is ',self.font)
        if colour is None or not ui.is_safe_colour(colour):
            colour=page.ink
        fill=ui.valid_colour(fill,default='#FFF')
        if x is None:
            x=page.cx
        else:
            try:
                x=int(x)
            except Exception as e:
                self.log('illegal x',e,level=2)
                x=0

        if y is None:
            y=page.cy
        else:
            try:
                y=int(y)
            except Exception as e:
                self.log('illegal y',e,level=2)
                y=0

        length=max(1,length_for_pixels(int(width)-self._font.line_space,
                                          self._font.font))
        self._button=button

        self.text_input=TextInput(
            self.canvas,
            x,y,
            self._write_back,
            history_list,
            default=self.value,
            prompt=prompt,
            font=self._font.font,
            colour=colour,
            fill=fill,
            length=length,
            button=self._button,
            tkinter_file_dialog=page._mach.tkinter_file_dialog,
            state='normal' if enabled else 'disabled')
        self.bind_mouse_events(self.text_input.combobox)
        self.uid=(self.text_input.uid[0],self.text_input.uid[1])
        self.suppress_event=False


    @property
    def value(self):
        return self._value
    @value.setter
    def value(self,value):
        self._value=f'{value}'
        self.suppress_event=True
        self.text_input.variable.set(self._value)

    @property
    def text(self):
        return self.value
    @text.setter
    def text(self,value):
        self.value=value


    def _write_back(self,value,update_history=False):
        self._value=value
        if self.suppress_event:
            self.suppress_event=False
            return
        if update_history:
            self.page.history_manager.add_to_history(self.history_key,value)
            self.text_input.combobox['values']=self.page.history_manager.get_list(
                self.history_key)
        self.page.dispatch_input_event(self)

    @property
    def width(self):
        #print('getting combobox length')
        #print(f"combobox config width>{self.text_input.combobox['width']}<")


        return pixels_for_length(int(self.text_input.combobox['width']),
                                 self._font.font)+self._font.line_space
        #print('got combobox length')
    @width.setter
    def width(self,value):
        self.text_input.combobox.configure(
            width=max(1,length_for_pixels(int(value)-self._font.line_space,
                                          self._font.font)))

    @property
    def height(self):
        return self._font.line_space+4

    @height.setter
    def height(self,value):
        print('Illegal setting of height',level=2)

    @property
    def enabled(self):
        return self.text_input.combobox['state']!='disabled'
    @enabled.setter
    def enabled(self,value):
        try:
            self.text_input.combobox['state']='normal' if value else 'disabled'
        except Exception as e:
            self.log('failed to change text input enabled',e,level=2)


    @property
    def colour(self):  #to be overridden in text items
        return self.text_input.colour

    @colour.setter
    def colour(self,value):
        self.text_input.colour=colour


    @property
    def fill(self):
        return self.text_input.fill
    @fill.setter
    def fill(self,value):
        self.text_input.fill=value

    @property
    def history(self):
        return self.history_key

    @history.setter
    def history(self,value):
        self.history_key=value

    @property
    def x(self):
        return int(self.text_input.x)
    @x.setter
    def x(self,value):
        self.text_input.x=value

    @property
    def y(self):
        return int(self.text_input.y)
    @y.setter
    def y(self,value):
        self.text_input.y=value

    @property
    def prompt(self):
        return self.text_input.prompt
    @prompt.setter
    def prompt(self,value):
        self.text_input.prompt=value





class TextEdDispThing(DispThing):
    fields=('thing','x','y','value','colour','fill','font','tags','width',
            'height','enabled')
    def __init__(self, page, value='',
                 x=None, y=None, colour=None,fill=None,
                 font=None,
                 width=240,
                 height=180,
                 tags=[],
                 enabled=True
                 ):
        #print('CREATING TextEdDispthing')
        DispThing.__init__(self,page,'texted',tags)
        if font is None:
            self._font=page.font
        else:
            self._font=BubblFont(font)
        #print('font is ',self.font)
        if colour is None or not ui.is_safe_colour(colour):
            colour=page.ink
        if fill is None or not ui.is_safe_colour(fill):
            fill='#FFF'
        self._colour=colour
        self._fill=fill
        if x is None:
            x=page.cx
        else:
            try:
                x=int(x)
            except Exception as e:
                self.log('illegal x',e,level=2)
                x=0

        if y is None:
            y=page.cy
        else:
            try:
                y=int(y)
            except Exception as e:
                self.log('illegal y',e,level=2)
                y=0
        self.texted=TextEditorWidget(self.canvas,x,y,
                                     self._write_back,
                                     text=value,
                                     width=width,
                                     height=height,
                                     font=self._font.font,
                                     enabled=enabled)
        self.bind_mouse_events(self.texted.text)
        self.uid=self.texted.uid
        self._value=value


    @property
    def enabled(self):
        return self.texted.text['state']!='disabled'

    @enabled.setter
    def enabled(self,value):
        try:
            self.texted.text['state']='normal' if value else 'disabled'
        except Exception as e:
            self.log('failed to set text enabled',e,level=2)

    def _write_back(self,value):
        self.log('TextEditorWidget writing back',value)
        self._value=value
        self.page.dispatch_texted_event(self)

    @property
    def width(self):
        return round(pixels_for_length(self.texted.text['width'],self._font.font)+6)
    @width.setter
    def width(self,value):
        self.log('Setting texted width')
        self.texted.text['width']=length_for_pixels(value-6,self._font.font)

    @property
    def height(self):
        return round(self.texted.text['height']*self._font.line_space+6)

    @height.setter
    def height(self,value):
        self.log('Setting texted height')
        self.texted.text['height']=round(round(value+1)//self._font.line_space)

    @property
    def colour(self):  #to be overridden in text items
        return self._colour

    @colour.setter
    def colour(self,value):
        if ui.is_safe_colour(value):  #more here todo
            self._colour=value
        self.log('setting texted colour') #todo here finish this

    @property
    def fill(self):
        return self._fill
    @fill.setter
    def fill(self,value):
        if ui.is_safe_colour(value):  #todo more here
            self._fill=value

    @property
    def x(self):
        return int(self.canvas.coords(self.texted.uid)[0])
    @x.setter
    def x(self,value):
        self.canvas.coords(self.texted.uid,value,self.y)

    @property
    def y(self):
        return int(self.canvas.coords(self.texted.uid)[1])
    @y.setter
    def y(self,value):
        self.canvas.coords(self.texted.uid,self.x,value)
    @property
    def value(self):
        return self._value
    @value.setter
    def value(self,value):
        self._value=f'{value}'
        self.texted.change_text(self._value)

    @property
    def text(self):
        return self.value
    @text.setter
    def text(self,value):
        self.value=value


class CheckboxDispThing(DispThing):
    fields=('thing','x','y','prompt','value','colour','fill','active_colour',
            'active_fill','font','width','enabled','tags','disabled_colour')
    def __init__(self, page, prompt=None,value=False,
                 x=None, y=None, colour=None,fill=None,
                 active_colour=None,active_fill=None,
                 font=None,enabled=True,width=None,
                 tags=[],disabled_colour=None,
                 ):
        #print('CREATING Checkbox')
        DispThing.__init__(self,page,'checkbox',tags)
        self._value=bool(value)
        if font is None:
            self._font=page.font
        else:
            self._font=BubblFont(font)
        #print('font is ',self.font)
        colour=ui.valid_colour(colour,page.ink)
        fill=ui.valid_colour(fill,default='#DDD')
        active_colour=ui.valid_colour(active_colour,default=brighter(colour))
        active_fill = ui.valid_colour(active_fill, default=brighter(fill))
        disabled_colour=ui.valid_colour(disabled_colour,default=brighter(colour))
        self._colour=ui.valid_colour(colour,page.ink)
        self._fill=ui.valid_colour(fill,'#FFF')
        if x is None:
            x=page.cx
        else:
            try:
                x=int(x)
            except Exception as e:
                self.log('illegal x',e,level=2)
                x=0

        if y is None:
            y=page.cy
        else:
            try:
                y=int(y)
            except Exception as e:
                self.log('illegal y',e,level=2)
                y=0
        self.checkbox=Checkbox(
            self.canvas,
            x,y,
            self._write_back,
            default=self.value,
            prompt=prompt,
            font=self._font,
            colour=self._colour,
            state='normal' if enabled else 'disabled',
            width=width,
            fill=self._fill,
            active_colour=active_colour,
            active_fill=active_fill,
            disabled_colour=disabled_colour
        )
        self.bind_mouse_events(self.checkbox.checkbox)
        self.uid=self.checkbox.uid

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self,value):
        try:
            self.checkbox.variable.set(1 if value else 0)
            self._value=bool(value)
        except:
            self.log('Failed to set checkbox state',loglevel=logger.INFO)

    def _write_back(self,value):
        self._value=bool(value)
        self.page.dispatch_checkbox_event(self)

    @property
    def width(self):
        return self.checkbox.width

    @width.setter
    def width(self,value):
        try:
            self.checkbox.width=int(value)
        except Exception as e:
            self.log('Illegal assignment to CheckboxThing.width',e,level=2)

    @property
    def colour(self):  #to be overridden in text items
        return self.checkbox.colour

    @colour.setter
    def colour(self,value):
        self.checkbox.colour=value

    @property
    def fill(self):  #to be overridden in text items
        return self.checkbox.fill

    @fill.setter
    def fill(self,value):
        self.checkbox.fill=value
    @property
    def active_colour(self):
        return self.checkbox.active_colour
    @active_colour.setter
    def active_colour(self,value):
        self.checkbox.active_colour=value
    @property
    def disabled_colour(self):
        return self.checkbox.disabled_colour
    @disabled_colour.setter
    def disabled_colour(self, value):
        self.checkbox.disabled_colour = value
    @property
    def active_fill(self):
        return self.checkbox.active_fill
    @active_fill.setter
    def active_fill(self,value):
        self.checkbox.active_fill=value

    @property
    def height(self):
        return self._font.line_space+6

    @height.setter
    def height(self,height):
        self.log('Illegal assignment to DISPLAY checkbox thing height',level=2)

    @property
    def enabled(self):
        return self.checkbox.checkbox['state']!='disabled'
    @enabled.setter
    def enabled(self,value):
        try:
            self.checkbox.checkbox['state']='normal' if value else 'disabled'
        except Exception as e:
            self.log('failed to change checkbox enabled',e,level=2)

    @property
    def fill(self):
        return self.checkbox.fill

    @fill.setter
    def fill(self,value):
        self.checkbox.fill=value

    @property
    def history(self):
        return self.history_key

    @history.setter
    def history(self,value):
        self.history_key=value

    @property
    def x(self):
        return int(self.checkbox.x)
    @x.setter
    def x(self,value):
        self.checkbox.x=value

    @property
    def y(self):
        return int(self.checkbox.y)
    @y.setter
    def y(self,value):
        self.checkbox.y=value

    @property
    def prompt(self):
        return self.checkbox.prompt
    @prompt.setter
    def prompt(self,value):
        self.checkbox.prompt=value

class RadioDispThing(DispThing):
    fields=('thing','x','y','tags','prompt','items','width','colour',
            'fill','active_colour','active_fill','font','value')
    def __init__(self, page, items=[''],value='',x=None, y=None,
                 prompt='',colour=None,fill=None,active_colour=None,
                 active_fill=None,width=None, font=None,enabled=True,
                 tags=[]):
        #print('CREATING Radio buttons')
        DispThing.__init__(self,page,'radio',tags)
        if x is None:
            x=page.cx
        else:
            try:
                x=int(x)
            except Exception as e:
                self.log('illegal x',e,level=2)
                x=0
        if y is None:
            y=page.cy
        else:
            try:
                y=int(y)
            except Exception as e:
                self.log('illegal y',e,level=2)
                y=0
        if font is None:
            self._font=page.font
        else:
            self._font=BubblFont(font)
        #print('font is ',self.font)
        colour=ui.valid_colour(colour,default=page.ink)
        fill=ui.valid_colour(fill,default='#DDD')
        active_colour=ui.valid_colour(active_colour,default=brighter(colour))
        active_fill = ui.valid_colour(active_fill, default=brighter(fill))
        if width is not None:
            try:
                length=self.length_from_width(width-self._font.line_space*2)
            except:
                length=None
        else:
            length=None
        self.radio_group=RadioGroup(
            self.canvas,
            x,y,
            self.write_back,
            items,
            colour=colour,
            fill=fill,
            active_colour=active_colour,
            active_fill=active_fill,
            value=value,
            font=self._font,
            enabled=enabled,
            prompt=prompt,
            length=length,
        )
        self.bind_mouse_events(self.radio_group.frame)
        for but in self.radio_group.buttons:
            self.bind_mouse_events(but)
        self.uid=self.radio_group.uid

    @property
    def colour(self):  #to be overridden in text items
        return self.radio_group.colour

    @colour.setter
    def colour(self,value):
        self.radio_group.colour=value

    @property
    def fill(self):
        return self.radio_group.fill
    @fill.setter
    def fill(self,value):
        self.radio_group.fill=value
    @property
    def active_colour(self):
        return self.radio_group.active_colour
    @active_colour.setter
    def active_colour(self,value):
        self.radio_group.active_colour=value
    @property
    def active_fill(self):
        return self.radio_group.active_fill
    @active_fill.setter
    def active_fill(self,value):
        self.radio_group.active_fill=value

    @property
    def value(self):
        return self.radio_group.value
    @value.setter
    def value(self,_value):
        self.radio_group.value=_value

    @property
    def items(self):
        return self.radio_group.items
    @items.setter
    def items(self,value):
        self.log('Invalid changing of Radio items',level=2)

    @property
    def enabled(self):
        return self.radio_group.enabled
    @enabled.setter
    def enabled(self,value):
        try:
            self.radio_group.enabled=value
        except Exception as e:
            self.log('failed to change radio enabled',e,level=2)

    @property
    def x(self):
        return int(self.radio_group.x)
    @x.setter
    def x(self,value):
        self.radio_group.x=value

    @property
    def y(self):
        return int(self.radio_group.y)
    @y.setter
    def y(self,value):
        self.radio_group.y=value

    @property
    def width(self):
        return self.width_from_length(
            self.radio_group.length)+2*self._font.line_space
    @width.setter
    def width(self,value):
        try:
            value=int(value)-2*self._font.line_space
        except:
            value=2*self._font.line_space
        self.radio_group.length=self.length_from_width(
            value)
    @property
    def height(self):
        return self.radio_group.height
    @height.setter
    def height(self,value):
        self.log('Illegal setting of radio height',level=2)

    def write_back(self,value):
        self.page.dispatch_radio_event(self)


class ChoiceDispThing(DispThing):
    fields=('thing','x','y','items','prompt','multiple','colour','fill','colours',
            'highlights','font','tags','width','enabled','length')
    def __init__(self, page,
                 items,
                 prompt='',
                 default=None,
                 x=None, y=None,
                 multiple=False,
                 colour=None,
                 fill=None,
                 colours=None,
                 highlights=None,
                 font=None,
                 width=None,
                 length=None,
                 enabled=True,
                 tags=[]
                 ):
        #print('CREATING ChoiceDispThing')
        if isinstance(items,str):
            items=items.split(',')
        else:
            try:
                items=[f'{item}' for item in items]
            except:
                items=[f'{items}']
        if isinstance(colours,str):
            colours=colours.split(',')
        DispThing.__init__(self,page,'choicedisp',tags)
        if x is None:
            x=page.cx
        else:
            try:
                x=int(x)
            except Exception as e:
                self.log('illegal x',e,level=2)
                x=0
        if y is None:
            y=page.cy
        else:
            try:
                y=int(y)
            except Exception as e:
                self.log('illegal y',e,level=2)
                y=0
        self._font=BubblFont(font)
        if length is None:
            length=min(10,len(items))

        self.choice_box=SelectionBox(
            self.canvas,
            x=x,
            y=y,
            items=items,
            client_handler=self._write_back,
            multi=multiple,
            colour=colour,
            fill=fill,
            colours=colours,
            highlights=highlights,
            default=default,
            title=prompt,
            length=length,
            width=width,
            enabled=enabled,
            font=font)
        self.bind_mouse_events(self.choice_box.canvas)
        self.uid=self.choice_box.uid


    @property
    def enabled(self):
        return self.choice_box.enabled
    @enabled.setter
    def enabled(self,value):
        self.choice_box.enabled=value

    @property
    def multiple(self):
        return self.choice_box.multi

    @multiple.setter
    def multiple(self,value):
        self.choice_box.multi=bool(value)

    def _write_back(self,value):
        self._value=value
        self.page.dispatch_choice_event(self)

    @property
    def value(self):
        return self._value

    @property
    def width(self):
        return self.choice_box.width
    @width.setter
    def width(self,value):
        self.log('Illegal assignment to DISPLAY choice thing width',level=2)
    @property
    def colour(self):  #to be overridden in text items
        return self.choice_box.colour
    @colour.setter
    def colour(self,value):
        self.choice_box.colour=value
    @property
    def colours(self):  #to be overridden in text items
        return self.choice_box.colours
    @colours.setter
    def colours(self,value):
        self.choice_box.colours=value
    @property
    def fill(self):  #to be overridden in text items
        return self.choice_box.fill
    @fill.setter
    def fill(self,value):
        self.choice_box.fill=value

    @property
    def highlights(self):
        return self.choice_box.highlights

    @highlights.setter
    def highlights(self,values):
        self.choice_box.highlights=values

    @property
    def height(self):
        return self.choice_box.height

    @height.setter
    def height(self,height):
        self.choice_box.height=height

    @property
    def prompt(self):
        return self.choice_box.frame["text"]
    @prompt.setter
    def prompt(self,value):
        self.choice_box.frame["text"]=f'{value}'

    @property
    def items(self):
        return self.choice_box.items
    @items.setter
    def items(self,values):
        if isinstance(values,str):
            values=values.split(',')
        self.choice_box.items=values

    @property
    def length(self):
        return self.choice_box.length
    @length.setter
    def length(self,value):
        self.choice_box.length=value

#class TextAreaDispThing(DispThing):
#    pass

class RectangleDispThing(DispThing):
    fields=('thing','x','y','tags','colour','fill','active_colour',
            'active_fill','width','height','line_width')

    def __init__(self,page,width=1,height=1,x=None,y=None,colour=None,fill='',
                 active_colour=None,active_fill=None,
                 line_width=1,tags=[]):
        DispThing.__init__(self,page,'rectangle',tags)
        #print('RECT x',x)
        if x is None:
            x=page.cx
        else:
            try:
                x=int(x)
            except Exception as e:
                self.log('illegal x',e,level=2)
                x=0
        if y is None:
            y=page.cy
        else:
            try:
                y=int(y)
            except Exception as e:
                self.log('illegal y',e,level=2)
                y=0
        try:
            width=int(width)
        except Exception as e:
            self.log('illegal width',e,level=2)
            width=1
        try:
            height=int(height)
        except Exception as e:
            self.log('illegal height',e,level=2)
            height=1
        if colour==None or colour!='' and not ui.is_safe_colour(colour):
            colour=page.ink
        if fill !='' and not ui.is_safe_colour(fill):
            fill=''

        active_colour=ui.valid_colour(active_colour,default=brighter(colour))
        active_fill=ui.valid_colour(active_fill,default=brighter(fill))

        #print('RECT x',x)
        #print('RECT y',y)
        #print('RECT width',width)
        #print('RECT height',height)
        self.uid=self.canvas.create_rectangle(x,y,x+width,y+height,
            activefill=active_fill,fill=fill,
            outline=colour,activeoutline=active_colour,
            width=line_width)

    @property
    def width(self):
        coords=self.canvas.coords(self.uid)
        return coords[2]-coords[0]
    @width.setter
    def width(self,value):
        try:
            value=int(value)
        except ValueError:
            self.log('illegal assignment to rectangle width',level=2)
            return

        coords=list(self.canvas.coords(self.uid))
        coords[2]=coords[0]+value
        self.canvas.coords(self.uid,coords)
    @property
    def height(self):
        coords=self.canvas.coords(self.uid)
        return coords[3]-coords[1]
    @height.setter
    def height(self,value):
        try:
            value=int(value)
        except ValueError:
            self.log('illegal assignment to rectangle height',level=2)
            return
        coords=list(self.canvas.coords(self.uid))
        coords[3]=coords[1]+value
        self.canvas.coords(self.uid,coords)

    @property
    def points(self):
        try:
            points=self.canvas.coords(self.uid)
            return [points[0],points[1],points[2],points[1],points[2],points[3],points[0],points[3]]
        except Exception as e:
            self.log('POINTS not there',e,level=2)
    @points.setter
    def points(self,value):
        try:
            self.canvas.coords(self.uid,value[0],value[1],value[2],value[5])
        except Exception as e:
            self.log('Illegal assignment to DISPLAY thing points',value,e,level=2)




class EllipseDispThing(DispThing):
    fields=('thing','x','y','tags','colour','fill','active_colour',
            'active_fill','width','height','line_width')
    def __init__(self,page,width=0,height=0,x=None,y=None,colour=None,fill='',
                 active_colour=None,active_fill=None, line_width=1,tags=[]):
        DispThing.__init__(self,page,'ellipse',tags)
        if x is None:
            x=page.cx
        else:
            try:
                x=int(x)
            except Exception as e:
                self.log('illegal x',e,level=2)
                x=0
        if y is None:
            y=page.cy
        else:
            try:
                y=int(y)
            except Exception as e:
                self.log('illegal y',e,level=2)
                y=0
        try:
            width=int(width)
        except Exception as e:
            self.log('illegal width',e,level=2)
            width=1
        try:
            height=int(height)
        except Exception as e:
            self.log('illegal height',e,level=2)
            height=1
        if colour==None or colour!='' and not ui.is_safe_colour(colour):
            colour=page.ink
        if fill !='' and not ui.is_safe_colour(fill):
            fill=''
        active_colour=ui.valid_colour(active_colour,default=brighter(colour))
        active_fill=ui.valid_colour(active_fill,default=brighter(fill))
        try:
            self.uid=self.canvas.create_oval(
                x,y,x+width,y+height,fill=fill,outline=colour,
                activeoutline=active_colour,activefill=active_fill,
                width=line_width)
        except Exception as e:
            self.runtime_error(f'Invalid ellipse',e)

    @property
    def width(self):
        coords=self.canvas.coords(self.uid)
        return round(coords[2]-coords[0])
    @width.setter
    def width(self,value):
        try:
            value=int(value)
        except ValueError:
            self.log('illegal assignment to ellipse width',level=2)
            return
        coords=list(self.canvas.coords(self.uid))
        coords[2]=coords[0]+value
        self.canvas.coords(self.uid,coords)
    @property
    def height(self):
        coords=self.canvas.coords(self.uid)
        return round(coords[3]-coords[1])
    @height.setter
    def height(self,value):
        try:
            value=int(value)
        except ValueError:
            self.log('illegal assignment to ellipse height',level=2)
            return
        coords=list(self.canvas.coords(self.uid))
        coords[3]=coords[1]+value
        self.canvas.coords(self.uid,coords)

    @property
    def points(self):
        return shape_points('ellipse',super().points)
    @points.setter
    def point(self,_value):
        log('Illegal setting of ellipse points',level=2)


class ArcDispThing(DispThing):
    fields=('thing','x','y','tags','colour','fill','active_colour',
            'active_fill','width','height','line_width','start','angle','style')
    def __init__(self,page,width=0,height=0,x=None,y=None,colour=None,fill='',
                 active_colour=None,active_fill=None, line_width=1,tags=[],
                 start=0,angle=90,style='pieslice'):
        DispThing.__init__(self,page,'arc',tags)
        if x is None:
            x=page.cx
        else:
            try:
                x=int(x)
            except Exception as e:
                self.log('illegal x',e,level=2)
                x=0
        if y is None:
            y=page.cy
        else:
            try:
                y=int(y)
            except Exception as e:
                self.log('illegal y',e,level=2)
                y=0
        try:
            width=int(width)
        except Exception as e:
            self.log('illegal width',e,level=2)
            width=1
        try:
            height=int(height)
        except Exception as e:
            self.log('illegal height',e,level=2)
            height=1
        try:
            start=int(start)
        except Exception as e:
            self.log('illegal start',e,level=2)
            start=0
        try:
            angle=int(angle)
        except Exception as e:
            self.log('illegal angle',e,level=2)
        if colour==None or colour!='' and not ui.is_safe_colour(colour):
            colour=page.ink
        if fill !='' and not ui.is_safe_colour(fill):
            fill=''
        active_colour=ui.valid_colour(active_colour,default=brighter(colour))
        active_fill=ui.valid_colour(active_fill,default=brighter(fill))
        try:
            self.uid=self.canvas.create_arc(x,y,x+width,y+height,fill=fill,outline=colour,
                activeoutline=active_colour,activefill=active_fill,
                start=start,extent=angle,style=style,width=line_width)
        except Exception as e:
            self.runtime_error(f'Invalid arc',e)

    @property
    def width(self):
        coords=self.canvas.coords(self.uid)
        return int(coords[2]-coords[0])
    @width.setter
    def width(self,value):
        try:
            value=int(value)
        except ValueError:
            self.log('illegal assignment to arc width',level=2)
            return
        coords=list(self.canvas.coords(self.uid))
        coords[2]=coords[0]+value
        self.canvas.coords(self.uid,coords)
    @property
    def height(self):
        coords=self.canvas.coords(self.uid)
        return int(coords[3]-coords[1])
    @height.setter
    def height(self,value):
        try:
            value=int(value)
        except ValueError:
            self.log('illegal assignment to arc height',level=2)
            return
        coords=list(self.canvas.coords(self.uid))
        coords[3]=coords[1]+value
        self.canvas.coords(self.uid,coords)

    @property
    def start(self):
        return round(float(self.canvas.itemcget(self.uid,'start')))
    @start.setter
    def start(self,value):
        try:
            self.canvas.itemcconfig(self.uid,'start',int(value))
        except Exception as e:
            self.log('illegal assignment to arc start',level=2)

    @property
    def angle(self):
        return round(float(self.canvas.itemcget(self.uid,'extent')))
    @angle.setter
    def angle(self,value):
        try:
            self.canvas.itemcconfig(self.uid,'extent',int(value))
        except Exception as e:
            self.log('illegal assignment to arc angle',level=2)

    @property
    def style(self):
        return str(self.canvas.itemcget(self.uid,'style'))


    @style.setter
    def style(self,value):
        try:
            self.canvas.itemcconfig(self.uid,'style',value)
        except Exception as e:
            self.log('illegal assignment to arc style',level=2)


    def _bb_contains_point(self,x,y):
        bbox=self.canvas.bbox(self.uid)
        #print('Line Contains_point',x,y,bbox)
        if bbox is not None:
            if x>=bbox[0] and x<=bbox[2]:
                if y>=bbox[1] and y<=bbox[3]:
                    return True
        return False

    def contains_point(self,x,y):
        if self.style=='arc':
            return self._bb_contains_point(x,y)
        return point_inside_coords(x,y,
            shape_points(self.style,
            self.canvas.coords(self.uid),
            angle=self.angle,
            start=self.start,
            coarseness=5))

    @property
    def points(self):
        return shape_points(self.style,super().points,
                            start=self.start,
                            angle=self.angle)
    @points.setter
    def point(self,_value):
        log('Illegal setting of arc points',level=2)


class ImageDispThing(DispThing):  #todo here could allow replacement and scaling of image
    fields=('thing','x','y','tags','width','height','filename','rotate','anchor','clip')
    def __init__(self,page,filename=None,x=None,y=None,width=None,height=None,
                 anchor='nw',clip=None,rotate=0,scale=None,tags=[]):
        self._clip=clip
        try:
            self._rotate=float(rotate)
        except ValueError:
            self._rotate=0

        DispThing.__init__(self,page,'image',tags)
        if width is not None:
            try:
                width=abs(int(width))
            except Exception as e:
                self.log('illegal width',e,level=2)
                width=None
        if height is not None:
            try:
                height=abs(int(height))
            except Exception as e:
                self.log('illegal height',e,level=2)
                height=None
        if isinstance(filename,BUBBLImage):
            image=filename
        elif isinstance(filename,Image.Image):
            image=get_image(image=filename,width=width,height=height,
                            clip=clip,rotate=self._rotate,scale=scale)
        else:
            image=get_image(filename,width=width,height=height,
                            clip=clip,rotate=self._rotate,scale=scale)
        self._filename=filename
        self.anchor=anchor
        if x is None:
            x=page.cx
        else:
            try:
                x=int(x)
            except Exception as e:
                self.log('illegal x',e,level=2)
                x=0
        if y is None:
            y=page.cy
        else:
            try:
                y=int(y)
            except Exception as e:
                self.log('illegal y',e,level=2)
                y=0
        if clip is not None:
            try:
                dx,dy=minxy(clip)
                x+=dx
                y+=dy
            except Exception as e:
                self.log('illegal clip',e,level=2)
                clip=None
        if image==None:
            self.uid=self.canvas.create_text(x,y,text=filename,anchor=anchor,font=BubblFont().font)
        elif isinstance(image,str):
            self.uid=self.canvas.create_text(x,y,text=image,anchor=anchor,font=BubblFont().font)
            image=None
        else:
            try:
                self.uid=self.canvas.create_image(x,y,image=image.get_image_for_canvas(),anchor=anchor)
            except Exception as e:
                self.runtime_error(f'Invalid image',e)
        self._image=image
        #log('canvas image at',canvas.coords(self.uid))

    @property
    def rotate(self):
        return self._rotate
    @rotate.setter
    def rotate(self,value):
        try:
            value=float(value)
            self._rotate=value
        except ValueError:
            self.log('invalid rotation',level=2)

    @property
    def width(self):
        if self._image is None:
            return 0
        try:
            return self._image.key[1]
        except:
            try:
                return self.image.pil_image.width
            except:
                return 0
    @width.setter
    def width(self,value):  #todo can recreate modified image here
        pass
    #def width(self,value):
    #    try:
    #        if value!=self.width:
    #            self.sx=value/self.image.width()
    #            self._geom_changed=True
    #    except:
    #        print(f'cannot set image width {self.ref}')

    @property
    def height(self):
        if self._image is None:
            return 0
        try:
            return self._image.key[2]
        except:
            try:
                return self.image.pil_image.height
            except:
                return 0
    @height.setter
    def height(self,value): #todo can recreate modified image here
        pass

    @property
    def rotate(self):
        if self._image is None:
            return 0
        try:
            return self._image.key[3]
        except:
            return 0

    @rotate.setter
    def rotate(self,value): #todo can recreate modified image here
        pass

    #    try:
    #        if value!=self.height:
    #            self.sy=value/self.image.height()
    #            self._geom_changed=True
    #    except:
    #        print(f'cannot set image height {self.ref}')

    @property
    def points(self):
        try:
            x,y=self.canvas.coords(self.uid)[:2]
            h=self.height
            w=self.width
            return x,y,x+w,y,x+w,y+h,x,y+h
        except Exception as e:
            self.log('POINTS not there',e,level=2)
    @points.setter
    def points(self,value):
        try:
            self.canvas.coords(self.uid,value[0],value[1])
        except Exception as e:
            self.log('Illegal assignment points',e,level=2)




class LineDispThing(DispThing):
    fields=('thing','x','y','tags','points','colour','active_colour',
            'line_width','joins','ends')

    def __init__(self,page,dxs=None,dys=None,x=None,y=None,colour=None,
                 active_colour=None,
                 joins='round',
                 ends='round',line_width=1,tags=[],points=None):

        #more here todo user iter( -ip (iter,iter))
        #ends butt,projecting,round
        if joins=='mitre':
            joins='miter'
        elif joins==round:
            joins='round'
        if ends==round:
            ends='round'
        DispThing.__init__(self,page,'line',tags)
        if colour==None or not ui.is_safe_colour(colour):
            colour=page.ink
        active_colour=ui.valid_colour(active_colour,default=brighter(colour))

        if points is None:
            if x is None:
                x=page.cx
            else:
                try:
                    x=int(x)
                except Exception as e:
                    self.log('illegal x',e,level=2)
                    x=0
            if y is None:
                y=page.cy
            else:
                try:
                    y=int(y)
                except Exception as e:
                    self.log('illegal y',e,level=2)
                    y=0
            points=[x,y]
            if isinstance(dxs,(int,float)):
                points.append(points[-2]+dxs)
                points.append(points[-2]+dys)
            else:
                try:
                    for dx,dy in zip(dxs,dys):
                        points.append(points[-2]+dx)
                        points.append(points[-2]+dy)
                except Exception as e:
                    self.runtime_error(f'Invalid points',e)
                    return
        try:
            self.uid=self.canvas.create_line(*points,fill=colour,
                                    activefill=active_colour,
                                    joinstyle=joins,
                                    capstyle=ends,width=line_width)
            page.cx,page.cy=self.canvas.coords(self.uid)[-2:]
        except Exception as e:
            self.runtime_error(f'Invalid line',e)


    @property
    def width(self):
        points=self.points
        return points[-2]-points[0]
    @width.setter
    def width(self,value):
        try:
            value=int(value)
        except Exception as e:
            self.log('illegal setting of line.width',e,level=2)
            return
        points=list(self.points)
        points[2]=points[0]+value
        self.points=points

    @property
    def height(self):
        points=self.points
        return points[-1]-points[1]
    @height.setter
    def height(self,value):
        try:
            value=int(value)
        except Exception as e:
            self.log('illegal setting of line.height',e,level=2)
            return
        points=list(self.points)
        points[3]=points[1]+value
        self.points=points

    @property
    def colour(self):  #to be overridden in text items
        return self.canvas.itemcget(self.uid,'fill')

    @colour.setter
    def colour(self,value):
        if value!=self.colour:
            if ui.is_safe_colour(value):
                self.canvas.itemconfig(self.uid,fill=value)

    @property
    def active_colour(self):
        return self.canvas.itemcget(self.uid,'activefill')

    @active_colour.setter
    def active_colour(self,value):
        if value!=self.active_colour:
            if value=='' or ui.is_safe_colour(value):
                self.canvas.itemconfig(self.uid,activefill=value)


    def contains_point(self,x,y):
        points=self.points
        mn=min(points[i] for i in range(0,len(points),2))
        mx=max(points[i] for i in range(0,len(points),2))
        if x<mn or x>mx:
            return False
        mn=min(points[i] for i in range(1,len(points),2))
        mx=max(points[i] for i in range(1,len(points),2))
        return y>=mn and y<=mx

class PolygonDispThing(DispThing):
    fields=('thing','x','y','tags','points','colour','fill','active_colour',
            'active_fill','line_width','joins')

    def __init__(self,page,dxs=None,dys=None,points=None,
                 x=None,y=None,colour=None,
                 fill='',
                 active_colour=None,active_fill=None,tags=[],joins='bevel',
                 line_width=1):
        if points is None:
            if x is None:
                x=page.cx
            else:
                try:
                    x=int(x)
                except Exception as e:
                    self.log('illegal x',e,level=2)
                    x=0
            if y is None:
                y=page.cy
            else:
                try:
                    y=int(y)
                except Exception as e:
                    self.log('illegal y',e,level=2)
                    y=0
            points=[x,y]
            for dx,dy in zip(dxs,dys):
                points.append(points[-2]+dx)
                points.append(points[-2]+dy)

        if joins=='mitre':
            joins='miter'
        elif joins==round:
            joins='round'
        DispThing.__init__(self,page,'polygon',tags)


        #print('JOINS',f'>{joins}<')
        if colour==None or colour!='' and not ui.is_safe_colour(colour):
            colour=page.ink
        if fill !='' and not ui.is_safe_colour(fill):
            fill=''
        active_colour=ui.valid_colour(active_colour,default=brighter(colour))
        active_fill=ui.valid_colour(active_fill,default=brighter(fill))

        if not all(isinstance(point,int) for point in points):
            self.uid.self.canvas.create_text(
                page.cx,page.cy,
                text=f'invalid polygon:{points}',
                anchor='nw')
            self.log('Invalid polygon',points,level=2)
        else:
            self.uid=self.canvas.create_polygon(*points,
                                       outline=colour,
                                       fill=fill,
                                       activeoutline=active_colour,
                                       activefill=active_fill,
                                       joinstyle=joins,
                                       width=line_width)
        if isinstance(x,(int,float)):
            self.x=int(x)
        if isinstance(y,(int,float)):
            self.y=int(y)

        #print('POLYGON OK SO FAR')

    @property
    def x(self):
        try:
            points=self.points
            return round(min(points[i] for i in range(0,len(points),2)))
        except Exception as e:
            self.runtime_error('Cannot read polygon x',e)
        #print('POLYGONDISPTHING points=',points)
        #        return round(points[0])

    @x.setter
    def x(self,value):
        dx=value-self.x
        if dx==0:
            return
        self.canvas.move(self.uid,dx,0)

    @property
    def y(self):
        try:
            points=self.points
            return round(min(points[i] for i in range(1,len(points),2)))
        except Exception as e:
            self.runtime_error('Cannot read polygon y',e)

        #print('POLYGONDISPTHING points=',points)
            return round(points[1])
    @y.setter
    def y(self,value):
        dy=value-self.y
        if dy==0:
            return
        self.canvas.move(self.uid,0,dy)

    @property
    def width(self):
        points=self.points
        mn=min(points[i] for i in range(0,len(points),2))
        mx=max(points[i] for i in range(0,len(points),2))
        return round(mx-mn)
    @width.setter
    def width(self,value):
        self.log('ILLEGAL setting of polygon width',level=2)

    @property
    def height(self):
        points=self.points
        mn=min(points[i] for i in range(1,len(points),2))
        mx=max(points[i] for i in range(1,len(points),2))
        return round(mx-mn)
    @height.setter
    def height(self,value):
        self.log('ILLEGAL setting of polygon height',level=2)

    def contains_point(self,x,y):
        return point_inside_coords(x,y,self.points)


thing_map={
    'text':TextDispThing,
    'button':ButtonDispThing,
    'scrollbar':ScrollbarDispThing,
    'input':InputDispThing,
    'texted':TextEdDispThing,
    'checkbox':CheckboxDispThing,
    'radio':RadioDispThing,
    'choicedisp':ChoiceDispThing,
    'rectangle':RectangleDispThing,
    'ellipse':EllipseDispThing,
    'arc':ArcDispThing,
    'image':ImageDispThing,
    'line':LineDispThing,
    'polygon':PolygonDispThing,
}
gr_things=set(('text','rectangle','ellipse',
              'arc','image','line','polygon'))