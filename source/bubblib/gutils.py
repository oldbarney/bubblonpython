"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import io
import subprocess
import sys
import tempfile
import zipfile
import math
from ast import literal_eval
from tkinter.ttk import Scrollbar

#from yt_dlp.utils import value

from .uiserver import ui
import base64
from io import BytesIO
from PIL import ImageColor, Image, ImageDraw, ImageTk, ImageGrab  # , ImageOps
#Could drop ImageColor
from tkinter import font,Canvas

from bubblib.globaldefs import render_defaults
from bubblib.base64icons import icons as bubbl_icons

paper_size_map={'A5':(421,595),
            'B5':(499,709),
            'A4':(595,842),
            'B4':(709,1002),
            'A3':(842,1191),
            'B3':(1001,1418),
            'A2':(1191,1684),
            'letter':(612,792),
            'legal':(612,1008),
            }

ext_map={'.jpg':'image',
         '.jpeg':'image',
         '.gif':'image',
         '.png':'image',
         '.txt':'page',
         '':'page',
         '.wav':'playsound',
         '.flac':'playsound',
         '.mp3':'playsound',
         '.mp4':'playsound',
         '.mpg':'playvideo',
         '.mpeg':'playvideo',
         '.mov':'playvideo',
         '.dv':'playvideo',
         '.webm':'playvideo',
         '.flv':'playvideo',
         '.ogg':'playvideo',
         '.htm':'www',
         '.html':'www',
         '.py':'python',
         '.c':'svars',
         '.cpp':'svars',
         'pdf':'output',
         }
ui=ui   #just to prevent IDE from removing uiserver import
icons={}
small_icons={}



"""
if sys.platform.startswith('win'):
    This function requires the _imagingft  service.

    :param font: A filename or file - like  object containing    a
    TrueType font. If the file is not found in this filename, the
    loader may also search in other directories, such as:
        *The: file:`fonts / ` directory on Windows,
        *:file: ` / Library / Fonts / `,:file: ` / System / Library / Fonts / `
        and:file: `~ / Library / Fonts / ` on  macOS.
        *:file: `~ /.local / share / fonts`,: file:` / usr / local / share / fonts
            `, and:file: ` / usr / share / fonts` on Linux; or those
    
    :param size: The requested  size, in pixels.
    :param index: Which font face to load(default is first available face).
"""

def icon_for_ext(ext,small=False):
    if small:
        if ext in ext_map:
            return small_icons[ext_map[ext]]
        return small_icons['']
    else:
        if ext in ext_map:
            return icons[ext_map[ext]]
        return icons['']

def alt(tkevent):
    return bool(tkevent.state &0x8)

def ctrl(tkevent):
    return bool(tkevent.state &0x4)

def shift(tkevent):
    return bool(tkevent.state &0x1)

def alt_gr(tkevent):
    return bool(tkevent.state & 0x80)

def darker(colour,by_factor=0.7):
    try:
        if len(colour)==4:
            r,g,b= [int(c,16)*17 for c in colour[1:]]
        else:
            r,g,b= [int(colour[i:i+2], 16) for i in (1, 3, 5)]
        return f'#{round(r*by_factor):02x}{round(g*by_factor):02x}{round(b*by_factor):02x}'
    except:
        return '#888'

def point_inside_coords(x,y,coords):
    inside=False
    if not isinstance(coords[0],(tuple,list)):
        coords=[(x,y) for i,(x,y) in enumerate(zip(coords,coords[1:])) if i % 2==0]
    x2,y2=coords[-1]

    for x1,y1 in coords:
        if (x == x1) and (y == y1):
            return True
        if (y1 > y) != (y2 > y):  #is y between y1 and y2
            gradient = (x - x1) * (y2 - y1) - (x2 - x1) * (y - y1)
            if gradient == 0:
                return True
            if (gradient < 0) != (y2 < y1):
                inside=not inside
        x2,y2=x1,y1
    return inside

def xywh_from_geom(geom):
    #get width,height,x,y from tkinter geom, not including rel to right-hand edge of
    parts=geom.split('+')
    if len(parts)!=3:
        return 0,0,640,480
    x=round(float(parts[1]))
    y=round(float(parts[2]))
    w,h=parts[0].split('x')
    return x,y,round(float(w)),round(float(h))

