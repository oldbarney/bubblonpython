"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import tkinter as tk

from bubblib.utils import log
from.dialogeditor import DialogEditor
from bubblib.gutils import BubblFont, cropped_string
from.baseelements import BlockPresenter
from bubblib.globaldefs import render_defaults
from bubblib.iset import Iset
from bubblib.linegrid import N,S,E,W, touching_arrow_coords,arrow_coords
from bubblib.mywidgets import PopupMenu
from.presenterinfo import PythonPresenterInfo, DialogPresenterInfo
from .pythoneditor import PythonEditor

class ExecutableBlockPresenter(BlockPresenter):

    def __init__(self, editor, node, grid=None):
        BlockPresenter.__init__(self, editor, node, centre_anchor=True, snappable=True)

        self.grid = grid
        try:
            self.menu_style_links = self.defn["menustylelinks"]
        except:
            self.menu_style_links = None
        # menu_style_links means in-links are top edge and bottom edge only
        # and out-link 0 (default or esc) is top edge and bottom edge only,
        # other out-links are left edge or right edge at fixed y-position
        for linkNo in range(len(self.node.links)):
            # print(f'adding link:{linkNo} to node:{node.no}')
            start = LinkStart(self.diag_editor, self, linkNo)
            # self.finished_dragging_my_link.connect(start.end_drag)
            self.link_starts.append(start)
            self.link_destinations.append((None, None))

        self._avail_out_cons = Iset(range(2 * (self.gwidth() + self.gheight())))
        self._in_cons = Iset()
        # self.fill_grid()

        # self.select_node.connect(self.node.diag.mach.diags.console.select_node)

    def refresh(self):
        self.xorg = -self.scaled_width() / 2
        super().refresh()
        # self.destroyLinkLines()
        # self.check_links()

    def reset_links(self):
        self.link_starts.clear()
        self.link_destinations.clear()
        for linkNo in range(len(self.node.links)):
            # print(f'adding link:{linkNo} to node:{node.no}')
            start = LinkStart(self.diag_editor, self, linkNo)
            # self.finished_dragging_my_link.connect(start.end_drag)
            self.link_starts.append(start)
            self.link_destinations.append((None, None))

        # print('got',len(self.link_starts),'links')

        self._avail_out_cons = Iset(range(2 * (self.gwidth() + self.gheight())))
        self._in_cons = Iset()

    def get_link_name(self, linkNo):
        style = self.link_type
        if style == 'single':
            return ''
        if style == 'if':
            if linkNo == 1:
                return ''
            return self.params[0]
        if style == 'menu':
            if linkNo == 0:
                return self.link_names[0]
            return ''
        if style == 'call':
            # print(f'diagelements.Block_item.getLinkName index={linkNo}')
            try:
                return self.node.diag.mach.diags[self.params[0]].sig["linknames"][linkNo]
            except:
                return ''  # For a block with no named links
        if style == 'python':
            return ''
        if style == "wait":
            return self.params[linkNo + 1]
        if style == "switch":
            if linkNo == 0:
                return "Default"
            return ''
        # if style == "python":
        #    return self.python_block.linknames[linkNo]
        if style == "none":
            raise Exception("There should not be a link name for a Link instruction")
        return self.link_names[linkNo]

    def get_link_arrow(self, linkNo):
        # return arrow coordinate,direction,touching
        # print(f'get_link_arrow called on node:{self.nodeNo},link:{linkNo}')
        if self.node.links[linkNo] == 0:
            if self.menu_style_links:
                if linkNo == 0:
                    cx, cy = self.centre()
                    x, y, dirn = self.nearest_out_edge(0, cx + 1, cy + 2, True)
                else:
                    x, y, dirn = self.link_edge(self.gwidth() + linkNo)
                    self._avail_out_cons -= self.gwidth() + linkNo
                return arrow_coords(x, y, dirn, render_defaults.grid), dirn, False

            px = round((self.node.position[0] + self.node.dim[0]) * render_defaults.grid)
            py = round((self.node.position[1] + linkNo) * render_defaults.grid)
            # print(f'getLinkArrow linkNo:{linkNo} pos:{Pos(px, py)}')
            x, y, dirn = self.nearest_out_edge(linkNo, px, py, True)
            return arrow_coords(x, y, dirn, render_defaults.grid), dirn, False
        lix, liy, _ = self.link_destinations[linkNo]

        x, y, dirn = self.nearest_out_edge(linkNo, lix, liy, True)

        if x == lix and y == liy:
            # print('TOUCHING')
            return touching_arrow_coords(x, y, dirn, render_defaults.grid), dirn, True
        return arrow_coords(x, y, dirn, render_defaults.grid), dirn, False

    def get_target_in_link(self, linkNo):
        # print(f'block_item:{self.nodeNo} getting target in link {linkNo}')
        if self.node.links[linkNo] == 0:
            self.link_destinations[linkNo] = (None, None, None)
        else:
            # print('HMM',self.node.links,linkNo)
            try:
                targetBlock = self.diag_editor.presenters[self.node.links[linkNo]]
            except KeyError: #Cater for corrupted source file
                self.node.links[linkNo] = 0
                self.link_destinations[linkNo] = (None, None, None)
                return
            # print(f'get_target_in_link:TargetBlock={targetBlock.nodeNo} links:{targetBlock.node.links}')
            if self.menu_style_links:
                if targetBlock.node.position[0] > self.node.position[0]:
                    x, y, _ = self.link_edge(self.gwidth() + linkNo)
                else:
                    x, y, _ = self.link_edge(self.gwidth() * 2 + self.gheight() * 2 - 1 - linkNo)
                self.link_destinations[linkNo] = targetBlock.reserve_inward_connection(x, y)
            else:
                self.link_destinations[linkNo] = targetBlock.reserve_inward_connection(*self.centre())

    def getExtendedPath(self, linkstart):
        # return points-in-path,in-line
        if linkstart.touching:
            return linkstart.arrow, linkstart.direction
        link = self.node.links[linkstart.link_no]
        if link == 0:
            return linkstart.arrow, linkstart.direction
        # print('we are a ',self.node.type_name)
        # print('linkstart is',linkstart)
        # print('link inputs is ', self.link_inputs[linkstart.link_no])
        (x, y, indir) = self.link_destinations[linkstart.link_no]

        # print('HMM',(inpos,indir))
        darrow = arrow_coords(x, y, indir, render_defaults.grid)
        # path=findpath(self.grid,linkstart.startpos,inpos)
        # print(f'path={path}')
        # print('inkstartarrow is',linkstart.arrow )

        result = linkstart.arrow + darrow[2:] + darrow[:2]
        return result, linkstart.direction

    def finished_dragging_link(self, pos):
        # print(f'finished_dragging_my_link emitting{pos}')
        self.finished_dragging_my_link.emit(pos)

    def resetConnections(self):  # this is where different kinds of linkability happens
        self._avail_out_cons = Iset(range(2 * (self.gwidth() + self.gheight())))
        self._in_cons = Iset()
        # print(f'connections for {self.nodeNo} are {self._availCons}')
        # else:
        # print(f'not resetting connections {self.nodeNo} not in {nodes}')

    def top_and_bottom(self):

        return (Iset(range(self.gwidth()))
                | Iset(range(self.gwidth() + self.gheight(),
                              2 * self.gwidth() + self.gheight()))
               )

    def left_and_right(self, row):
        return Iset(self.gwidth() + row, self.gwidth() * 2 + self.gheight() * 2 - 1 - row)

    def in_connections(self):
        if self.menu_style_links:
            return (self._avail_out_cons & self.top_and_bottom()) | self._in_cons
        return self._avail_out_cons | self._in_cons

    def out_connections(self, linkNo):
        if self.menu_style_links is not None:
            if linkNo == 0:
                return self.top_and_bottom() & self._avail_out_cons
            return self.left_and_right(linkNo)
        if self.node.type_name=='IF':
            return self._avail_out_cons
        return self._avail_out_cons - self._in_cons

    def centre(self):
        return (round(self.node.position[0] * render_defaults.grid),
                round(self.node.position[1] * render_defaults.grid +
                     (self.node.dim[1] - 1) * render_defaults.gs_div2)
               )

    def link_edge(self, conNo):
        gby2 = render_defaults.gs_div2
        gw = self.node.dim[0]
        w = round(gw * render_defaults.grid)
        gh = self.node.dim[1]
        h = round(gh * render_defaults.grid)
        le = round(self.node.position[0] * render_defaults.grid - gw * gby2)
        re = le + w
        te = round(self.node.position[1] * render_defaults.grid - gby2)
        be = te + h

        if conNo < gw:
            return le + gby2 + conNo * render_defaults.grid, te, N
        conNo -= gw
        if conNo < gh:
            return re, te + gby2 + conNo * render_defaults.grid, E
        conNo -= gh
        if conNo < gw:
            return re - gby2 - conNo * render_defaults.grid, be, S
        conNo -= gw
        return le, be - gby2 - conNo * render_defaults.grid, W

    def nearest_out_edge(self, linkNo, tx, ty, allocate: bool):
        # returns pos,direction
        # print(f'linkNo:{linkNo}  target:{target}  connections:{self.out_connections(linkNo)}')
        dist = None
        res = None
        for i in self.out_connections(linkNo):
            x, y, dirn = self.link_edge(i)
            d = (x - tx) ** 2 + (y - ty) ** 2
            if (dist == None) or d < dist:
                dist = d
                res = i, x, y, dirn
        if res == None:  # should not happen
            raise Exception("Should not happen that an outlink is unavailable")
        if allocate:
            self._avail_out_cons -= res[0]
        return res[1:]

    def reserve_inward_connection(self, sx, sy):
        # return x-coord,y-coord,outward_direction of inward_connection
        dist = None
        res = None

        out_cons_reserved=(
            len(self.link_starts)==len(self.out_connections(0))
        )
        if out_cons_reserved:
            candidates=self._in_cons
        else:
            candidates=self.in_connections()

        for i in candidates:
            x, y, dirn = self.link_edge(i)
            # print(f'p={p} dir={dir}')
            d = (x - sx) ** 2 + (y - sy) ** 2
            # print(f'conn:{i} d={d} dist={dist}')
            if (dist == None) or d < dist:
                dist = d
                # print(f'updating dist conn:{i} d={d} dist={dist}')
                res = i, x, y, dirn

        if not out_cons_reserved:
            self._in_cons |= res[0]
        if res is None:
            log('No available inlinks for',self.node.type_name)
            return [0]
        return res[1:]

    def end_edit(self,changed):
        #print('END_EDIT a',changed)
        super().end_edit(changed)
        try:
            self.node.compile_code()
        except:
            self.node.code=self.node.code_text()
            self.node.undoable_code=self.node.undoable_code_text()


    # def fill_grid(self):
    #    if self.snappable:
    #        self.grid.blockout(Pos(self.node.position), self.gwidth(), self.gheight(), self.node_no)

    # def clear_grid(self):
    #    if self.snappable:
    #        self.grid.blockout(Pos(self.node.position), self.gwidth(), self.gheight(), 0)

    """
    def edit(self):
        #print('BlockItem.edit calling editor')
        if self.node.presentation['edlines']:
            self.beditor = BlockEditor(self.canvas, self.node)
            self.beditor.show()
            self.beditor.setFocus()
    """


