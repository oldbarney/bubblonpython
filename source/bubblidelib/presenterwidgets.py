"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import os
import threading
import tkinter.messagebox
import webbrowser
from copy import deepcopy

from bubblib.logger import Logger
from bubblib.utils import value_from_str, get_val_from_kvlist, log
from .baseelements import BlockPresenter
from bubblib.globaldefs import render_defaults, dispmarkups
from bubblib.gutils import get_image, BubblFont, brighter, minxy, maxxy, \
    grab_image_from_screen, shape_points
from bubblib.simplebubblapp import SimpleBUBBLApp
from bubblib.basebubblapp import BaseBUBBLApp


class ImageViewPresenter(BlockPresenter):
    # shows an image in a diagram
    def __init__(self, diag_editor, node):
        BlockPresenter.__init__(self, diag_editor, node, False, False)
        # the above gave us
        #   self.params
        #   self.node
        #   self.nodeNo
        #   self.diag_editor
        #   self.highlighted
        self.load_image()

    def load_image(self) -> object:
        width = round(self.node.dim[0] * render_defaults.grid)
        height = round(self.node.dim[1] * render_defaults.grid)
        kwargs={}
        for p, v in self.params[1:]:
            if p == 'width':
                try:
                    width=int(v)
                except:
                    pass
            elif p == 'height':
                try:
                    width=int(v)
                except:
                    pass
            elif p == 'rotate':
                try:
                    kwargs[p]=int(v)
                except:
                    pass
            elif p == 'scale':
                scale = v.split(',')
                if len(scale) == 2:
                    try:
                        scale = (float(scale[0]), float(scale[1]))
                        kwargs[p]=scale
                    except ValueError:
                        pass
                else:
                    try:
                        kwargs[p]= float(scale)
                    except:
                        pass
        try:
            self.image = get_image(self.params[0], width=width, height=height,**kwargs)
            if isinstance(self.image,str):
                log('Failed to load image:',self.image)
                self.image=None
        except Exception as e:
            log('Failed to load image', e,level=Logger.INFO)
            self.image = None

    def adjustHeight(self):
        self.load_image()

    def highlight(self,highlight):
        super().highlight(highlight)
        self.refresh()



    def refresh(self):
        #print('IMAGE VIEW Refreshing')
        self.delete_from_canvas()
        self.load_image()
        if self.image is None:
            self.canvas.create_text(self.xpos(),
                                    self.ypos(),
                                    text=self.params[0],
                                    fill='#844',
                                    activefill='#AA4',
                                    tags=self.tags,
                                    font=BubblFont().font,
                                    anchor='nw')
            return
        image=self.image.get_image_for_canvas()
        self.canvas.create_image(self.xpos(), self.ypos(), image=image, anchor='nw',
                                 tags=self.tags)
        if self.highlighted:
            self.canvas.create_rectangle(self.xpos(),self.ypos(),
                                         self.xpos()+image.width(),
                                         self.ypos()+image.height(),
                                         outline='#D00',width=3,tags=self.tags)

    def scaled_width(self):
        try:
            return self.image.pil_image.width
        except:
            return BubblFont().width(self.params[0])

    def scaled_height(self):
        try:
            return self.image.pil_image.height
        except:
            return render_defaults.grid

    def get_json_for_disp_thing(self,node_no,link,gx,gy,x_org,y_org):
        """Return json for block connecting to node_no_1
        and new y-coord of block below
        """
        x_off=self.node.init['pos'][0]*render_defaults.grid-x_org
        y_off=self.node.init['pos'][1]*render_defaults.grid-y_org

        def mups():
            width=f"{self.node.init['size'][0]*render_defaults.grid}"
            result=''
            for (key,value) in self.params[1:]:
                if key in dispmarkups['image']:
                    if key=='width':
                        width=value
                    else:
                        result+=f'["{key}","{value}"],\n'
            result+=f'["width","{width}"],\n'

            result+=f'["x","round(_xorg+{x_off:.2f})"],\n["y","round(_yorg+{y_off:.2f})"]'
            return result

        def pars():
            return f'''["'{self.params[0]}'",{mups()}]'''

        def height():
            return 2+mups().count('\n')

        result=f""""{node_no}":{{"params":{pars()},
"type":"IMAGE",
"size":[9,{height()}],
"pos":[{gx},{gy}],
"links":[{link}]}}""",gy+height()+1
        log('IMAGEJASON',result[0])
        return result