def ensure_top_level_on_screen(window):
    geom=xywh_from_geom(window.geometry())
    #print('ensure on screen',geom)
    #print('width',window.winfo_width())
    dx=window.winfo_screenwidth()-geom[2]-geom[0]
    dy=window.winfo_screenheight()-geom[3]-geom[1]
    #print('dx,dy',dx,dy)
    if dx<0 or dy<0:
        #print('new geom',f'{geom[2]}x{geom[3]}+{geom[0]+dx}+{geom[1]+dy}')
        window.geometry(f'{geom[2]}x{geom[3]}+{geom[0]+dx}+{geom[1]+dy}')

def colour(arg, alpha=255):
    try:
        return Colour(ImageColor.colormap[arg],alpha)
    except:
        try:
            return Colour(arg,alpha)
        except:
            return '#000'

def ghostscript_command():
    if sys.platform.startswith('win32'):
        return ['gswin32c','-dBATCH', '-sDEVICE=pdfwrite', '-dEPSCrop','-o']
    elif sys.platform.startswith('win64'):
        return ['gswin64c', '-dBATCH', '-sDEVICE=pdfwrite', '-dEPSCrop','-o']
    else:
        return ['gs','-dBATCH', '-sDEVICE=pdfwrite', '-dEPSCrop','-o']


def canvas_to_PIL_image(canvas,monochrome=False,background=False):
    canvas.update()
    width=canvas.winfo_width()


    pars={}
    if monochrome:
        pars['colormode']='gray'
    else:
        pars['colormode']='color'
    pars['pagewidth'] = width
    pars['pageanchor'] = 'nw'

    pars['pagex']=0
    pars['pagey']=0
    ps=canvas.postscript(**pars)
    ramfile=io.BytesIO(ps.encode())

    #print('SAVING CANVAS ramfile',ramfile)
    image = Image.open(ramfile)
    image.load(transparency=not background)
    return image


def save_canvas_message(
        canvas,
        filename,
        landscape=False,
        monochrome=False,
        left_margin=0,
        top_margin=0,
        paper_size=None
    ):
    """
        Print the contents of the canvas to a postscript or image file
file. Valid options: colormap, colormode, file, fontmap,
height, pageanchor, pageheight, pagewidth, pagex, pagey,
rotate, width, x, y.
       """
    canvas.update()
    width=canvas.winfo_width()
    pagewidth=int(width/ui.ppp)

    if paper_size is not None:
        try:
            pagewidth,_pageheight=paper_size_map[paper_size]
        except:
            pass

    pars={}
    if monochrome:
        pars['colormode']='gray'
    else:
        pars['colormode']='color'
    pars['pagewidth'] = pagewidth
    pars['pageanchor'] = 'nw'

    pars['pagex']=left_margin
    pars['pagey']=top_margin
    if landscape:
        pars['rotate']=True
    ps=canvas.postscript(**pars)
    if filename.split('.')[-1].lower() in ('eps','ps'):
        try:
            with open(filename,'wb') as f:
                f.write(ps.encode())
            return 'Ok'
        except Exception as e:
            return f'{e}'
    if filename.lower().endswith('.pdf'):
        temp=tempfile.gettempdir()+'/bubbl.eps'
        #print('TEMPFILE',temp)
        try:
            with open(temp,'wb') as f:
                f.write(ps.encode())
            result = subprocess.run(ghostscript_command()+[filename,temp])
            if result.returncode==0:
                return 'Ok'
            else:
                return 'Failed to create '+filename+' with ghostscript'
        except Exception as e:
            return f'{e}'
    ramfile=io.BytesIO(ps.encode())

    #print('SAVING CANVAS ramfile',ramfile)
    png=filename.lower().endswith('.png')
    try:
        image = Image.open(ramfile)
        #print('IMAGE',image)
        image.load(transparency=png)

        #print('image loaded')
    except Exception as e:
        #print('Failed to open IMAGE',e)
        return f'Failed to save image:{e}'
    try:
        image.save(filename)
        return 'Ok'
    except Exception as e:
        return f'{e}'

class AutoScrollbar(Scrollbar):

    # Defining set method with all
    # its parameter
    def set(self, low, high):
        if float(low) <= 0.0 and float(high) >= 1.0:
           # Using grid_remove
            self.tk.call("grid", "remove", self)
        else:
            try:
                self.grid()
            except:
                pass
        Scrollbar.set(self, low, high)