label_anchor_map = ['sw', '', 'sw', '', 'nw', '', 'se', '']

join_in_dir_map = (N, E, S, W)

class DialogPresenter(ExecutableBlockPresenter):
    def __init__(self, diag_editor,node):
        ExecutableBlockPresenter.__init__(self,diag_editor,node)
        self.info=DialogPresenterInfo(self.params)
        self.x=0
        self.y=0

    def edit(self,x,y,on_top=False,line_no=None):
        self.x=x
        self.y=y

        PopupMenu(self.canvas,x,y,['Edit parameters','Edit dialog'],
                  self.whether_call_or_dialog)

    def whether_call_or_dialog(self,item):
        if item=='Edit parameters':
            super().edit(self.x,self.y,on_top=False)
            return
        if item is None:
            return
        try:
            table=self.diag_editor.bbsm.database[self.params[0]]
            if table is None:
                raise
        except Exception as e:
            log('Exception here',e)
            table=self.params[0]
        log('table is',table)
        self.editor=DialogEditor(self.x,self.y,table,self.params[1],self.dialog_edited)

    def dialog_edited(self,result):
        log('Dialog_edited result',result)
        if result is not None:
            self.diag_editor.bbsm.database[self.params[0]]=result
        self.editor=None





class PythonPresenter(ExecutableBlockPresenter):
    def __init__(self, diag_editor,node):
        ExecutableBlockPresenter.__init__(self,diag_editor,node)
        self.info=PythonPresenterInfo(self.params)
        self.font=BubblFont('Monospace,9')

    def edit(self,x,y,on_top=False,line_no=None,col_no=0):
        if self.editor is None:
            self.editor=PythonEditor(self.canvas,
                                     exit_func=self.update_params,
                                     params=self.params
                                     )
            if line_no is not None:
                self.editor.text.see(f'{line_no}.{col_no}')
                self.editor.text.mark_set('insert',f'{line_no}.{col_no}')
                #self.editor.text.highlight_line()
            if on_top:
                self.editor.window.attributes('-topmost',True)
            self.editor.text.focus_set()
        else:
            self.editor.window.attributes('-topmost',True)
            if line_no is not None:
                self.editor.text.see(f'{line_no}.0')
                self.editor.text.mark_set('insert',f'{line_no}.0')
            self.editor.text.focus_set()



    def update_params(self,changed):  # todo here ensure machine not running before updating
        self.editor=None
        if changed:
            self.diag_editor.redraw_live_data()
            self.refresh()
            try:
                self.node.compile_code()
            except:
                self.node.undoable_code=self.node.code='_mach.runtime_error("Invalid Python code")\n'

    def highlight(self, highlight):
        if self.highlighted:
            if not highlight:
                self.highlighted = False
                self.refresh()
        else:
            if highlight:
                self.highlighted = True
                self.refresh()

    def squash(self,x,y,factor):
        self.canvas.create_text(x,y,text='PYTHON',anchor='center',
                                tags=self.tags,font=12/factor)

    def refresh(self):
        #print('IMAGE VIEW Refreshing')
        self.xorg = -self.scaled_width() / 2

        x=self.xpos()
        y=self.ypos()
        self.delete_from_canvas()
        self.canvas.create_rectangle(x,y,x+self.scaled_width(),
                                     y+self.scaled_height(),
                                     outline='#000',
                                     fill=self.highlight_fill if self.highlighted else self.fill_colour,
                                     tags=self.tags)
        #print('range',range(1,self.node.dim[1]-1))
        width=self.node.dim[0]*render_defaults.grid
        for i in range(min(len(self.params),self.node.dim[1])):
           self.canvas.create_text(x,y+i*render_defaults.grid,
                                   text=cropped_string(self.params[i],width,self.font.font,render_defaults.grid),
                                   fill='#009',
                                   font=self.font.font,
                                   anchor='nw',tags=self.tags)