class WeblinkPresenter(BlockPresenter):
    # creates an active link to web page (via browser)
    def __init__(self, diag_editor, node):
        BlockPresenter.__init__(self, diag_editor, node, False, False)
        self.font=BubblFont()

        # got self.diag_editor to access resources

    def load_image(self) -> object:
        try:
            self.image = get_image(self.params[2], width=25, height=25)
            if isinstance(self.image,str):
                log('Failed to load image:',self.image)
                self.image=None
        except Exception as e:
            log(f'Failed to load image {e}',level=Logger.INFO)
            self.image = None

    def scaled_width(self):
        return self.font.width(self.params[0])+(3 if self.image is None else 28)

    def scaled_height(self):
        return 25

    def refresh(self):
        #print('IMAGE VIEW Refreshing')
        self.delete_from_canvas()
        self.load_image()
        if self.highlighted:
            #print('Highlighted Activation block')
            self.canvas.create_rectangle(
                self.xpos(),
                self.ypos(),
                self.xpos()+self.scaled_width(),
                self.ypos()+self.scaled_height(),
                fill='#ECC',
                tags=self.tags
            )
        if self.image is None:
            self.canvas.create_text(self.xpos(), self.ypos(),text=self.params[0],tags=self.tags,font=BubblFont().font)
            return
        self.canvas.create_image(self.xpos(), self.ypos(), image=self.image.get_image_for_canvas(), anchor='nw',
                                 tags=self.tags)
        self.canvas.create_text(self.xpos()+26, self.ypos(),text=self.params[0],tags=self.tags,font=BubblFont().font,anchor='nw')

    def highlight(self,highlight):
        if highlight!=self.highlighted:
            self.highlighted=highlight
            self.refresh()

    def execute(self):
        if not webbrowser.open(self.params[1]):
            tkinter.messagebox.showerror('Web Browser','Failed to open web-browser',parent=self.diag_editor.canvas)

class BubblPresenter(WeblinkPresenter):
    def __init__(self,diag_editor, node):
        WeblinkPresenter.__init__(self,diag_editor,node)

    def execute(self):
        #print('Run Bubbl Program')
        if self.node.runs:
            if self.params[3]!='1':
                tkinter.messagebox.showerror('Run BUBBL app','Only one at a time allowed\nMultiple not enabled',
                                             parent=self.diag_editor.canvas)
                return

        def ended(app):
            if app in self.node.runs:
                self.node.runs.remove(app)

        parent_app=self.diag_editor.diag.mach.app
        #def message_func(sender,receiver,message):
            #print('presenter widget message func',sender,receiver,message)
            #parent_app.message_machine(sender,receiver,message)

        try:
            app=SimpleBUBBLApp(BaseBUBBLApp.get_pbub_from_file(self.params[1]),
                               exit_func=ended)
            #parent_app.register_machine(self.params[0],app.mach)
            #print('ADDING',app,'to',self.node.runs)
            self.node.runs.add(app)
            #print('after',self.node.runs)
            app.run()
        except Exception as e:
            tkinter.messagebox.showerror(
                'Bubbl runner',f'Failed to run BUBBL program\n{e}',
                parent=self.diag_editor.canvas)
        #print('Ran Bubbl Program')