class Colour:
    def __init__(self,spec,alpha=None):
        if isinstance(spec,Colour):
            self._int=spec._int
            self._array=spec._array
            return

        if isinstance(spec,(tuple,list)):
            if len(spec)==3:
                self._array=list(spec)+[255]
            else:
                self._array=spec
            self._int=None
        elif isinstance(spec,int):
            self._int=spec
            self._array=[spec>>16 &255,spec>>8&255,spec*255,255-(spec>>24&255)]
        elif isinstance(spec,str):
            try:
                spec= ImageColor.colormap[spec]
            except:
                pass
            try:
                value=int(spec[1:],base=16)
            except:
                value=0
            if len(spec)==7:
                self._array=[(value>>16)&0xff,(value>>8)&0xff,value & 0xff,255 if alpha is None else alpha]
                self._int=value
            else:
                self._array=[(value>>4)&0xf0,value&0xf0,(value<<4) & 0xf0,255 if alpha is None else alpha]
                self._int=None
        else:
            self._array=[0,0,0,255]

    @property
    def rgb(self):
        if self._int is None:
            [r,g,b,a]=self._array
            self._int=((255-a)<<24)+(r<<16)+(g<<8)+b
            return self._int&0xFFFFFF

    @rgb.setter
    def rgb(self,value):
        self._int=value
        self._array=[value>>16 &255,value>>8&255,value*255,(value>>24&255)^255]

    @property
    def rgba(self):
        if self._int is None:
            [r,g,b,a]=self._array
            self._int=(a<<24)+(r<<16)+(g<<6)+b
        return self._int
    @rgba.setter
    def rgba(self,value):
        self._int=value^0xFF000000
        self._array=[value>>16 &255,value>>8&255,value*255,value>>24]

    @property
    def red(self):
        return self._array[0]
    @red.setter
    def red(self,value):
        self._array[0]=int(value)&0xFF
        self._int=None
    @property
    def green(self):
        return self._array[1]
    @green.setter
    def green(self,value):
        self._int=None
        self._array[1]=int(value)&0xFF
    @property
    def blue(self):
        return self._array[2]
    @blue.setter
    def blue(self,value):
        self._int=None
        self._array[2]=int(value)&0xFF
    @property
    def alpha(self):
        return self._array[3]
    @alpha.setter
    def alpha(self,value):
        self._array[3]=int(value)&0xFF
        self._int=None

    def __str__(self):
        return self.string()

    def string(self):
        [r,g,b,_]=self._array
        return f'#{r:02X}{g:02X}{b:02X}'

    def to_list(self):
        return self._array

def get_contrasting_colour(colour:Colour):
    result=Colour(colour)
    result.red=(result.red+70)%256
    result.green=(result.green+170)%256
    result.blue=(result.blue+70)%256
    return result

def get_text_rect(font,text,gridsize):
    metrics=font.metrics()
    h=metrics['linespace']+2
    w=font.measure(text)+2+gridsize
    h=max(h,gridsize)
    return (0,0,w,h)

def _darker(colour):
    result=Colour(colour)
    result.red=2*result.red//3
    result.green=2*result.green//3
    result.blue=2*result.blue//3
    return result

def brighter(colour):
    if colour=='':
        return ''
    result=Colour(colour)
    #input=Colour(colour)

    #print('input colour',colour)

    result.red=255-(255-result.red)//2
    result.green=255-(255-result.green)//2
    result.blue=255-(255-result.blue)//2

    #input.to_list()
    #print('brighter than',input.__repr__(),'is',result.__repr__())


    return result



universal_fonts=['TkDefaultFont',
                 'TkTextFont',
                 'TkFixedFont',
                 'TkMenuFont',
                 'TkHeadingFont',
                 'TKCaptionFont',
                 'TkSmallCaptionFont',
                 'TkIconFont',
                 'TkTooltipFont']

truetype_fonts=[
    'DejaVuSans',
    'DejaVuSansMono',
    'DejaVuSerif',
    'FreeFontMono',
    'FreeMono',
    'FreeSans',
    'FreeSerif',
    'LiberationSans-Regular',
    'LiberationMono-Regular',
    'LiberationSerif-Regular',
]

main_fonts=['Courier','Times','Helvetica']

font_family_map={None: 'Helvitica',
          'sanserif':'Helvetica',
          'serif':'Times',
          'mono':'Courier',
          'Sanserif':'Helvetica',
          'Serif':'Times',
          'Mono':'Courier'
                 }
def pixels_for_length(length,font):
    return font.measure('0')*length

def length_for_pixels(width,font):
    return int(width/font.measure('0'))

def cropped_string(text,width,font,grid_size):
    if width<grid_size:
        return '...'

    m=font.measure(text)
    if m>width-4:
        return text[:round((width-15)/m*len(text))]+'..'
    return text
    if font.measure(text)>width-4:
        end=width-font.measure('..')-4
        text=text[:-2]
        while font.measure(text)>end and text!='':
            text=text[:-1]
        return text+'..'
    return text