class JoinBlockPresenter(ExecutableBlockPresenter):
    def __init__(self, editor, node, grid=None):
        super().__init__(editor, node, grid)
        self.yorg=0
        self.link_starts = [JoinBlockLinkStart(self.diag_editor, self)]
        self.link_destinations = [(0, 0, E)]
        self._avail_out_cons = Iset(range(4))

    # def refresh(self):
    #    x=self.node.position[0]*render_defaults.grid
    #    y=self.node.position[1]*render_defaults.grid
    #    self.canvas.delete(self.outline_id)
    #    self.outline_id=self.canvas.create_oval(x-3,y-3,x+3,y+3,fill='#000')

    def squash(self,x,y,factor):
        self.canvas.delete(self.uid)
        sx, sy = self.centre()
        x=x+(sx-x)/factor
        y=y+(sy-y)/factor
        self.canvas.create_oval(x - 1, y - 1, x + 1, y + 1, tags=self.tags,
                            fill='#000')

    def refresh(self):
        self.canvas.delete(self.uid)
        x, y = self.centre()
        if self.highlighted:
            gs = render_defaults.gs_by3
            fill = '#889'
        else:
            gs = render_defaults.grid//4
            fill = '#000'

        self.canvas.create_oval(x - gs, y - gs, x + gs, y + gs, tags=self.tags, fill=fill)

    def highlight(self, highlight):
        if self.highlighted:
            if not highlight:
                self.highlighted = False
                self.refresh()
        else:
            if highlight:
                self.highlighted = True
                self.refresh()

    def contains_point(self, x, y):
        # print('contains point',x,y)
        xp = self.xpos()
        gs = render_defaults.gs_div2
        if x < xp - gs:
            return False
        if x > xp + gs:
            return False
        yp = self.ypos()
        if y < yp - gs:
            return False
        return y <= yp + gs

    def reset_links(self):
        self._avail_out_cons = Iset(range(4))

    def link_edge(self, conNo):
        return round(self.node.position[0] * render_defaults.grid), round(self.node.position[1] * render_defaults.grid), join_in_dir_map[conNo]

    def reserve_inward_connection(self, sx, sy):
        x, y = self.centre()
        if abs(x - sx) > abs(y - sy):  # ew
            if sx >= x:
                dirn = E
            else:
                dirn = W
        else:
            if sy >= y:
                dirn = S
            else:
                dirn = N
        self._avail_out_cons -= dirn // 2
        return x, y, dirn

    def nearest_out_edge(self, linkNo, tx, ty, allocate: bool):
        x, y = self.centre()
        if abs(x - tx) > abs(y - ty):  # ew
            if tx >= x:
                dirn = E
            else:
                dirn = W
        else:
            if ty >= y:
                dirn = S
            else:
                dirn = N
        if dirn // 2 not in self._avail_out_cons:
            if dirn in (E, W):
                if ty >= y:
                    dirn = S
                else:
                    if tx >= x:
                        dirn = E
                    else:
                        dirn = W
        return x, y, dirn

    def get_link_name(self, _linkNo):
        return ''

    def centre(self):
        return round(self.node.position[0] * render_defaults.grid), round(self.node.position[1] * render_defaults.grid)

    def get_link_arrow(self, linkNo):
        # return arrow coordinate,direction,touching
        # print(f'get_link_arrow called on node:{self.nodeNo},link:{linkNo}')
        if self.node.links[0] == 0:
            x, y, dirn = self.link_edge(1)
            # x=round(x)
            # y=round(y)
            # print('join arrow',arrow_coords(x, y, dirn, render_defaults.grid), dirn)
            return arrow_coords(x, y, dirn, render_defaults.grid), dirn, False
        lix, liy, _ = self.link_destinations[0]
        x, y, dirn = self.nearest_out_edge(0, lix, liy, True)
        return arrow_coords(x, y, dirn, render_defaults.grid), dirn, False


