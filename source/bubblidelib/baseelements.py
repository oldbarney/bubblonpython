"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import time

from bubblib.utils import log
from .blockeditor import BlockEditor
from bubblib.blockfactory import PythonBlock, CallBlock, VariableBlock, \
    DBVariableBlock
from bubblib.gutils import colour, brighter, cropped_string, BubblFont
from bubblib.iset import Iset
from bubblib.globaldefs import non_editable_types, centre_text_types, \
    render_defaults
from .presenterinfo import get_presenter_info
from .renderer import render


class Maxtlogger:
    def __init__(self):
        self.maxt = 0

    def log(self, t):
        if t > self.maxt:
            self.maxt = t
            return True
        return False


maxtlogger = Maxtlogger()


class BaseBlockPresenter:

    def __init__(self, diag_editor, node, centre_anchor=False, live_data=False):
        self.diag_editor = diag_editor
        self.canvas = diag_editor.canvas
        self.node = node
        self.node_no = node.no
        self.params = self.node.params
        self.info = get_presenter_info(self.node.type_name, self.params,
                                       diag_editor.diag)
        self.centre_text = node.type_name in centre_text_types

        self.highlighted = False
        self.snappable = False
        self.live_data = live_data
        self.has_editor = self.node.type_name not in non_editable_types
        self.editor = None
        self.uid = f'wn{node.no}'
        self.tags = ('widget', self.uid)
        if centre_anchor:
            self.xorg = -self.scaled_width() // 2
            self.yorg = -render_defaults.gs_div2
        else:
            self.xorg = 0
            self.yorg = 0
        self.font = BubblFont(render_defaults.font)
        self.shape_type = node.presentation["shape"]
        self.defn = node.presentation["block"]
        self.allow_vertical_sizing = 'vertical_sizing' in self.defn
        self.executable = 'executable' in self.defn
        # print('making Presenter for ',node.presentation['title'])
        if isinstance(node, PythonBlock):
            self.fill_colour = '#FF0'
            self.colour = '#04A'
        elif isinstance(node, CallBlock):
            self.fill_colour = self.diag_editor.diag.mach.diags[
                node.target_name].params[0]
            #print(f'CALLBLOCK {self.info.display_line(0)} FILL COLOUR>{self.fill_colour}< uid:>{self.uid}<')
        elif self.defn["colour"]:
            self.fill_colour = colour(self.defn["colour"]).string()
            # print('fill_colour=',self.fill_colour)
        else:
            # print(f'blockItem setting fill colour to white')
            self.fill_colour = '#DDD'  # None
        self.highlight_fill = brighter(self.fill_colour).string()
        if isinstance(node, (VariableBlock,DBVariableBlock)):
            self.colour = '#FFFF77'
            self.fill_colour = '#004'
        else:
            self.colour = '#000'

    def __str__(self):
        return (f'{self.uid} h/l:{self.highlighted} {self.node.type_name}'+
                f' {self.node_no}')

    def highlight(self, highlight):
        # print('highlight',self.node_no,highlight)
        if self.highlighted:
            if not highlight:
                self.highlighted = False
                self.canvas.itemconfigure(f'o{self.node_no}',
                                          fill=self.fill_colour)
        else:
            if highlight:
                # print('highlightingblockpresenter',self.highlight_fill,self.fill_colour)
                self.highlighted = True
                self.canvas.itemconfigure(f'o{self.node_no}',
                                          fill=self.highlight_fill)

    def adjustHeight(self):
        if 'height_adjust' in self.defn:
            adjust_style = self.defn['height_adjust']
        else:
            self.node.dim[1] = get_presenter_info(
                self.node.type_name,
                self.params,
                self.diag_editor.diag).ndisplay_lines()
            return
        if adjust_style == 'interface':
            self.node.dim[1] = len(self.node.diag.params)
        elif adjust_style == 'menu':
            self.node.dim[1] = len(self.params) + (
                1 if self.node.presentation["title"] == "Menu" else 0)
        elif adjust_style == 'wait':
            h = 1 + (len(self.node.links))
            self.node.dim[1] = h
        else:
            raise Exception('Unrecognised height adjust style')

    def xy(self, event):
        return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    def contains_point(self, x, y):
        # print('contains point',x,y)
        xp = self.xpos()
        if x < xp:
            return False
        if x > xp + self.scaled_width():
            return False
        yp = self.ypos()
        if y < yp:
            return False
        return y <= yp + self.scaled_height()

    def start_dragging(self, xo, yo):
        self.drag_xo = xo
        self.drag_yo = yo

    def translate(self, dx, dy):
        self.diag_editor.vm.translate_nodes(
            self.node.diag, Iset(self.node_no), dx, dy, True)

    def drag(self, x, y, thresh=1):
        dx = round(x - self.drag_xo)
        dy = round(y - self.drag_yo)
        if abs(dx) >= thresh or abs(dy) >= thresh:  # dx or dy:
            # print('dragging',dx,dy)
            self.diag_editor.vm.translate_nodes(
                self.node.diag, Iset(self.node_no),
                dx / render_defaults.grid,
                dy / render_defaults.grid, True)
            self.canvas.move(self.uid, dx, dy)
            self.drag_xo += dx
            self.drag_yo += dy

    def delete_from_canvas(self):
        self.canvas.delete(self.uid)

    def squash(self,x,y,fact):
        self.delete_from_canvas()
        x = x + round((self.xpos() - x) / fact)
        y = y + round((self.ypos() -y) / fact)
        font=BubblFont('sanserif,5')
        render(self.canvas, x,y,
               self.scaled_width()/fact, self.scaled_height()/fact,
               self.tags, self.node_no, self.shape_type,
               self.highlight_fill if self.highlighted else self.fill_colour,
               self.colour,
               [cropped_string(self.info.display_line(i),
                               self.scaled_width(),font.font, render_defaults.grid/fact)
                for i in range(self.info.ndisplay_lines())],
               centre_text=self.centre_text, font=font,
               grid=render_defaults.grid/fact)

    def refresh(self):
        # torg=time.perf_counter()
        self.delete_from_canvas()

        render(self.canvas, self.xpos(), self.ypos(),
               self.scaled_width(), self.scaled_height(),
               self.tags, self.node_no, self.shape_type,
               self.highlight_fill if self.highlighted else self.fill_colour,
               self.colour,
               [cropped_string(self.info.display_line(i),
                               self.scaled_width(),
                               self.font.font, render_defaults.grid)
                for i in range(self.info.ndisplay_lines())],
               centre_text=self.centre_text, font=self.font)
        # t=time.perf_counter()-torg
        # if maxtlogger.log(t):
        #    print('NEW MAX render_time',
        #          self.diag_editor.diag.name,
        #          self.node_no,
        #          self.node.type_name,t)

        # self.make_shape()
        # for i in range(self.node.ndisplay_lines()):
        #    self.draw_line(i, self.cropped_string(self.node.display_line(i)))

    def xpos(self):
        return round(self.node.position[0] * render_defaults.grid + self.xorg)

    def ypos(self):
        return round(self.node.position[1] * render_defaults.grid + self.yorg)

    def gwidth(self):
        return self.node.dim[0]

    def gheight(self):
        return self.node.dim[1]

    def scaled_width(self):
        return self.node.dim[0] * render_defaults.grid

    def scaled_height(self):
        return self.node.dim[1] * render_defaults.grid

    """
    def make_shape(self):
        # print('shape',self.node.type_name,self.node.position[1]*render_defaults.grid,self.ypos(),self.yorg)
        x1 = self.xpos()
        y1 = self.ypos()
        x2 = x1 + self.scaled_width()
        y2 = y1 + self.scaled_height()
        fill = self.highlight_fill if self.highlighted else self.fill_colour
        if self.shape_type == 'rect':
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill,
                                         outline='#000',
                                         tags=self.tags + (f'o{self.node_no}',),
                                         width=1)
        elif self.shape_type == 'round':
            r = render_defaults.gs_by2
            points = [x1, y1 + r, x1 + r / 4, y1 + r / 2, x1 + r / 2,
                      y1 + r / 4, x1 + r, y1,
                      x2 - r, y1, x2 - r / 2, y1 + r / 4, x2 - r / 4,
                      y1 + r / 2, x2, y1 + r,
                      x2, y2 - r, x2 - r / 4, y2 - r / 2, x2 - r / 2,
                      y2 - r / 4, x2 - r, y2,
                      x1 + r, y2, x1 + r / 2, y2 - r / 4, x1 + r / 4,
                      y2 - r / 2, x1, y2 - r]
            self.canvas.create_polygon(points, fill=fill, outline='#000',
                                       tags=self.tags + (f'o{self.node_no}',),
                                       width=1)  # ,activefill=self.highlight_fill)
            ''' points = [x1+radius, y1,
              x1+radius, y1,
              x2-radius, y1,
              x2-radius, y1,
              x2, y1,
              x2, y1+radius,
              x2, y1+radius,
              x2, y2-radius,
              x2, y2-radius,
              x2, y2,
              x2-radius, y2,
              x2-radius, y2,
              x1+radius, y2,
              x1+radius, y2,
              x1, y2,
              x1, y2-radius,
              x1, y2-radius,
              x1, y1+radius,
              x1, y1+radius,
              x1, y1]
            points=[x+r,y, x+r,y, x2-r,y, x2-r,y, x2,y, x2,r+y, x2,r+y, x2,y2-r, x2,y2-r, x2,y2,
                    x2-r,y2, x2-r,y2, x+r,y2, x+r,y2, x,y2, x,y2-r, x,y2-r, x,y+r, x,y+r, x,y]
            self.id_no=self.canvas.create_polygon(points,fill=self.fill_colour, outline='#000',tag=f'{self.nodeNo}',smooth=True)
 '''
        elif self.shape_type == 'rhombus':
            g2 = render_defaults.gs_div2
            points = [x1, y1 + g2, x1 + g2, y1 + g2 + g2, x1 + g2 + g2, y1 + g2,
                      x1 + g2, y1]
            self.canvas.create_polygon(points, fill=fill, outline='#000',
                                       tags=self.tags + (
                                       f'o{self.node_no}',))  # ,activefill=self.highlight_fill)

    def draw_line(self, index, text):
        self.canvas.create_text(self.xpos() + 2,
                                self.ypos() + index * render_defaults.grid,
                                text=text, fill=self.colour, anchor='nw',
                                tags=self.tags + (f't{self.node_no}#{index}',),
                             font=BubblFont().font)
"""