class CommandPresenter(WeblinkPresenter):
    def __init__(self,diag_editor, node):
        WeblinkPresenter.__init__(self,diag_editor,node)

    def execute(self):
        #print('Run O/S Command',self.params[1])
        #print('Threads so far',self.node.threads)
        if self.node.threads:
            #print('already running',self.params[3])
            if self.params[3]!='1':
                tkinter.messagebox.showerror('Shell command','Only one at a time allowed\nMultiple not enabled',
                                             parent=self.diag_editor.canvas)
                return
            #print('multiple allowed')
        def run():
            os.system(self.params[1])
            #print('finished run now popping thread')
            self.node.threads.remove(threading.current_thread())

        new_thread=threading.Thread(target=run)
        self.node.threads.add(new_thread)
        #print('Created thread',new_thread)
        new_thread.start()


class GraphicPresenter(BlockPresenter):
    def __init__(self,diag_editor,node):
        BlockPresenter.__init__(self,diag_editor,node)
        self.xo=0
        self.yo=0
        self.indexo=0
        self.reload()

    def convert_to_polygon(self):
        if self.params[0] == 'line':
            self.canvas.delete(self.uid)
            self.params[0]='polygon'
            self.reload()
            self.create_func()
        if self.params[0] =='rect':
            points=list(value_from_str(self.params[1]))
            self.params[1]=str(shape_points('rect',points))
            self.canvas.delete(self.uid)
            self.params[0]='polygon'
            for i in range(2,len(self.params)):
                if self.params[i]=='joins':
                    break
            else:
                self.params.append(['joins','mitre'])
            self.reload()
            self.create_func()
        elif self.params[0]=='ellipse':
            points=value_from_str(self.params[1])
            self.params[1]=str(shape_points('ellipse',points))
            self.canvas.delete(self.uid)
            self.params[0]='polygon'
            self.reload()
            self.create_func()
        elif self.params[0]=='arc':
            points=value_from_str(self.params[1])
            self.params[1]=str(shape_points(self.style,
                                            points,
                                            start=self.start,
                                            angle=self.angle))
            for i in range(2,len(self.params)):
                if self.params[i]=='joins':
                    break
            else:
                self.params.append(['joins','bevel'])
            self.canvas.delete(self.uid)
            if self.style=='arc':
                self.params[0]='line'
            else:
                self.params[0]='polygon'
            self.reload()
            self.create_func()

    def get_polygon_params(self):
        params=deepcopy(self.params)
        if params[0] == 'line':
            params[0]='polygon'
        elif params[0] =='rect':
            points=list(value_from_str(params[1]))
            params[1]=str(shape_points('rect',points))
            params[0]='polygon'
            for i in range(2,len(self.params)):
                if params[i]=='joins':
                    break
            else:
                params.append(['joins','mitre'])
        elif params[0]=='ellipse':
            points=value_from_str(params[1])
            params[1]=str(shape_points('ellipse',points))
            params[0]='polygon'
        elif params[0]=='arc':
            points=value_from_str(params[1])
            params[1]=str(shape_points(self.style,
                                       points,
                                       start=self.start,
                                       angle=self.angle))
            for i in range(2,len(params)):
                if params[i]=='joins':
                    break
            else:
                params.append(['joins','bevel'])
            if self.style=='arc':
                params[0]='line'
            else:
                params[0]='polygon'
        return params

    def reload(self):
        thing=self.params[0]
        points=list(value_from_str(self.params[1]))
        dx=self.node_x()
        dy=self.node_y()
        for i in range(0,len(points),2):
            points[i]+=dx
            points[i+1]+=dy

        join_map={'mitre':'miter','round':'round','bevel':'bevel',
                  'Mitre':'miter','Round':'round','Bevel':'bevel'}
        end_map={'Round':'round','Butt':'butt','Projecting':'projecting',
                 'round':'round','butt':'butt','projecting':'projecting'
                 }

        line_width=get_val_from_kvlist('line_width',self.params[2:],1)
        colour=get_val_from_kvlist('colour',self.params[2:],'#000')
        fill=get_val_from_kvlist('fill',self.params[2:],'')
        active_colour=get_val_from_kvlist('active_colour',self.params[2:],
                                          brighter(colour))
        active_fill=get_val_from_kvlist('active_fill',self.params[2:],
                                        '' if not fill else brighter(fill))
        arrow=get_val_from_kvlist('arrow',self.params[2:],'')
        arrow_shape=get_val_from_kvlist('arrow_shape',self.params[2:],(7,7,3))
        self.start=start=get_val_from_kvlist('start',self.params[2:],0)
        self.angle=angle=get_val_from_kvlist('angle',self.params[2:],90)
        self.style=style=get_val_from_kvlist('style',self.params[2:],'pieslice')
        line_ends=end_map[get_val_from_kvlist('ends',self.params[2:],'Round')]
        line_joins=join_map[get_val_from_kvlist('joins',self.params[2:],'Round')]

        if self.highlighted:
            fill=active_fill
            colour=active_colour

        if thing=='rect':
            def create_func():
                self.canvas.create_rectangle(*points[:4],
                    width=line_width,
                    outline=colour,
                    fill=fill,
                    activeoutline=active_colour,
                    activefill=active_fill,
                    tags=self.tags)
        elif thing=='line':
            def create_func():
                self.canvas.create_line(*points,
                    width=line_width,
                    fill=colour,
                    activefill=active_colour,
                    tags=self.tags,
                    arrow=arrow,
                    arrowshape=arrow_shape,
                    joinstyle=line_joins,
                    capstyle=line_ends)

        elif thing=='ellipse':
            def create_func():
                self.canvas.create_oval(*points[:4],
                    width=line_width,
                    outline=colour,
                    fill=fill,
                    activeoutline=active_colour,
                    activefill=active_fill,
                    tags=self.tags)

        elif thing=='polygon':
            def create_func():
                self.canvas.create_polygon(*points,
                    width=line_width,
                    outline=colour,
                    fill=fill,
                    activeoutline=active_colour,
                    activefill=active_fill,
                    tags=self.tags,
                    joinstyle=line_joins)

        elif thing=='arc':
            def create_func():
                self.canvas.create_arc(*points[:4],
                    width=line_width,
                    outline=colour,
                    fill=fill,
                    activeoutline=active_colour,
                    activefill=active_fill,
                    start=start,
                    extent=angle,
                    style=style,
                    tags=self.tags
                    )

        self.create_func=create_func

    def add_point(self,x,y,force=False):
        pos=self.node.init['pos']
        nx=round(x-pos[0]*render_defaults.grid)
        ny=round(y-pos[1]*render_defaults.grid)
        points=value_from_str(self.params[1])
        dsq=(nx-points[-2])**2+(ny-points[-1])**2
        if not force and dsq<max(5,self.diag_editor.ide.line_width()**2):
            return
        points.append(nx)
        points.append(ny)
        self.indexo=len(points)-2
        self.params[1]=str(points)
        self.reload()
        self.refresh()

    def node_x(self):
        return self.node.init['pos'][0]*render_defaults.grid

    def node_y(self):
        return self.node.init['pos'][1]*render_defaults.grid

    def refresh(self):
        #print('IMAGE VIEW Refreshing')
        self.delete_from_canvas()
        self.reload()
        self.create_func()
        if self.highlighted:
            points=value_from_str(self.params[1])
            xoff=self.node_x()
            yoff=self.node_y()
            for i in range(0,len(points),2):
                x=points[i]+xoff
                y=points[i+1]+yoff
                self.canvas.create_rectangle(x-3,y-3,x+3,y+3,outline='#C00',width=2,tags=['graphics','widget',self.uid,f'pn{i}'])

    def set_move_origin(self,x,y):
        self.xo=round(x)
        self.yo=round(y)

    def move_point(self,x,y):
        x=round(x)
        y=round(y)
        dx=x-self.xo
        dy=y-self.yo
        self.xo=x
        self.yo=y
        points=value_from_str(self.params[1])
        if self.indexo==0:      #ensure always normalised
            pos=self.node.init['pos']
            pos[0]+=dx/render_defaults.grid
            pos[1]+=dy/render_defaults.grid
            for i in range(2,len(points),2):
                points[i]-=dx
                points[i+1]-=dy
        else:
            points[self.indexo]+=dx
            points[self.indexo+1]+=dy
        self.params[1]=str(points)

    def highlight(self,highlight):
        if highlight!=self.highlighted:
            self.highlighted=highlight
            self.refresh()

    def over_point(self,index,x,y,radius=2):
        x=round(x)
        y=round(y)
        #log('over_point',x,y,'r=',radius,)
        points=value_from_str(self.params[1])
        try:
            px=round(points[index]+self.node_x())
            py=round(points[index+1]++self.node_y())
            result= ( x in range(px-radius,px+radius)
                 and y in range(py-radius,py+radius))
            log('over_point',x,y,'r=',radius,px,py,'result=',result)
            return result

        except Exception as e:
            log(f'OVER_POINT EXCEPTION{e}',level=Logger.INFO)
            return False

    def xpos(self):
        points=value_from_str(self.params[1])
        return (round(minxy(points)[0]
                 +self.node_x()))
    def ypos(self):
        points=value_from_str(self.params[1])
        return (round(minxy(points)[1]
                 +self.node_y()))

    def scaled_width(self):
        points=value_from_str(self.params[1])
        return round(maxxy(points)[0]-minxy(points)[0])

    def scaled_height(self):
        points=value_from_str(self.params[1])
        return round(maxxy(points)[1]-minxy(points)[1])

    def get_json_for_disp_thing(self,node_no,link,gx,gy,x_org,y_org):
        """Return json for block connecting to node_no_1
        and new y-coord of block below
        """
        points=value_from_str(self.params[1])
        x_off=self.node_x()-x_org
        y_off=self.node_y()-y_org
        thing=self.params[0]
        def mups():
            #'write',line,'rect','ellipse','polygon','arc'
            result=''
            for (key,value) in self.params[2:]:
                if key in dispmarkups[thing] and key!='points':
                    result+=f'["{key}","{value}"],\n'
            result+=f'["x","round(_xorg+{x_off:.2f})"],\n["y","round(_yorg+{y_off:.2f})"]'
            return result

        def pars():
            if thing in ('rect','ellipse','arc'):
                return f'["{round(points[2]-points[0])}","{round(points[3]-points[1])}",{mups()}]'
            if thing in ('line','polygon'):
                dxs=','.join(f'{points[i+2]-points[i]}'
                                for i in range(0,len(points)-2,2))
                dys=','.join(f'{points[i+2]-points[i]}'
                                for i in range(1,len(points)-2,2))
                return f'["{dxs}","{dys}",{mups()}]'
        def height():
            if thing in ('rect','ellipse','arc'):
                return 2+mups().count('\n')
            return 2+mups().count('\n')

        return f""""{node_no}":{{"params":{pars()},
"type":"{thing.upper()}",
"size":[7,{height()}],
"pos":[{gx},{gy}],
"links":[{link}]}}""",gy+height()+1

    def grab_from_screen(self):
        sx,sy=self.diag_editor.screen_xy()
        points=value_from_str(self.params[1])
        ex=self.node_x()
        ey=self.node_y()
        thing=self.params[0]
        if thing=='rect':
            rect=(sx+ex+points[0],
                  sy+ey+points[1],
                  sx+ex+points[2],
                  sy+ey+points[3])
            rect=(min(rect[0],rect[2]),
                  min(rect[1],rect[3]),
                  max(rect[0],rect[2]),
                  max(rect[1],rect[3]))
            poly=None
        else:
            rect=None
            poly=[]
            for i in range(0,len(points),2):
                poly.append((sx+ex+points[i],sy+ey+points[i+1]))
            poly=tuple(poly)
        return grab_image_from_screen(rect,poly)