class JoinBlockLinkStart:
    def __init__(self, diag_editor, presenter):
        self.diag_editor = diag_editor
        self.presenter = presenter
        self.canvas = presenter.canvas
        self.touching = False
        self.link_path = []
        self.direction = E
        self.link_no = 0
        self.label = None
        self.uid = f'ln{self.presenter.node_no}#0'
        self.tags = ('link', self.uid)
        self.highlighted = False
        self.draggable=False

    def allocate_ins(self):
        self.presenter.get_target_in_link(self.link_no)

    def allocate_outs(self):
        self.arrow, self.direction, self.touching = self.presenter.get_link_arrow(0)

    def allocate_path(self):
        self.link_path, dirn = self.presenter.getExtendedPath(self)

    def clear_path(self, wherever=None):
        # self.prepareGeometryChange()
        self.link_path = []

    def draw(self):
        #if self.highlighted:
        #    fill = '#f00'
        #else:
        fill = '#000'
        #if self.presenter.node.links[0] != 0:
            # print('should be drawing link arrow here',self.link_path)
        self.canvas.create_line(self.link_path[:4], arrow=tk.LAST, arrowshape=(7, 7, 3), fill=fill,
                                    tag=self.tags + ('arrow',))


        if len(self.link_path) >= 6:
            self.canvas.create_line(self.link_path[2:], arrow=tk.LAST, arrowshape=(7, 7, 3), fill=fill,
                                    tag=self.tags + ('line',))

        if self.highlighted:
            x1,y1,x2,y2=circle_over_line(self.link_path[-4:])
            self.canvas.create_oval(x1, y1, x2,y2, fill='#F00', outline='#F00',
                               tags=self.tags + ('draggable',))

    def highlight(self, highlight):
        if highlight:
            if self.highlighted:
                return
            self.highlighted = True
            self.canvas.delete(self.uid)
            self.draw()
        else:
            if self.highlighted:
                self.highlighted = False
                self.canvas.delete(self.uid)
                self.draw()