font_cache={}
#last_fs=


def _get_font(value='TkDefaultFont,10',update_cache=True,return_key=False):
    #print('get_font from:',value)
    if value in font_cache:
        #print('returning font from cache')
        if return_key:
            return font_cache[value],value
        return font_cache[value]

    if ':' in value:
        vals=value.split(':')
    else:
        vals=value.split(',')
    qual=set(vals[1:])
    family=vals[0]
    if family in font_family_map:
        family=font_family_map[family]
    size=10
    for p in qual:
        try:
            size=int(p)
            break
        except:
            pass
    key=f'{family},{size}'
    options={}
    if 'b' in qual:
        options['weight']="bold"
        key+=',b'
    if 'i' in qual:
        options['slant']="italic"
        key+=',i'
    if key in font_cache:
        if return_key:
            return font_cache[key],key
        return font_cache[key]

    #print('Get font- family:',family,'size:',size,'options',options)

    try:
        result=font.Font(family=family,size=ui.scaled_font_size(size),**options)
    except Exception as e:
        result=_get_font(render_defaults.font,update_cache=False)
    if update_cache:
        font_cache[key]=result
    if return_key:
        return result,key
    else:
        return result

simple_cursors =[
        "arrow",
        "circle",
        "clock",
        "cross",
        "dotbox",
        "exchange",
        "fleur",
        "heart",
        "man",
        "mouse",
        "pirate",
        "plus",
        "shuttle",
        "sizing",
        "spider",
        "spraycan",
        "star",
        "target",
        "tcross",
        "trek"
]
cursors= [
'arrow',
'based_arrow_down',
'based_arrow_up',
'boat',
'bogosity',
'bottom_left_corner',
'bottom_right_corner',
'bottom_side',
'bottom_tee',
'box_spiral',
'center_ptr',
'circle',
'clock',
'coffee_mug',
'cross',
'cross_reverse',
'crosshair',
'diamond_cross',
'dot',
'dotbox',
'double_arrow',
'draft_large',
'draft_small',
'draped_box',
'exchange',
'fleur',
'gobbler',
'gumby',
'hand1',
'hand2',
'heart',
'icon',
'iron_cross',
'left_ptr',
'left_side',
'left_tee',
'leftbutton',
'll_angle',
'lr_angle',
'man',
'middlebutton',
'mouse',
'pencil',
'pirate',
'plus',
'question_arrow',
'right_ptr',
'right_side',
'right_tee',
'rightbutton',
'rtl_logo',
'sailboat',
'sb_down_arrow',
'sb_h_double_arrow',
'sb_left_arrow',
'sb_right_arrow',
'sb_up_arrow',
'sb_v_double_arrow',
'shuttle',
'sizing',
'spider',
'spraycan',
'star',
'target',
'tcross',
'top_left_arrow',
'top_left_corner',
'top_right_corner',
'top_side',
'top_tee',
'trek',
'ul_angle',
'umbrella',
'ur_angle',
'watch',
'xterm']