class BlockPresenter(BaseBlockPresenter):
    def __init__(self, diag_editor, node, centre_anchor=False, snappable=False,
                 live_data=False):
        BaseBlockPresenter.__init__(self, diag_editor, node,
                                    centre_anchor=centre_anchor,
                                    live_data=live_data)
        # if node.no in diag_editor.presenters:
        # print('DOUBLE CREATION OF BLOCK PRESENTER')
        self.edgehit = None
        self.sizing = False
        self.sizeorg = [0, 0]

        self.link_type = self.defn["linktype"]
        self.link_names = self.defn["linknames"]
        self.link_starts = []
        self.link_destinations = []

        # "size=({self.width()},{self.height()})")
        # self.setFlag(QGraphicsObject.ItemIsMovable,True)
        self.got_mouse = False
        self.flash_phase = False

        # print('COLOURS',self.fill_colour,self.highlight_fill)
        # self.fill_colour=self.highlight_fill
        self.sizing_base_width = 0
        self.sizing_base_height = 0

        self.snappable = snappable
        self.editor=None
        # print(f'BlockItem params for {node.typename} is {self.params}')

    def start_sizing(self, xo, yo):
        self.sizing_base_width = self.gwidth()
        self.sizing_base_height = self.gheight()
        self.sizing_posx = self.node.position[0]
        self.size_x_org = xo
        self.size_y_org = yo

    def size_move_event(self, x, y):
        # print('mouse_move on widget',x,y)
        xoff = x - self.size_x_org
        dx = round(xoff / render_defaults.grid)
        if self.allow_vertical_sizing:
            yoff = y - self.size_y_org
            dy = round(yoff / render_defaults.grid)
        else:
            dy = 0
        if self.xorg != 0 and not self.allow_vertical_sizing:  # isinstance(self,ExecutableBlockPresenter): #centre anchored (executable) node
            if self.edgehit == 'right':
                newwidth = self.sizing_base_width + 2 * dx
            else:
                newwidth = self.sizing_base_width - 2 * dx
            newwidth = max(newwidth, 3)

            if newwidth != self.gwidth():
                self.diag_editor.vm.change_block_size(self.node.diag,
                                                      self.node_no, newwidth,
                                                      self.gheight(), True)
                self.refresh()
        else:
            if self.edgehit == 'right':
                newwidth = max(self.sizing_base_width + dx, 1)
                if newwidth != self.gwidth():
                    self.diag_editor.vm.change_block_size(self.node.diag,
                                                          self.node_no,
                                                          newwidth,
                                                          self.gheight(), True)
                    self.refresh()
            elif self.edgehit == 'bottomright':
                newwidth = max(self.sizing_base_width + dx, 1)
                newheight = max(self.sizing_base_height + dy, 1)
                if newwidth != self.gwidth() or newheight != self.gheight():
                    self.diag_editor.vm.change_block_size(self.node.diag,
                                                          self.node_no,
                                                          newwidth, newheight,
                                                          True)
                    self.refresh()
            elif self.edgehit == 'left':
                newwidth = max(self.sizing_base_width - dx, 1)
                if newwidth != self.gwidth():
                    self.diag_editor.vm.change_block_size(self.node.diag,
                                                          self.node_no,
                                                          newwidth,
                                                          self.gheight(), True)
                    tx = self.sizing_posx + dx - self.node.position[0]
                    if tx != 0:
                        self.diag_editor.vm.translate_nodes(self.node.diag,
                                                            Iset(self.node_no),
                                                            tx, 0, True)
                    self.refresh()
            elif self.edgehit == 'bottomleft':
                newwidth = max(self.sizing_base_width - dx, 1)
                newheight = max(self.sizing_base_height + dy, 1)
                if newwidth != self.gwidth() or newheight != self.gheight():
                    self.diag_editor.vm.change_block_size(self.node.diag,
                                                          self.node_no,
                                                          newwidth, newheight,
                                                          True)
                    tx = self.sizing_posx + dx - self.node.position[0]
                    if tx != 0:
                        self.diag_editor.vm.translate_nodes(self.node.diag,
                                                            Iset(self.node_no),
                                                            tx, 0, True)
                    self.refresh()
            elif self.edgehit == 'bottom':
                newheight = max(self.sizing_base_height + dy, 1)
                if newheight != self.gheight():
                    self.diag_editor.vm.change_block_size(self.node.diag,
                                                          self.node_no,
                                                          self.gwidth(),
                                                          newheight, True)
                    self.refresh()

    def get_hit_edge(self, x, y):
        if self.shape_type in ('rhombus', 'oval'):
            return None
        if x is not None:
            if x > self.scaled_width() - render_defaults.gs_by3:
                if self.allow_vertical_sizing and y > self.scaled_height(
                ) - render_defaults.gs_by3:
                    self.edgehit = 'bottomright'
                else:
                    self.edgehit = "right"
            elif x < render_defaults.gs_by3:
                if self.allow_vertical_sizing and y > self.scaled_height(
                ) - render_defaults.gs_by3:
                    self.edgehit = 'bottomleft'
                else:
                    self.edgehit = "left"
            elif self.allow_vertical_sizing and y > self.scaled_height(
            ) - render_defaults.gs_by3:
                self.edgehit = 'bottom'
            else:
                self.edgehit = None
        else:
            self.edgehit = None
        # print('node',self.node_no,'edge',self.edgehit)
        return self.edgehit

    def edit(self, x, y,on_top=False,line_no=None):
        # print('BlockItem.edit calling editor')
        # print('node.presentation["edlines"]',self.node.presentation['edlines'])
        if self.editor is None:
            self.editor = BlockEditor(self.diag_editor, self.node, x, y)
            if on_top:
                self.editor.input_box.win.attributes("-topmost",True)
        else:
            self.editor.input_box.win.attributes("-topmost",True)

    def end_edit(self, changed):
        # print('END_EDIT b',changed)
        if changed:
            try:
                self.adjustHeight()
                if self.live_data:
                    self.info.cache.clear()
                self.refresh()
                self.diag_editor.redraw()
            except Exception as e:
                log('Ending edit unable to refresh',e,level=2)
        self.editor = None