def circle_over_line(coords):
    g3=render_defaults.grid//3
    x1,y1,x2,y2=coords
    if x1==x2:
        cy=(y1+y2)//2
        return x1-g3,cy-g3,x1+g3,cy+g3
    cx=(x1+x2)//2
    return cx-g3,y1-g3,cx+g3,y1+g3


class LinkStart:
    #font=None
    def __init__(self, diag_editor, presenter, link_no):
        #if self.font is None:
        #    self.__class__.font=BubblFont().font
        self.font=BubblFont(render_defaults.font).font
        self.diag_editor = diag_editor
        self.canvas = presenter.canvas
        self.presenter = presenter
        self.link_no = link_no
        self.uid = f'ln{presenter.node_no}#{link_no}'
        self.tags = ('link', self.uid)
        #print('LINKSTART For ',presenter.node_no,link_no)
        label = presenter.get_link_name(link_no)
        if label == '':
            self.label = None
        else:
            self.label = label
        #self.label_text = label
        self.highlighted = False

        # self.draggedover.connect(block.canvas.highlight)
        self.link_path = []
        # self.dragstart.connect(self.clear_path)

        # self.arrow = ()
        self.direction = E
        self.touching = False
        self.flash_phase = 0  # controls flashing
        # self.flash_timer = ui.timer()
        # self.flash_timer.timeout.connect(self.flash)
        self.draggable=False

    def allocate_ins(self):
        self.presenter.get_target_in_link(self.link_no)

    def allocate_outs(self):
        self.arrow, self.direction, self.touching = self.presenter.get_link_arrow(self.link_no)

    def allocate_path(self):
        self.link_path, dirn = self.presenter.getExtendedPath(self)
        if self.label is not None:
            self.label_anchor = label_anchor_map[dirn]

    def update_drag_pos(self, x, y):
        self.link_path = self.arrow + [x, y]

    def flash(self):
        # print('flash timer')
        if self.flash_phase == 0:
            self.flash_phase = 1
        else:
            self.flash_phase = 0

    def start_flashing(self, diageditor):
        self.flash_timer.stop()
        self.diageditor = diageditor
        self.diageditor.stop_link_flashing.connect(self.stop_flashing)
        # print('linkstart flash timer started')
        self.flash_timer.start(500)

    def stop_flashing(self):
        # print('linkstart flash timer stopped')
        self.diageditor.stop_link_flashing.disconnect(self.stop_flashing)
        self.flash_phase = 0

    def __str__(self):
        return self.uid

    def clear_path(self, wherever=None):
        # self.prepareGeometryChange()
        self.link_path = []

    def highlight(self, highlight):
        if highlight:
            if self.highlighted:
                return
            self.highlighted = True
            self.canvas.delete(self.uid)
            self.draw()
        else:
            if self.highlighted:
                self.highlighted = False
                self.canvas.delete(self.uid)
                self.draw()
        self.canvas.lift('factory')

    def draw(self):
        if self.highlighted:
            fill = '#f00'
        else:
            fill = '#000'
        fill='#000'
        canvas = self.canvas
        if self.label is not None:
            canvas.create_text(*self.link_path[:2], text=self.label, anchor=self.label_anchor, fill=fill,
                               tags=self.tags + ('label',),font=self.font)
        #if self.presenter.node.links[self.link_no] != 0:
        canvas.create_line(self.link_path[:4], arrow=tk.LAST, arrowshape=(7, 7, 3), fill=fill,
                           tag=self.tags + ('arrow',))
        if len(self.link_path) >= 6:
            x1,y1,x2,y2,*rest=self.link_path
            path=[x2,y2,(x2-x1)//2+x2,(y2-y1)//2+y2]+list(rest)
            canvas.create_line(path,# self.link_path[2:],
                               arrow=tk.LAST, arrowshape=(7, 7, 3), fill=fill,
                           tag=self.tags + ('line',),smooth=True)
            #else:
            #canvas.create_line(self.link_path[:4], arrow=tk.LAST, arrowshape=(7, 7, 3), fill=fill,
            #                   tag=self.tags + ('arrow',))

            #x = self.link_path[2]
            #y = self.link_path[3]
            #canvas.create_oval(x, y, x + grid_size // 2, y + grid_size // 2, fill='', outline=fill,
            #                   tags=self.tags + ('ring_' + self.uid,))
            #print('drawtag','ring_' + self.uid)
        if self.highlighted:
            x1,y1,x2,y2=circle_over_line(self.link_path[-4:])
            canvas.create_oval(x1, y1, x2,y2, fill='#F00', outline='#F00',
                               tags=self.tags + ('draggable',))