def shape_points(shape_type,points,start=0,angle=90,coarseness=1):
    """ return polygon points for
        'pieslice(x1,y1,','chord','rect',or 'ellipse'
    """
    if shape_type=='rect':
        return [points[0],points[1],points[2],points[1],points[2],points[3],points[0],points[3]]
    elif shape_type=='ellipse':
        x1,y1,x2,y2=points
        x1,x2=min(x1,x2),max(x1,x2)
        y1,y2=min(y1,y2),max(y1,y2)

        if x2-x1<2 or y2-y1<2:
            return x1,y1,x2,y2
        rx=(x2-x1)/2
        ry=(y2-y1)/2
        da=round(max(1,1720/(rx+ry)))
        points=[]
        for a in range(0,360,da):
            points.append(round(rx*math.cos(a/180*math.pi)+x1+rx))
            points.append(round(ry*math.sin(a/180*math.pi)+y1+ry))
        return points
    elif shape_type in ('arc','pieslice','chord'):
        x1,y1,x2,y2=points
        x1,x2=min(x1,x2),max(x1,x2)
        y1,y2=min(y1,y2),max(y1,y2)
        if x2-x1<2 or y2-y1<2:
            return x1,y1,x2,y2

        rx=(x2-x1)/2
        ry=(y2-y1)/2
        cx=x1+rx
        cy=y1+ry

        da=round(max(1,1720*coarseness/(rx+ry)))
        points=[round(rx*math.cos(start/180*math.pi)+cx),
                round(-ry*math.sin(start/180*math.pi)+cy)]
        for a in range(round(start)+da//3,round(start)+angle-da//3,da):
            points.append(round(rx*math.cos(a/180*math.pi)+cx))
            points.append(round(-ry*math.sin(a/180*math.pi)+cy))
        points.append(round(rx*math.cos((start+angle)/180*math.pi)+cx))
        points.append(round(-ry*math.sin((start+angle)/180*math.pi)+cy))
        if shape_type=='pieslice':
            points.append(round(cx))
            points.append(round(cy))
        return points

def minxy(points):
    if isinstance(points[0],(int,float)):
        mnx=round(min(points[i] for i in range(0,len(points),2)))
        mny=round(min(points[i] for i in range(1,len(points),2)))
        return mnx,mny
    mnx=round(min(p[0] for p in points))
    mny=round(min(p[1] for p in points))
    return mnx,mny

def maxxy(points):
    if isinstance(points[0],(int,float)):
        mxx=round(max(points[i] for i in range(0,len(points),2)))
        mxy=round(max(points[i] for i in range(1,len(points),2)))
        return mxx,mxy
    mxx=round(max(p[0] for p in points))
    mxy=round(max(p[1] for p in points))
    return mxx,mxy

def bbox(points):
    mnx=min(p[0] for p in points)
    mny=min(p[1] for p in points)
    mxx=max(p[0] for p in points)
    mxy=max(p[1] for p in points)
    return mnx,mny,mxx,mxy

#def flattened(points):
#    if points is None:
#        return None
#   if isinstance(points[0],int):
#        return tuple(points)
#    if isinstance(points[0],float):
#        return tuple(round(p) for p in points)
#    result=[]
#    for p in points:
#        result.append(round(p[0]))
#        result.append(round(p[1]))
#    return tuple(result)

def paired(points):
    if points is None:
        return None
    if isinstance(points[0],int):
        return tuple((points[i],points[i+1]) for i in range(0,len(points),2))
    if isinstance(points[0],float):
        return tuple((round(points[i]),round(points[i+1])) for i in range(0,len(points),2))
    if isinstance(points[0][0],int):
        return tuple(tuple(p) for p in points)
    return tuple((round(p[0]),round(p[1])) for p in points)

def translated(points,dx,dy):
    return tuple((x+dx,y+dy) for (x,y) in points)

class BubblFont:
    def __init__(self,font_spec=None):
        if isinstance(font_spec,BubblFont):
            self.font=font_spec.font
            self.key=font_spec.key
            return

        if font_spec is None:
            font_spec='TkDefaultFont,10'

        #print('font_spec',font_spec)
        #print('Type of font_spec is',type(font_spec))

        if not isinstance(font_spec,str):
            font_spec='TkDefaultFont,10'

        fnt,key=_get_font(font_spec,return_key=True)
        self.font=fnt
        self.key=key

    def __str__(self):
        return self.key

    @property
    def family(self):
        return self.key.split(',')[0]
    @property
    def point_size(self):
        return int(self.key.split(',')[1])
    @property
    def italic(self):
        return 'i' in self.key.split(',')
    @property
    def bold(self):
        return 'b' in self.key.split(',')
    @property
    def line_space(self):
        return self.font.metrics('linespace')
    def width(self,text):
        return self.font.measure(text)
    def to_tuple(self):
        return (self.font.actual()['family'],self.font.actual()['size'])

    def cropped(self,text,width,min_width=18):
        if width<min_width:
            return '...'
        m=self.font.measure(text)
        if m>width-4:
            return text[:round((width-15)/m*len(text))]+'..'
        return text

    def get_bold(self):
        if self.font.actual()['weight']=='bold':
            return self.font
        return BubblFont(self.key+',b').font

image_cache={}

def clear_image_cache():
    for i in image_cache.items:
        i.close()
    image_cache.clear()

photo_image_cache={}

def get_cached_image(key,maker):
    if key in image_cache:
        return image_cache[key]
    try:
        result=maker()
        image_cache[key]=result
        return result
    except Exception as e:
        return f'failed to make image:{e}'

def get_cached_photo_image(key,image):
    if key is not None and key in photo_image_cache:
        return photo_image_cache[key]
    else:
        try:
            result=ImageTk.PhotoImage(image)
            if key is not None:
                photo_image_cache[key]=result
            return result
        except Exception as e:
            return f'failed to make image image:{key}:{e}'

class BUBBLImage:
    """ Wrapper class for PIL images, using caches to
    limit loading and rescaling opertations"""
    def __init__(self,pil_image,key=None):
        self._pil_image=pil_image
        self.key=key
        self.tk_image=None
        self.error_message='Ok'
    def get_image_for_canvas(self):
        if self.tk_image is None:
            self.tk_image=get_cached_photo_image(self.key,self.pil_image)
        return self.tk_image
    def ok_save_to_file(self,filename):
        try:
            self.pil_image.save(filename)
            self.error_message='Ok'
            return True
        except Exception as e:
            self.error_message=f'{e}'
            return False
    def to_base64(self,format='PNG'):
        data=BytesIO()
        self.pil_image.save(data,format=format)
        result=base64.b64encode(data.getvalue())
        return result.decode()

    @property
    def pil_image(self):
        return self._pil_image
    @pil_image.setter
    def pil_image(self,value):
        if not isinstance(value,Image.Image):
            return
        try:
            self.tk_image=None
            photo_image_cache.pop(self.key)
        except KeyError:
            pass
        self._pil_image=value

def flush_image_cache():
    for key in image_cache:
        if isinstance(key,str):
            image_cache[key].close()
    image_cache.clear()

def grab_image_from_screen(rect=None,poly=None):
    if rect is not None:
        return get_image(image=ImageGrab.grab(rect))
    else:
        x1,y1=minxy(poly)
        x2,y2=maxxy(poly)
        return get_image(clip=tuple((p[0]-x1,p[1]-y1) for p in poly),
                         image=ImageGrab.grab((x1,y1,x2,y2)))

def get_image(filename=None,
              width=0,
              height=0,
              scale=None,
              rotate=0,
              clip=None,
              image=None,
              transform=None,
              base64_data=None,
              formats=('PNG',)): #here todo close image from open
    """Return BUBBLImage"""
    if filename is not None and isinstance(filename,str):
        if filename.startswith('base64:'):
            base64_data=filename[7:]
        elif '_pg.icons[' in filename:
            try:
                [ref]=literal_eval(filename.strip()[9:])
                base64_data=bubbl_icons[ref]
            except:
                pass
    if base64_data is not None:
        try:
            data=BytesIO(base64.b64decode(base64_data))
            def get_image_from_b64():
                return Image.open(data,'r',formats=formats)
            image=get_cached_image(filename,get_image_from_b64)
            if isinstance(image,str):
                return image
        except Exception as e:
            return f'Failed to set up base64 image decode: {e}'
    elif image is None:
        if isinstance(filename,str):
            parts=filename.split(',')
            if len(parts)==2:
                zip,key=parts
                def get_image_from_zip():
                    try:
                        with zipfile.ZipFile(zip,'r') as f:
                            return Image.open(f.open(key))
                    except Exception as e:
                        return f'Failed to load image from zip file:{e}'
                image=get_cached_image(filename,get_image_from_zip)
            else:
                image=get_cached_image(filename,lambda filename=filename: Image.open(filename))
            if isinstance(image,str):
                return image
    if image is None:
        return None

    if scale is not None:
        if isinstance(scale,tuple):
            width=round(image.width*scale[0])
            height=round(image.height*scale[1])
        else:
            width=round(image.width*scale)
            height=round(image.height*scale)
    else:
        if not width:
            if not height:
                width=image.width
                height=image.height
            else:
                try:
                    width=round(image.width*height/image.height)
                except ZeroDivisionError:
                    return None
        elif not height:
            try:
                height=round(image.height*width/image.width)
            except ZeroDivisionError:
                return None
    #print('before',clip)
    clip=paired(clip)
    #print('after',clip)
    key=(filename,width,height,rotate,clip)
    if width!=image.width or height!=image.height:
        image=get_cached_image(key,lambda image=image:image.resize((width,height),resample=Image.Resampling.BICUBIC,reducing_gap=3))
    if rotate:
        #image.putalpha(0xFF)
        if image.mode!='RGBA':
            image=image.convert('RGBA')
        image=image.rotate(angle=rotate,expand=True,resample=Image.Resampling.BICUBIC)#,fillcolor='#000000FF')

    if clip is not None:
        x1,y1,x2,y2=box=bbox(clip)
        image=image.crop(box)
        poly=translated(clip,-x1,-y1)
        #print('poly',poly)
        mask=Image.new('L',(x2-x1,y2-y1))
        ImageDraw.Draw(mask).rectangle((0,0,x2-x1,y2-y1),fill='#000000FF')
        ImageDraw.Draw(mask).polygon(poly,fill='#FFFFFF')
        image.putalpha(mask)
    return BUBBLImage(image,key)


    """
    return get_cached_photo_image(key,image)
    source_im=Image.open('test.jpg')
    poly = [(1000,1000),(1500,750),(1600,1770),(1300,2000),(900,1300)]
    x1,y1,x2,y2=box=bbox(poly)
    tx_poly=translated(poly,-x1,-y1)
    boxed_im=source_im.crop(box)
    # Convert to grayscale
    mask = Image.new('L',(x2-x1,y2-y1))
    #source_im.close()
    #result=crop image to bbox of poly
    #translate poly to origin
    #create mask bbox size
    #fill maxk with alpha0
    #draw translated poly on mask
    #result.putalpha from mask
    #return result
    ImageDraw.Draw(mask).rectangle((0,0,x2-x1,y2-y1),fill='#000000FF')
    #ImageDraw.Draw(mask).rectangle((0,0,source_im.width,source_im.height),fill='#000000FF')
    print('tx_poly',tx_poly)
    ImageDraw.Draw(mask).polygon(tx_poly,fill='#FFFFFF')
    #ImageDraw.Draw(mask).polygon(poly,fill='#FFFFFF')
    mask.save('crop.png')
    # The size of the images must match before apply the mask
    #img = ImageOps.fit(source_im,mask.size)
    img = ImageOps.fit(boxed_im,mask.size)
    img.putalpha(mask) # Modifies the original image without return
    img.save('croppeda.png')
    img=img.rotate(angle=45,expand=True,fillcolor='#00000000')
    img.save('croppedb.png')
    print('done')
    source_im.close()
"""

def image_with_alpha_to_background(image, background='#FFF'):
    result=Image.new('RGBA', (image.width,image.height), background)
    result.paste(image)
    result=result.convert('RGB')
    return result

#Image.open().putalpha()

def binary_file_to_base64_str(filename):
    with open(filename, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')

def save_base64_str_to_binary_file(base64_data,filename):
    with open(filename,'wb') as f:
        data=base64.b64decode(base64_data.encode('utf-8'))
        f.write(data)

def icon(key,icon_size=20):
    if icon_size==20:
        try:
            return icons[key]
        except:
            image=get_image(filename=key,
                            base64_data=bubbl_icons[key]
            ).pil_image.resize((20,20))
            icons[key]=ImageTk.PhotoImage(image,size='20x20')
            return icons[key]
    elif icon_size==13:
        return small_icon(key)

    image=get_image(
        key,base64_data=bubbl_icons[key]
    ).pil_image.resize((icon_size,icon_size))
    return ImageTk.PhotoImage(image,size=f'{icon_size}x{icon_size}')

def small_icon(key):
    try:
        return small_icons[key]
    except:
        image=get_image(
            key,base64_data=bubbl_icons[key]
        ).pil_image.resize((13,13))
        small_icons[key]=ImageTk.PhotoImage(image,size='13x13')
        return small_icons[key]

full_image_cache={}

def full_icon(key,width,height):
    try:
        return full_image_cache[key]
    except KeyError:
        pass
    image = get_image(filename=key,
                      base64_data=bubbl_icons[key]
                      ).pil_image.resize((width,height))
    full_image_cache[key]=result=ImageTk.PhotoImage(image)
    return result



"""
def get_image(filename,width=None,height=None,crop=None):
    result=get_scaled_image(filename,width=width,height=height)
    if crop is None:
        return ImageTk.PhotoImage(result)

    pass

image_cache={}
resized_image_cache={}

def get_scaled_image(filename,width=None,height=None):
    try:
        image=image_cache[filename]
    except KeyError:
        image=Image.open(filename)
        image_cache[filename]=image

    if width is None and height is None:
        key=(filename,image.width,image.height)
        try:
            return resized_image_cache[key]
        except KeyError:
            result=resized_image_cache[key]=image
            return result
    else:
        if width is None:
            width=round(image.width*height/image.height)
        elif height is None:
            height=round(image.height*width/image.width)
        key=(filename,width,height)
        #try:
        #    return resized_image_cache[key]
        #except KeyError:
        image=image.resize((width,height))
        result=resized_image_cache[key]=image
        return result

def get_uncropped_image(filename,width=None,height=None):
    try:
        image=image_cache[filename]
    except KeyError:
        image=Image.open(filename)
        image_cache[filename]=image

    if width is None and height is None:
        key=(filename,image.width,image.height)
        try:
            return resized_image_cache[key]
        except KeyError:
            result=resized_image_cache[key]=ImageTk.PhotoImage(image)
            return result
    else:
        if width is None:
            width=round(image.width*height/image.height)
        elif height is None:
            height=round(image.height*width/image.width)
        key=(filename,width,height)
        #try:
        #    return resized_image_cache[key]
        #except KeyError:
        image=image.resize((width,height))
        result=resized_image_cache[key]=ImageTk.PhotoImage(image)
        return result




# read image as RGB and add alpha (transparency)

#image=Image.open(file)
def cropped_image(image,polygon):
    im = image.convert("RGBA")
    im_array = numpy.asarray(im)
    mask_im = Image.new('L', (im_array.shape[1], im_array.shape[0]), 0)
    ImageDraw.Draw(mask_im).polygon(polygon, outline=1, fill=1)
    mask = numpy.array(mask_im)
    # assemble new image (uint8: 0-255)
    new_im_array = numpy.empty(im_array.shape,dtype='uint8')
    # colors (three first columns, RGB)
    new_im_array[:,:,:3] = im_array[:,:,:3]
    # transparency (4th column)
    new_im_array[:,:,3] = mask*255

# back to Image from numpy
    newIm = Image.fromarray(new_im_array, "RGBA")
    newIm.save("out.png")
"""













'''
from PIL import Image, ImageDraw
blank_image = Image.new('RGBA', (100, 40), (255,255,255,0))
img_draw = ImageDraw.Draw(blank_image)
img_draw.rectangle((0, 0, 100, 40), outline='red', fill='#AFF')
img_draw.text((0,0), 'Hello World',fill='black')
blank_image.save('drawn_image.png')
'''
"""

def get_image(width,height,backgound,text_lines,font):
    im=Image.new("RGBA", (width, height))
    f=ImageFont.
    ps=PSDraw.PSDraw(im.




with Image.open("hopper.ppm") as im:
    title = "hopper"
    box = (1 * 72, 2 * 72, 7 * 72, 10 * 72)  # in points

    ps = PSDraw.PSDraw()  # default is sys.stdout or sys.stdout.buffer
    ps.begin_document(title)

    # draw the image (75 dpi)
    ps.image(box, im, 75)
    ps.rectangle(box)

    # draw title
    ps.setfont("HelveticaNarrow-Bold", 36)
    ps.text((3 * 72, 4 * 72), title)

    ps.end_document()

"""
'''

def label_to_image(label):

#print(qcolour(1,2,3))
from PIL import Image, ImageGrab

def capture_widget(widget):
    """Take screenshot of the passed widget"""

    widget.update()
    widget.focus()

    x0 = widget.winfo_rootx()
    y0 = widget.winfo_rooty()
    x1 = x0 + widget.winfo_width()
    y1 = y0 + widget.winfo_height()

    img = ImageGrab.grab((x0, y0, x1, y1))
    return img

img = capture_widget(widget)

# resize and interpolate (resample)
scale = 2
img = img.resize((int(img.size[0] * scale), int(img.size[1] * scale)), resample = Image.LANCZOS)



mg = img.convert('P',
    palette=Image.ADAPTIVE, # Let PIL pick the best fitting palette
    colors=256, # Amount of colors for the ADAPTIVE palette, 256 is default and max
    )


14




Thi
'''
"""
from tkinter import *
from tkinter import font

root = Tk()
root.title('Font Families')
fonts=list(font.families())
fonts.sort()

def populate(frame):
    '''Put in the fonts'''
    listnumber = 1
    for i, item in enumerate(fonts):
        label = "listlabel" + str(listnumber)
        label = Label(frame,text=item,font=(item, 16))
        label.grid(row=i)
        label.bind("<Button-1>",lambda e,item=item:copy_to_clipboard(item))
        listnumber += 1

def copy_to_clipboard(item):
    root.clipboard_clear()
    root.clipboard_append("font=('" + item.lstrip('@') + "', 12)")

def onFrameConfigure(canvas):
    '''Reset the scroll region to encompass the inner frame'''
    canvas.configure(scrollregion=canvas.bbox("all"))

canvas = Canvas(root, borderwidth=0, background="#ffffff")
frame = Frame(canvas, background="#ffffff")
vsb = Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=vsb.set)

vsb.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)
canvas.create_window((4,4), window=frame, anchor="nw")

frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))

populate(frame)

root.mainloop()
"""

#tk=tk.Tk()
#f=BubblFont().font#
#print(f.metrics('linespace'))
