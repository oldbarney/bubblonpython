"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import logging
import os
import tkinter as tk
from collections import deque
from tkinter import Canvas, messagebox

from bubblib.bubbldiag import InterfaceBlock
from bubblib.gutils import BubblFont, brighter, ctrl, icon
from bubblib.inputbox import InputBox
from bubblib.logger import Logger
from bubblib.table import Table
from bubblib.tableeditor import TableEditor
from bubblib.utils import log
from .bin import Bin
#from bubblib.piltkcanvas import PCanvas
from .finder import Finder
from .presenterinfo import InterfacePresenterInfo
from .presenterwidgets import ImageViewPresenter, BubblPresenter, WeblinkPresenter, \
    CommandPresenter, GraphicPresenter
from bubblib.pastings import get_json_for_text_or_list, image_view_text
from .replaceeditor import ReplaceEditor

from bubblib.uiserver import ui, UITimer
from .userpageitemdragger import UserPageItemDragger

if ui.has_dnd:
    from tkinterdnd2 import DND_FILES, DND_TEXT, COPY
else:
    DND_FILES=DND_TEXT=COPY=None

from bubblib.globaldefs import ExState, render_defaults, DiagEditorState, \
    run_control_options, executable_types
from .variablepresenter import TableViewPresenter
from .baseelements import BaseBlockPresenter, BlockPresenter
from bubblib.bubbljson import fromJSON, toJSON
from bubblib.editorframe import EditorWindow
from .factorytoolbar import get_drag_factory
from bubblib.keyhandler import BubblDiagKeyHandler
from .livetextedit import TextPresenter
from bubblib.mywidgets import PopupMenu, HoverTextPresenter
from bubblib.block import ExecutableBlock
from bubblib.blockfactory import CallBlock, JoinBlock, TextBlock, block_factory, \
    ButtonBlock, CheckboxBlock, ChoiceBlock, ChoiceDispBlock, EllipseBlock, \
    ImageBlock, InputDispBlock, LineBlock, PolygonBlock, RadioBlock, \
    ScrollbarBlock, TextEdBlock, WriteBlock, display_blocks, PageBlock, \
    PageCloseBlock, PageClearBlock
from .diagelements import ExecutableBlockPresenter, JoinBlockPresenter, \
    LinkStart, JoinBlockLinkStart, PythonPresenter, DialogPresenter
from bubblib.iset import Iset
from .variablepresenter import VariablePresenter, FormulaPresenter

def get_block_item(diag_editor, node):
    #todo here make a proper map
    if node.type_name == 'PYTHON':
        #print('returning PTHONPErsetbed')
        return PythonPresenter(diag_editor,node)
    elif node.type_name =='DIALOG':
        return DialogPresenter(diag_editor,node)

    elif isinstance(node,JoinBlock):  # todo here tidy -move code to get_block_item
        return JoinBlockPresenter(diag_editor, node)
    elif isinstance(node,InterfaceBlock):
        result=ExecutableBlockPresenter(diag_editor,node)
        result.diag=node.diag
        return result
    elif isinstance(node, ExecutableBlock):
        return ExecutableBlockPresenter(diag_editor,node)
    elif node.type_name == 'TEXT':
        #print('TEXTHERE')
        return TextPresenter(diag_editor, node)
    # elif node.typename=='TABLE':
    #    return TableViewPresenter(diag_editor, node)
    elif node.type_name == 'IMAGE_VIEW':
        return ImageViewPresenter(diag_editor, node)
    elif node.type_name == 'GRAPHIC':
        return GraphicPresenter(diag_editor,node)
    elif node.type_name == 'VARIABLE':
        return VariablePresenter(diag_editor,node)
    elif node.type_name == 'DBVARIABLE':
        return VariablePresenter(diag_editor, node,is_global=True)
    elif node.type_name == 'TABLE':
        return TableViewPresenter(diag_editor, node)
    elif node.type_name == 'FORMULA':
        return FormulaPresenter(diag_editor,node)
    elif node.type_name == 'JOIN':
        return JoinBlockPresenter(diag_editor,node)
    elif node.type_name =='BUBBL':
        return BubblPresenter(diag_editor,node)
    elif node.type_name =='WEBLINK':
        return WeblinkPresenter(diag_editor,node)
    elif node.type_name =='COMMAND':
        return CommandPresenter(diag_editor,node)
    return BlockPresenter(diag_editor, node)

test_defn = {'x': 100, 'y': 100, 'title': 'An input box', 'items': [
    {'type': 'input', 'prompt': 'enter', 'var': 'this', 'default': 'hmmm'},
    {'type': 'assign', 'prompt': 'Let', 'var': 'that2',
     'default': ['this22', 'that22']},
    {'type': 'assign_buts', 'prompt': 'Let', 'var': 'that',
     'default': ['thiis', 'thaat']},
    {'type': 'button', 'prompt': 'Add Item', 'icon': 'ins'},
    {'type': 'check', 'prompt': 'Check this', 'var': 'check', 'default': '1'},
    {'type': 'input', 'prompt': 'longer prompt', 'var': 'that6',
     'default': 'hmmm'},
    {'type': 'radio', 'prompt': 'Radio 4', 'var': 'radio', 'default': 'r4'},
    {'type': 'radio', 'prompt': 'Radio 5', 'var': 'radio', 'default': 'r5'},
    {'type': 'radio_row', 'prompt': 'Channel:', 'var': 'channel',
     'default': 'c4', 'choices': ['bbc1', 'bbc2', 'c4']},
    {'type': 'choice', 'prompt': 'chooose', 'var': 'choice', 'default': 'first',
     'choices': ['first', 'second', 'third']},
    {'type': 'subchoice', 'var': 'subchoice', 'prompt': 'Markup',
     'default': ['reload', '1'],
     'choicemap': {'x-value': 'input',
                   'y-value': 'input',
                   'reload': 'check',
                   'colour:': ['red', 'greeen', 'blue']}}],
             'style': ''}

DRAG_THRESH = 2

fonts = ['TkDefaultFont',
         'TkTextFont',
         'TkHeadingFont',
         'TkCaptionFont',
         'TkTooltipFont',
         'TkFixedFont',
         'TkIconFont',
         'TkMenuFont',
         'TkSmallCaptionFont',
         'Cantarell', 'FreeMono', 'FreeSans', 'FreeSerif','Times','Helvetica','Courier']
from random import choice


def rf():
    return choice(fonts)


valid_mouse_states = {'up': ('overfactory', 'overlink', 'overpresenter',
                        'overpresenterinfo','overdragpoint',
                       'overcanvas', 'overconsole', 'off',
                       'rightclickmenu', 'editingpresenter', 'overedge'),
                'downleft': ('oncanvas', 'onselection', 'onpresenter',
                             'ontyping', 'onfactory', 'onnothing'),
                'downright': ('oncanvas', 'oneditable','onnoneditable',
                              'onselection','onnothing'),
                'draggingleft': ('draggingselection', 'draggingpresenter',
                                 'dragginglink', 'draggingjson',
                                 'draggingdnd', 'rubberbanding', 'sizing',
                                 'draggingtyping', 'sizingeditor',
                                 'movingdragpoint','dragginglocaldnd'),
                'draggingright': ('draggingcanvas', 'draggingnothing',),
                'active': ('running', 'paused'),
                'graphics':('ongraphic',
                            'drawing',
                            'lining',
                            'recting',
                            'ellipsing',
                            'arcing',
                            'cuttingout',
                            'grabbing')
                }

debug_self = None

def debugger(func):
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)
        debug_self.debug()
        return result

    return wrapped

class BubblDiagEditor:
    backgrounds={DiagEditorState.editing: '#E0F0FF',
                 DiagEditorState.restricted_editing: '#CAD8E6',
                 DiagEditorState.disabled:'#B3C0CC',
                 DiagEditorState.activated: '#FFE0E0',
                 DiagEditorState.activated_but_stacked: '#AA8080'}
    local_dnd_json=None

    def __init__(self, ide, window, diag, width=640,height=480,
                 initial_state=DiagEditorState.disabled,contents=None):
        global debug_self
        debug_self=self
        self.ide = ide
        self._uid = None
        self._visible_state=initial_state
        #print('making diag editor with',geom)
        self.window = window
        options = {}
        background=self.backgrounds[initial_state]
        if isinstance(window, EditorWindow):
            self.canvas = Canvas(window.frame, width=width, height=height,
                                 background=background, **options)
            self.canvas.grid(row=1, column=0, sticky='nsew')
        else:
            self.canvas = Canvas(window, width=width, height=height,
                                 background=background, **options)
            self.canvas.grid(row=0, column=0, sticky='nsew')

        self.diag = diag
        self.bbsm = diag.mach
        if contents is None:
            self.presenters = {}
        else:
            self.presenters=contents
            for p in contents.values():
                p.diag_editor=self
                p.canvas=self.canvas

        self.factory = get_drag_factory(self)
        self.bin=None

        # if ui.root.tk.call('tk', 'windowingsystem')=='aqua':
        #    ui.register_event_receiver(self.canvas,'<2>',self.right_click,self)
        #    ui.register_event_receiver(self.canvas,'<Control-1>',self.right_click,self)
        # else:
        #    ui.register_event_receiver(self.canvas,'<3>',self.right_click,self)
        # ui.register_event_receiver(self.canvas,'<1>',self.left_click,self)

        self.canvas.bind('<1>', self.mouse_left_down_event)
        self.canvas.bind('<3>', self.mouse_right_down_event)
        self.canvas.bind('<MouseWheel>',lambda event:self.mouse_wheel(event.delta//60))  # Windows
        self.canvas.bind('<4>', lambda event:self.mouse_wheel(2))  # Windows
        self.canvas.bind('<5>', lambda event:self.mouse_wheel(-2))  # Windows

        self.canvas.bind('<B1-ButtonRelease>', self.mouse_left_release_event)
        self.canvas.bind('<B2-ButtonRelease>', self.mouse_right_release_event)
        self.canvas.bind('<B3-ButtonRelease>', self.mouse_right_release_event)
        self.canvas.bind('<Motion>', self.mouse_move_event)
        self.canvas.bind('<Leave>', self.mouse_leave_event)
        self.canvas.bind('<Enter>', self.mouse_enter_event)
        self.canvas.bind('<Double-Button-1>', self.double_mouse_press)
        if ui.has_dnd:
            self.canvas.drop_target_register(DND_FILES, DND_TEXT)
            self.canvas.dnd_bind('<<Drop>>', self.dnd_drop)
            self.canvas.dnd_bind('<<DropEnter>>', self.dnd_drop_enter)
            self.canvas.dnd_bind('<<DropLeave>>', self.dnd_drop_leave)
            self.canvas.dnd_bind('<<DropPosition>>', self.dnd_drop_position)
            self.canvas.drag_source_register(1, DND_TEXT)
            self.canvas.dnd_bind('<<DragInitCmd>>', self.dnd_drag_start)

        self.dnd_drag_data = None
        self.bubbl_app = None
        self._mouse_state = ['up', 'nowhere']
        self.linking_presenters = []
        self.dragged_join = None
        self._what_mouse_is_over = None  # presenter or linkstart
        self.right_clicked_presenter=None
        self.active_text_editor = None
        self.redraw()
        self.active_widget = None
        self.selection = set()
        self.hit_x = 0
        self.hit_y = 0
        self.hit_x_root = 0
        self.hit_y_root = 0
        self.sizing_widget = None
        self.vm = ide.edvm
        self.remove_empty_text_blocks()
        self.rubberband_xo = 0
        self.rubberband_yo = 0
        self.rubberband = -1
        self.text_x = 0
        self.text_y = 0
        self.edge = None
        self.size_width = None
        self.size_height = None
        self.key_handler = BubblDiagKeyHandler(self)
        self.new_inst_json = None
        self.debug_tag = 'debug'

        self.active_flash_timer = ui.flasher(self.show_active, self.hide_active)
        self.find_flash_timer=ui.flasher(self.show_finds,self.hide_finds)
        self.finds={}
        self.find_settings={}
        self._active_node = 0
        self._visible_state=initial_state
        self.hover_timer=None
        self.next_hover_item=None
        self.current_graphic_item=None
        self.user_page_item_dragger=None
        self.user_page_mouse_queue=deque(maxlen=20)
        self.delayed_user_mouse_event=None
        self.last_user_mouse_event=None
        self.ready_for_user_page_editing=False
        self.last_table_fieldnames=[]
        self.non_active_over_executable=None

    def screen_xy(self):
        x=self.ide.desktop_window.winfo_x()
        y=self.ide.desktop_window.winfo_y()
        if isinstance(self.window,EditorWindow):
            x+=self.window.frame.winfo_x()+2
            y+=self.window.frame.winfo_y()+2
        return x,y

    def handle_user_page_event(self,node,item,event):
        self.user_page_mouse_queue.append((node,item,event))
        if self.delayed_user_mouse_event is None:
            #print('Delaying call to mouse event')
            self.delayed_user_mouse_event= self.canvas.after(
                20,self.user_page_mouse_event)

    def user_page_mouse_event(self):
        self.delayed_user_mouse_event=None
        moved=False
        mx=0
        my=0
        last_node=None
        while self.user_page_mouse_queue:
            (node,item,event)=self.user_page_mouse_queue.popleft()
            if node is None:
                node=last_node
            else:
                last_node=node

            if event.event_type=='MouseDn':
                if node not in self.presenters:
                    continue
                pres=self.presenters[node]
                if pres.editor is not None:
                    continue
                self.user_page_item_dragger=UserPageItemDragger(
                    item,
                    self.diag.nodes[node],
                    event.x,
                    event.y
                )
            elif event.event_type=='MouseUp':
                if self.user_page_item_dragger is not None:
                    self.user_page_item_dragger.node.compile_code()
                    self.user_page_item_dragger=None
                    moved=False
                    self.redraw()
                    self.redraw_live_data()
            elif event.event_type=='MouseMv':
                if self.user_page_item_dragger is not None:
                    mx=event.x
                    my=event.y
                    moved=True
        if moved:
            self.user_page_item_dragger.mouse_move(mx,my)
            if node is not None: # this is very defensive - always true
                self.presenters[node].refresh()
            #else:
            #print('NODE WAS NONE')

    def hovered(self,block):
        self.canvas.delete('info')
        self.canvas.create_image(
            block.xpos(),
            block.ypos(),
            image=icon('info'),
            anchor='center', tags=['info','widget',block.uid])

    def clear_hover(self,caller=None):
        if self.hover_timer is not None:
            self.canvas.after_cancel(self.hover_timer)
            self.hover_timer=None
        self.next_hover_item=None
        self.canvas.delete('info')

    def mouse_wheel(self,dy):
        if self.mouse !='up':
            return
        for presenter in self.presenters.values():
            self.canvas.move(presenter.uid,0,dy*render_defaults.grid)
        self.vm.translate_nodes(self.diag,Iset(self.presenters),0,dy,True)
        self.redraw_links()

    @property
    def what_mouse_is_over(self):
        return self._what_mouse_is_over

    @what_mouse_is_over.setter
    def what_mouse_is_over(self,what):
        if isinstance(what,BlockPresenter):
            if what is not self.next_hover_item:
                self.clear_hover()
                self.hover_timer=self.canvas.after(2000,self.hovered,what)
                self.next_hover_item=what
        else:
            self.clear_hover()
        self._what_mouse_is_over=what

    @property
    def useful_parent(self):
        if isinstance(self.window, EditorWindow):
            return self.window.frame
        else:
            return self.window

    def sx(self):
        if isinstance(self.window, EditorWindow):
            return round(self.ide.desktop_window.winfo_x() + self.window.geometry()[0])
        return round(self.window.winfo_x())

    def sy(self):
        if isinstance(self.window, EditorWindow):
            return round(self.ide.desktop_window.winfo_y() + self.window.geometry()[1])
        return round(self.window.winfo_y())

    @property
    def name(self):
        return self.diag.name

    @property
    def uid(self):
        return self.window.uid

    @property
    def visible_state(self):
        return self._visible_state
    @visible_state.setter
    def visible_state(self,value):
        if value==self._visible_state:
            return
        self._visible_state=value
        if value!=DiagEditorState.activated:
            self.deactivate_flasher()
        if value==DiagEditorState.editing:
            self.factory.draw()
        else:
            self.factory.hide()
            self.deactivate_text_editor()
        self.canvas.configure(bg=self.backgrounds[value])

    def __str__(self):
        return f'BubblDiagEditor:{self.name} with {len(self.diag.nodes)} blocks'

    def select(self):
        #print('Being selected',self.name)
        #print('SELECTING EDITOR',repr(self.diag.mach.state))
        if self.diag.mach.state in (ExState.quiescent,
                                    ExState.stopped_on_link,
                                    ExState.stopped_on_node):
            self.factory.refresh()
            new_state=DiagEditorState.editing
        else:
            new_state=DiagEditorState.restricted_editing
        if self.name == 'main':
            self.window.focus_set()  # grab_set()#focus_get()aasa
        else:
            self.window.frame.focus_set()
        self.visible_state=new_state
        #print('EDITOR NEW STATE',self.name, repr(self.visible_state))

        self.ready_for_user_page_editing=new_state==DiagEditorState.editing

    def deselect(self):
        #print('DESELECTING',self.name)
        self.visible_state=DiagEditorState.disabled
        self.ready_for_user_page_editing=False

    @property
    def current(self):
        return self._visible_state in (
            DiagEditorState.editing,
            DiagEditorState.restricted_editing,
            DiagEditorState.activated
        )

    def set_visible_state(self):
        mach_state=self.diag.mach.state
        if mach_state==ExState.quiescent:
            if self.visible_state==DiagEditorState.activated:
                self.select()
            elif self.visible_state==DiagEditorState.restricted_editing:
                self.select()
            elif self.visible_state!=DiagEditorState.editing:
                self.deselect()
        elif mach_state==ExState.active:
            if self.visible_state==DiagEditorState.editing:
                self.deselect()
                self.visible_state=DiagEditorState.restricted_editing
        elif mach_state==ExState.stopped_on_node:
            if self.diag.mach.diag==self.diag:
                self.visible_state=DiagEditorState.activated
                self.activate_flasher(self.diag.mach.node)
                self.redraw_live_data()
            elif self.ide.is_stacked(self.diag):
                self.visible_state=DiagEditorState.activated_but_stacked
                self.redraw_live_data()
            else:
                self.visible_state=DiagEditorState.disabled
        elif mach_state==ExState.stopped_on_link:

            if self.diag.mach.diag==self.diag:
                self.visible_state=DiagEditorState.activated
                self.activate_flasher(self.diag.mach.last_node, self.diag.mach.link)
                self.redraw_live_data()
            elif self.ide.is_stacked(self.diag):
                self.visible_state=DiagEditorState.activated_but_stacked
                self.redraw_live_data()
            else:
                #print('SET_VISIBLE_STATE setting disabled 2',self.name)
                self.visible_state=DiagEditorState.disabled
        elif mach_state==ExState.exited:
            if self.diag.mach.diag==self.diag:
                self.visible_state=DiagEditorState.editing
                self.redraw_live_data()
            else:
                #print('SET_VISIBLE_STATE setting disabled 3',self.name)
                self.visible_state=DiagEditorState.disabled

    def deactivate_flasher(self):
        self.active_flash_timer.stop()
        self.mouse_state = 'up', 'off'
        #self.redraw_live_data()

    @property
    def active_node(self):
        return self._active_node
    @active_node.setter
    def active_node(self,value):
        try:
            assert(isinstance(value,int))
        except Exception as e:
            print(f'ACTIVE NODE IS >{value}<')
            raise e
        self._active_node=value

    def activate_flasher(self, node_no, link_no=None):
        self.active_node = node_no
        self.active_link = link_no
        self.active_flash_timer.start(300, 200)
        # self.redraw_live_data()

    def show_active(self):
        if self.active_link is None:
            pres = self.presenters[self.active_node]
            self.canvas.create_rectangle(pres.xpos() - 3, pres.ypos() - 2,
                                         pres.xpos() + pres.scaled_width() + 3,
                                         pres.ypos() + pres.scaled_height() + 3,
                                         outline='#F00', width=6,
                                         tags=('flash_rect',))
        else:
            try:
                link=self.presenters[self.active_node].link_starts[self.active_link]
                link.highlight(True)
            except Exception as e:
                pass

    def hide_active(self):
        if self.active_link is None:
            self.canvas.delete('flash_rect')
        else:
            try:
                link=self.presenters[self.active_node].link_starts[self.active_link]
                link.highlight(False)
            except Exception as e:
                pass

    def get_window_details(self):
        return self.window.geometry_and_state()

    def mouse_leave_event(self, event):
        #print('mouse has left',self.name)
        #self.clear_hover()
        self.canvas['cursor']='arrow'
        self.clear_hover()
        return 'break'

        if self.visible_state==DiagEditorState.editing:
            self.factory.mouse_over(-20, -20)
        # if self.mouse=='up':
        #    self.mouse_state='up','off'

    def mouse_enter_event(self, event):
        #print('mouse has entered',self.name)
        self.clear_hover()
        if self.local_dnd_json is not None:
            self.select()
            self.canvas['cursor']='hand1'
        return 'break'

    def debug(self):
        #print('debugging',self.name)
        try:
            self.canvas.delete(self.debug_tag)
        except AttributeError:
            return
        try:
            mess = f'typ  {self.mouse},{self.mouse_substate} {self.what_mouse_is_over.type}'
        except:
            mess = f'wid  {self.mouse},{self.mouse_substate} {self.what_mouse_is_over}'
        # mess=f'uicallstack={len(ui.client_call_queue)} {mess}'
        self.canvas.create_text(30, 480, text=mess, tags=(self.debug_tag,),
                                anchor='nw',font=BubblFont().font)

    def xy(self, event):
        return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    def update_cursor(self):
        if self.mouse == 'up':
            cursor_map = {
                'right': 'right_side',
                'bottomright': 'bottom_right_corner',
                'bottom': 'bottom_side',
                'bottomleft': 'bottom_left_corner',
                'left': 'left_side',
                None: 'arrow'
            }
            self.canvas['cursor']=cursor_map[self.edge]
            return

        if self.mouse in ('draggingleft', 'draggingright'):
            if self.mouse_substate in ('sizing', 'sizingeditor'):
                pass  # self.canvas.config(cursor='sb_right_arrow')
            elif self.mouse_substate == 'movingdragpoint':
                self.canvas['cursor']='dot'
            elif self.mouse_substate =='dragginglocaldnd':
                self.canvas['cursor']='hand1'
            else:
                self.canvas['cursor']='fleur'
            return
        if self.mouse =='graphics':
            cursor_map= {
                'up':'pencil',
                'lining':'crosshair',
                'drawing':'pencil',
                'recting':'crosshair',
                'ellipsing':'crosshair',
                'arcing':'crosshair',
                'cuttingout':'crosshair',
                'sizing':'sizing',
                'grabbing':'crosshair'
            }
            cursor=cursor_map[self.mouse_substate]
            if cursor.startswith('@'):
                self.canvas.config(cursor=cursor)
            else:
                self.canvas['cursor']=cursor

            return
        self.canvas['cursor']='arrow'

    @property
    def mouse_state(self):
        return self._mouse_state

    @mouse_state.setter
    def mouse_state(self, value):
        if value[0] not in valid_mouse_states:
            raise Exception('INVALID mouse ASSIGNMENT:' + value[0])

        if value[1] not in valid_mouse_states[value[0]]:
            raise Exception(
                f'INVALID state assigment:{value[1]} not valid for {value[0]}')
        self._mouse_state[0], self.mouse_state[1] = value
        self.update_cursor()
        #self.debug()

    @property
    def mouse(self):
        return self._mouse_state[0]

    @property
    def mouse_substate(self):
        return self._mouse_state[1]

    @mouse_substate.setter
    def mouse_substate(self, value):
        if value not in valid_mouse_states[self.mouse]:
            raise Exception(
                f'INVALID state assigment:{value} not valid for {self.mouse}')
        self._mouse_state[1] = value
        #self.debug()

    def highlight_finds(self,finds,find_settings):
        if finds is not None:
            self.finds=finds
            self.find_settings=find_settings
            self.activate_find_flasher()
            log('highlighten finds',self.finds) #flash
        else:
            log('DE-HIGHLIGHTING FINDS')
            self.finds={}
            self.deactivate_find_flasher()

    def deactivate_find_flasher(self):
        self.find_flash_timer.stop()
        self.redraw_live_data()
        self.hide_finds()

    def activate_find_flasher(self):
        # self.stop_link_flashing.emit()
        log('find flash timer starting')
        self.find_flash_timer.start(300, 200)
        # self.redraw_live_data()

    def show_finds(self):
        #print('showing finds')

        for find in self.finds:
            try:
                widget=self.presenters[find]
                x1=min(self.useful_parent.winfo_width()-10,widget.xpos()),
                x2=max(widget.xpos()+widget.scaled_width(),10)
                y1=min(self.useful_parent.winfo_height()-10,widget.ypos()),
                y2=max(widget.ypos()+widget.scaled_height(),10)

                self.canvas.create_rectangle(x1,y1,x2,y2,
                    width=8,
                    outline='#f0f',
                    tags=['found']
                )
            except KeyError:  #In case editing deleted something
                pass

    def hide_finds(self):
        #print('hiding finds')
        self.canvas.delete('found')


    def get_presenter_from_tags(self, tags):
        if 'widget' not in tags:
            return None
        for tag in tags:
            if tag.startswith('wn'):
                try:
                    return self.presenters[int(tag[2:])]
                except Exception as e:
                    log(f'PROBLEM WITH TAG >{tag}<  :{e}')
        return None

    def get_link_from_tags(self, tags):
        #print(tags)
        if 'link' not in tags:
            return None
        for tag in tags:
            if tag.startswith('ln'):
                n, l = tag[2:].split('#')
                return self.presenters[int(n)].link_starts[int(l)]
        return None

    def redraw_live_data(self):

        #print('bubbldiageditor REDRAWING LIVE DATA')
        #if self.visible_state==DiagEditorState.editing:
        #    factorytoolbar.redo_vars(self.factory, self)
        #print('REDONE VARS')
        # self.factory.draw(full=True)

        for pres in self.presenters.values():
            #print('LIVE_ITEM',pres)
            if pres.live_data:
                pres.info.cache.clear()
                pres.refresh()

    def redraw_calls(self,to):
        for node in self.diag.nodes:
            if (self.diag.nodes[node].type_name=='CALL' and
                self.diag.nodes[node].params[0]==to):
                self.presenters[node].refresh()
        self.redraw()

    def redraw(self,do_all=False):
        #print('bubbldiageditor REDRAWING', self.name,time.perf_counter())

        if do_all:
            to_remove=Iset(self.presenters)
        else:
            to_remove = Iset(self.presenters) - Iset(self.diag.nodes) - 0
        #print('REMOVALS', to_remove)
        #ttorg = torg = time.perf_counter()
        #longest = None, 0
        for node in to_remove:
            pres = self.presenters[node]
            if pres.editor is not None:
                if isinstance(pres.editor,TableEditor):
                    pres.editor.close(update=False) #
                else:
                    pres.editor.close()
            self.canvas.delete(pres.uid) #todo here check this is correct
            self.presenters.pop(pres.node_no)
        #nt = time.perf_counter()
        #longest = 'removals', nt - torg
        #torg = nt
        for (node, block) in self.diag.nodes.items():
            if node not in self.presenters:
                self.presenters[node] = get_block_item(self, block)
            self.presenters[node].refresh()
        self.redraw_links()
        if self.visible_state==DiagEditorState.editing:
            self.factory.refresh()
        else:
            self.factory.hide()
        #print('diadeditor redraw slowest', self.diag.name, longest[0], longest[1], 'total',
        #      torg - ttorg)

    #def dont_redraw_links(self):
    #    try:
    #        self.do_redraw_links()
    #    except Exception as e:
    #        pass
    #        #print('REDRAW LINKS EXCEPTION',e)

    def redraw_links(self):
        self.canvas.delete('link')
        to_link = set(pres for pres in self.presenters.values() if
                      isinstance(pres, ExecutableBlockPresenter))
        #print('SHONWONG TO LIONK',to_link)
        for pres in to_link:
            pres.reset_links()
        for pres in to_link:
            for start in pres.link_starts:
                start.allocate_ins()
        for pres in to_link:
            for start in pres.link_starts:
                try:
                    start.allocate_outs()
                except Exception as e:
                    log(self.diag.name,'UNABLE to allocates outs for',
                        pres.node.type_name,e,level=Logger.INFO)
        for pres in to_link:
            for start in pres.link_starts:
                try:
                    start.allocate_path()
                except Exception as e:
                    log(self.diag.name,'UNABLE to allocate path for',
                          pres.node.type_name,e,level=Logger.INFO)

        for pres in to_link:
            for start in pres.link_starts:
                try:
                    start.draw()
                except Exception as e:
                    log(self.diag.name,'UNABLE to draw start for',
                          pres.node.type_name,e,level=Logger.INFO)
        if self.visible_state==DiagEditorState.editing:
            self.canvas.lift('factory')

    def get_links_to(self,node_no):
        result=[]
        for n in self.diag.nodes:
            for ln,l in enumerate(self.diag.nodes[n].links):
                if l==node_no:
                    result.append((self.presenters[n],ln))
        return result

    #@debugger
    def mouse_left_down_event(self, event):
        #print(event.x)
        #print('diag editor CANVAS mouse_left_down_event',event,self.name, self.current)
        #print('event.state',hex(event.state))
        #print('LD',self.mouse_substate)
        #print(self.diag.mach.find('tt',False,False,'Current block'))

        self.canvas.delete('info')
        if self.finds and not self.find_settings:
            self.ide.found(None,None,None)
        if not self.current:
            try:
                self.ide.select_editor_for_editing(self.name)
            except KeyError:  #todo fix this hack to cover changing apps bug
                pass
            return
        self.hit_x = event.x
        self.hit_x_root = event.x_root
        self.hit_y = event.y
        self.hit_y_root = event.y_root
        self.dnd_drag_data = None
        self.__class__.local_dnd_json = None

        x, y = self.xy(event)
        if self.mouse == 'up':
            if self.mouse_substate == 'overfactory':
                self.clear_selection()
                self.deactivate_text_editor()
                self.mouse_state = 'downleft', 'onfactory'
                if self.factory.hl_widget is not None:
                    self.new_inst_json = self.factory.hl_widget.create(x, y)
                else:
                    self.new_inst_json = None
                return
            if self.mouse_substate == 'overedge':
                _, _, self.size_width, self.size_height = self.get_window_details()
                self.mouse_state = 'draggingleft', 'sizingeditor'
                return
            if self.mouse_substate=='overdragpoint':
                self.what_mouse_is_over.set_move_origin(self.hit_x,self.hit_y)
                self.mouse_state='draggingleft','movingdragpoint'
                return

        if self.mouse=='graphics':
            self.vm.mark()
            if self.mouse_substate=='drawing':
                line_block=f"""{{"1":
    {{"params": ["line","[0,0,0,0]",["colour","{self.ide.pen_colour}"],
                                    ["line_width","{self.ide.line_width()}"],
                                    ["ends","{self.ide.line_ends()}"],
                                    ["joins","{self.ide.line_joins()}"]
                                    ],
        "type": "GRAPHIC", 
        "size": [0,0],
        "pos": [0,0],
        "links":[] }}}}"""
                new_no = max(list(self.diag.nodes)) + 1
                self.vm.add_blocks_from_json(
                    self.diag,
                    line_block,
                    Iset(new_no), False, [x, y])
                presenter=get_block_item(self, self.diag.nodes[new_no])
                self.current_graphic_item=presenter
                #print('self.current_graphic_item is',presenter.__class__)
                self.presenters[new_no] = presenter
                presenter.refresh()
                self.redraw()
                return
            elif self.mouse_substate=='recting':
                rect_block=f"""{{"1":
    {{"params": ["rect","[0,0,0,0]",["colour","{self.ide.pen_colour}"],
                                    ["active_colour","{brighter(self.ide.pen_colour)}"],
                                    ["fill","{self.ide.shape_fill}"],
                                    ["line_width","{self.ide.line_width()}"]
                                    ],
        "type": "GRAPHIC", 
        "size": [1,1],
        "pos": [0,0],
        "links":[] }}}}"""
                new_no = max(list(self.diag.nodes)) + 1
                self.vm.add_blocks_from_json(
                    self.diag,
                    rect_block,
                    Iset(new_no), False, [x, y])
                presenter=get_block_item(self, self.diag.nodes[new_no])
                presenter.indexo=2
                presenter.set_move_origin(self.hit_x,self.hit_y)
                self.current_graphic_item=presenter
                #print('self.current_graphic_item is',presenter.__class__)
                self.presenters[new_no] = presenter
                presenter.refresh()
                self.redraw()
                return

            elif self.mouse_substate=='grabbing':
                rect_block=f"""{{"1":
    {{"params": ["rect","[0,0,0,0]",["fill",""]],
        "type": "GRAPHIC", 
        "size": [1,1],
        "pos": [0,0],
        "links":[] }}}}"""
                new_no = max(list(self.diag.nodes)) + 1
                self.vm.add_blocks_from_json(
                    self.diag,
                    rect_block,
                    Iset(new_no), False, [x, y])
                presenter=get_block_item(self, self.diag.nodes[new_no])
                presenter.indexo=2
                presenter.set_move_origin(self.hit_x,self.hit_y)
                self.current_graphic_item=presenter
                self.presenters[new_no] = presenter
                presenter.refresh()
                self.redraw()
                return

            elif self.mouse_substate=='ellipsing':
                ellipse_block=f"""{{"1":
    {{"params": ["ellipse","[0,0,0,0]",["colour","{self.ide.pen_colour}"],
                                    ["active_colour","{brighter(self.ide.pen_colour)}"],
                                    ["fill","{self.ide.shape_fill}"],
                                    ["line_width","{self.ide.line_width()}"]
                                    ],
        "type": "GRAPHIC", 
        "size": [1,1],
        "pos": [0,0],
        "links":[] }}}}"""

                new_no = max(list(self.diag.nodes)) + 1
                self.vm.add_blocks_from_json(
                    self.diag,
                    ellipse_block,
                    Iset(new_no), False, [x, y])
                presenter=get_block_item(self, self.diag.nodes[new_no])
                presenter.indexo=2
                presenter.set_move_origin(self.hit_x,self.hit_y)
                self.current_graphic_item=presenter
                #print('self.current_graphic_item is',presenter.__class__)
                self.presenters[new_no] = presenter
                presenter.refresh()
                self.redraw()
                return

            elif self.mouse_substate=='arcing':
                arc_block=f"""{{"1":
    {{"params": ["arc","[0,0,0,0]",["colour","{self.ide.pen_colour}"],
                                    ["active_colour","{brighter(self.ide.pen_colour)}"],
                                    ["fill","{self.ide.shape_fill}"],
                                    ["line_width","{self.ide.line_width()}"],
                                    ["start","0"],
                                    ["angle","90"]
                                    ],
        "type": "GRAPHIC", 
        "size": [1,1],
        "pos": [0,0],
        "links":[] }}}}"""

                new_no = max(list(self.diag.nodes)) + 1
                self.vm.add_blocks_from_json(
                    self.diag,
                    arc_block,
                    Iset(new_no), False, [x, y])
                presenter=get_block_item(self, self.diag.nodes[new_no])
                presenter.indexo=2
                presenter.set_move_origin(self.hit_x,self.hit_y)
                self.current_graphic_item=presenter
                #print('self.current_graphic_item is',presenter.__class__)
                self.presenters[new_no] = presenter
                presenter.refresh()
                self.redraw()
                return

            elif self.mouse_substate=='lining':
                things = list(self.canvas.find_overlapping(x - 2, y - 2, x + 2, y + 2))
                things.reverse()
                for id_no in things:
                    tags = self.canvas.gettags(id_no)
                    pres = self.get_presenter_from_tags(tags)
                    if (isinstance(pres,GraphicPresenter)
                            and pres.params[0]=='line'):
                        if pres.over_point(-2,x,y):
                            self.current_graphic_item=pres
                            pres.set_move_origin(self.hit_x,self.hit_y)
                            pres.add_point(x,y,force=True)
                            pres.reload()
                            pres.refresh()
                            self.redraw()
                            return
                line_block=f"""{{"1":
    {{"params": ["line","[0,0,0,0]",["colour","{self.ide.pen_colour}"],
                                    ["active_colour","{brighter(self.ide.pen_colour)}"],
                                    ["line_width","{self.ide.line_width()}"],
                                    ["ends","{self.ide.line_ends()}"],
                                    ["joins","{self.ide.line_joins()}"]
                                    ],
        "type": "GRAPHIC", 
        "size": [1,1],
        "pos": [0,0],
        "links":[] }}}}"""
                new_no = max(list(self.diag.nodes)) + 1
                self.vm.add_blocks_from_json(
                    self.diag,
                    line_block,
                    Iset(new_no), False, [x, y])
                presenter=get_block_item(self, self.diag.nodes[new_no])
                presenter.indexo=2
                presenter.set_move_origin(self.hit_x,self.hit_y)
                self.current_graphic_item=presenter
                #print('self.current_graphic_item is',presenter.__class__)
                self.presenters[new_no] = presenter
                presenter.refresh()
                self.redraw()
                return
            elif self.mouse_substate=='cuttingout':
                things = list(self.canvas.find_overlapping(x - 2, y - 2, x + 2, y + 2))
                things.reverse()
                for id_no in things:
                    tags = self.canvas.gettags(id_no)
                    pres = self.get_presenter_from_tags(tags)
                    if (isinstance(pres,GraphicPresenter)
                            and pres.params[0]=='line'):
                        if pres.over_point(-2,x,y):
                            self.current_graphic_item=pres
                            pres.set_move_origin(self.hit_x,self.hit_y)
                            pres.add_point(x,y,force=True)
                            pres.reload()
                            pres.refresh()
                            self.redraw()
                            return
                line_block=f"""{{"1":
    {{"params": ["line","[0,0,0,0]",["colour","#A00"],["fill",""]],
        "type": "GRAPHIC", 
        "size": [1,1],
        "pos": [0,0],
        "links":[] }}}}"""
                new_no = max(list(self.diag.nodes)) + 1
                self.vm.add_blocks_from_json(
                    self.diag,
                    line_block,
                    Iset(new_no), False, [x, y])
                presenter=get_block_item(self, self.diag.nodes[new_no])
                presenter.indexo=2
                presenter.set_move_origin(self.hit_x,self.hit_y)
                self.current_graphic_item=presenter
                #print('self.current_graphic_item is',presenter.__class__)
                self.presenters[new_no] = presenter
                presenter.refresh()
                self.redraw()
                return

        if self.mouse_substate=='overpresenterinfo':
            self.mouse_state='up','off'
            try:
                HoverTextPresenter(self,self.next_hover_item.node)
                self.clear_hover()
            except:
                pass
            return

        over = self.what_mouse_is_over
        if over is None:
            self.clear_selection()
            self.mouse_state = 'downleft', 'oncanvas'
            return
        self.vm.mark()

        if over in self.selection:
            if ctrl(event):  #todo here make ctrl adding/removing from selection
                sel = Iset(pres.node_no for pres in self.selection) - 0
                #print('sel=', sel)
                if sel:
                    data=self.diag.get_json_for_nodes(sel)
                    if ui.has_dnd:
                        self.dnd_drag_data = data
                    else:
                        BubblDiagEditor.local_dnd_json = data
                    self.mouse_state = 'downleft', 'onselection'
                    return
            self.mouse_state = 'downleft', 'onselection'
            return
        if isinstance(over, BaseBlockPresenter):
            if over.node_no in self.finds:
                #print('self.find_settings',self.find_settings)
                find=self.find_settings['find']
                replace=self.find_settings['replace']
                cased=self.find_settings['cased']
                whole=self.find_settings['whole']


                ReplaceEditor(self,
                    self.what_mouse_is_over,
                    find,cased,whole,replace)
                return

            if ctrl(event):
                sel = Iset(over.node_no) - 0
                if sel:
                    data=self.diag.get_json_for_nodes(sel)
                    if ui.has_dnd:
                        self.dnd_drag_data = data
                    else:
                        BubblDiagEditor.local_dnd_json = data
                self.mouse_state = 'downleft', 'onselection'
                return
        self.clear_selection()

        if over == self.active_text_editor:
            self.mouse_state = 'downleft', 'ontyping'
            self.active_text_editor.mouse_down(x, y)
            return

        self.deactivate_text_editor()

        if isinstance(over, JoinBlockPresenter) and over.node.links[0] == 0:
            self.linking_presenters=self.get_links_to(over.node_no)
            self.dragged_join = over
            self.what_mouse_is_over = None
            self.mouse_state = 'draggingleft', 'dragginglink'
            self.update_link_drag_pos(event.x, event.y)
            self.dragged_join.start_dragging(event.x, event.y)
            return

        if isinstance(over, BaseBlockPresenter):
            if self.edge is not None:
                self.sizing_widget = over
                over.start_sizing(event.x, event.y)
                self.mouse_state = 'draggingleft', 'sizing'
            else:
                self.mouse_state = 'downleft', 'onpresenter'
                self.vm.undo()
            return
        elif isinstance(over,
                        (LinkStart, JoinBlockLinkStart)):
            #if not over.draggable:
            #    self.mouse_state='downleft','oncanvas'
            #    return
            #print('DOWN ON',over)

            pres=over.presenter
            link_no=over.link_no
            self.linking_presenters=[(pres,link_no)]

            x, y = self.xy(event)
            new_no = max(list(self.diag.nodes)) + 1

            link = pres.node.links[link_no]
            if (link != 0 and isinstance(self.diag.nodes[link], JoinBlock) and
                    self.diag.nodes[link].links[0] == 0):
                self.dragged_join = self.presenters[link]
                self.clear_selection()
                self.update_link_drag_pos(event.x, event.y)
                self.dragged_join.start_dragging(event.x, event.y)
                self.what_mouse_is_over=None
                self.mouse_state = 'draggingleft', 'dragginglink'
                return

            self.vm.add_blocks_from_json(self.diag,
                                         f'{{"1":{{"params":[],"type":"JOIN","size":[0,0],"pos":[0,1],"links":[0,0]}}}}',
                                         Iset(new_no), True,
                                         [x, y - render_defaults.grid])
            for (pres,link) in self.linking_presenters:
                self.vm.make_link(self.diag, pres.node_no, link, new_no, True)
            self.dragged_join = self.presenters[new_no] = JoinBlockPresenter(
                self, self.diag.nodes[new_no])
            self.dragged_join.start_dragging(event.x, event.y)
            self.dragged_join.refresh()
            self.clear_selection()
            self.mouse_state = 'draggingleft', 'dragginglink'
            self.redraw_links()
            return

    def double_mouse_press(self, event):
        if self.visible_state!=DiagEditorState.editing:
            self.ide.console.tell_machine.emit('edit')
            return
        self.determine_what_mouse_is_over(event)
        over = self.what_mouse_is_over

        if isinstance(
            over,ExecutableBlockPresenter) and not self.diag.mach.is_active():
            #print('SELECTING NODE FOR EXECUTION')
            self.mouse_state = 'active', 'paused'
            if over.node_no==0:
                node_no=self.diag.links[0]
            else:
                node_no=over.node_no
            if node_no!=0:
                self.ide.console.select_node(self.name,node_no)
        elif isinstance(over,BaseBlockPresenter) and over.executable:
            over.execute()
        else:
            self.active_flash_timer.stop()

    #@debugger

    def executable_block_under_mouse(self,event):
        x, y = self.xy(event)
        things = list(self.canvas.find_overlapping(x - 2, y - 2, x + 2, y + 2))
        things.reverse()
        for id_no in things:
            tags = self.canvas.gettags(id_no)
            #print('tags',id_no,tags)
            pres = self.get_presenter_from_tags(tags)
            #print(pres)
            if pres is not None:
                if not pres.contains_point(x, y):
                    continue
                if isinstance(pres,ExecutableBlockPresenter):
                    if pres.node_no!=0:
                        return pres
        return None

    def determine_what_mouse_is_over(self, event):
        #print('determining what mouse is over in',self.name)
        # return widget,edge,link
        # priority: widget_edge,widget,link
        if not self.current:
            return
        x, y = self.xy(event)
        if self.mouse == 'up':
            if self.visible_state==DiagEditorState.editing:
                self.factory.mouse_over(x, y)
                if self.factory.hl_col is not None or self.factory.hl_widget is not None:
                    self.edge = None
                    self.mouse_substate = 'overfactory'
                    self.what_mouse_is_over = self.factory
                    return
            if isinstance(self.window, EditorWindow):
                right = x > self.canvas.winfo_width() - 10
                bottom = y > self.canvas.winfo_height() - 10
                if right or bottom:
                    if right and bottom:
                        edge = 'bottomright'
                    elif right:
                        edge = 'right'
                    else:
                        edge = 'bottom'
                    _, _, self.size_width, self.size_height = self.get_window_details()
                    self.edge = edge
                    self.mouse_state = 'up', 'overedge'
                    self.what_mouse_is_over = None
                    return
                else:
                    self.edge = None
            else:
                self.edge = None

        last = self.what_mouse_is_over
        things = list(self.canvas.find_overlapping(x - 2, y - 2, x + 2, y + 2))
        things.reverse()
        if self.mouse == 'up':
            for id_no in things:
                tags = self.canvas.gettags(id_no)

                #print('tags',id_no,tags)
                pres = self.get_presenter_from_tags(tags)

                #print('pres',pres)
                if pres is not None:

                    if isinstance(pres,GraphicPresenter):
                        if 'graphics' in tags:
                            self.mouse_substate='overdragpoint'
                            for tag in tags:
                                if tag.startswith('pn'):
                                    pn=int(tag[2:])
                                    pres.indexo=pn
                                    break
                            else:
                                log('FAILED TO IDENTIFY DRAG TAG',tags,
                                    level=Logger.INFO)
                        else:
                            self.mouse_substate='overpresenter'
                        self.what_mouse_is_over=pres
                        return
                    if 'info' in tags:
                        pres.highlight(True)
                        self.what_mouse_is_over = pres
                        self.mouse_substate = 'overpresenterinfo'
                        return

                    if  not pres.contains_point(x, y):
                        #print('nopoint')
                        continue
                    if isinstance(pres, BlockPresenter):
                        self.edge = pres.get_hit_edge(x - pres.xpos(),
                                                      y - pres.ypos())
                    else:
                        self.edge = None
                    if self.edge is not None:
                        pass#self.clear_hover()
                    elif 'info' in tags:
                        pres.highlight(True)
                        self.what_mouse_is_over = pres
                        self.mouse_substate = 'overpresenterinfo'
                        return
                    if pres == last:
                        if self.mouse_substate=='overpresenterinfo':
                            self.mouse_substate='overpresenter'
                        return pres
                    if last is not None:
                        if last not in self.selection:
                            if last is not self.factory:
                                last.highlight(False)
                    #print('calling highlight true')
                    pres.highlight(True)
                    self.what_mouse_is_over = pres
                    self.mouse_substate = 'overpresenter'
                    return

            for id_no in things:
                tags = self.canvas.gettags(id_no)

                if self.visible_state==DiagEditorState.editing:
                    link = self.get_link_from_tags(tags)
                    if link is not None:
                        #if isinstance(link.presenter.node,CallBlock):
                        #    self.what_mouse_is_over=None
                        #    return
                        #print('link.draggable',link.draggable,'tags',tags)
                        if 'draggable' in tags:
                            if link.presenter.node.type_name=='LOOP':
                                self.what_mouse_is_over=None
                                return
                            link.draggable=True
                        else:
                            link.draggable=False
                        link.draggable='draggable' in tags

                        if link == last:
                            return link
                        if last is not None:
                            if last not in self.selection:
                                if last is not self.factory:
                                    last.highlight(False)
                        link.highlight(True)
                        self.what_mouse_is_over = link
                        self.mouse_substate = 'overlink'
                        return
            else:
                if last is not None:
                    if last not in self.selection:
                        if last is not self.factory:
                            last.highlight(False)
                self.what_mouse_is_over = None
                self.mouse_substate = 'overcanvas'
            return
        elif self.mouse == 'draggingleft':
            if self.mouse_substate == 'dragginglink':
                for id_no in things:
                    tags = self.canvas.gettags(id_no)
                    #print('tags',tags)

                    pres = self.get_presenter_from_tags(tags)
                    #print('presenter',pres)
                    if pres is self.dragged_join:
                        continue
                    if pres is not None and isinstance(pres,
                                                       ExecutableBlockPresenter):
                        if pres == last:
                            return pres
                        if last is not None:
                            last.highlight(False)
                        pres.highlight(True)
                        self.what_mouse_is_over = pres
                        return
                else:
                    self.what_mouse_is_over=None
                    if last is not None:
                        last.highlight(False)
            elif self.mouse_substate in ('draggingselection',
                                         'draggingpresenter'):
                if self.mouse_substate == 'draggingselection':
                    preses = self.selection
                else:
                    preses = set((self.what_mouse_is_over,))
                bin_prox=self.bin_proximity(event)
                if bin_prox=='over':
                    for pres in preses:
                        pres.delete_from_canvas()
                elif bin_prox=='far':
                    for pres in preses:
                        pres.refresh()
                else:
                    for pres in preses:
                        pres.squash(x,y,bin_prox)
                self.redraw_links()

    # def mouse_move_event(self,event):
    #    self.domouse_move_event(event)
    #    self.debug()
    #@debugger
    def mouse_move_event(self, event):
        if not self.current:
            return
        #print('mouse is', self.mouse)
        if self.mouse=='graphics':
            if self.current_graphic_item is not None:
                x=self.canvas.canvasx(event.x)
                y=self.canvas.canvasy(event.y)
                if self.mouse_substate in ('drawing','cuttingout'):
                    self.current_graphic_item.add_point(x,y)
                elif self.mouse_substate in (
                        'recting','grabbing','ellipsing',
                        'lining','arcing'):
                    self.current_graphic_item.move_point(x,y)
                    self.current_graphic_item.reload()
                    self.current_graphic_item.refresh()
            return
        if (self.mouse=='draggingleft'
            and self.mouse_substate=='movingdragpoint'):
            self.what_mouse_is_over.move_point(event.x,event.y)
            self.what_mouse_is_over.refresh()
            return

        self.determine_what_mouse_is_over(event)
        self.update_cursor()
        if self.mouse == 'up':
            return
        if self.mouse == 'downleft':
            if abs(event.x - self.hit_x) + abs(
                    event.y - self.hit_y) < DRAG_THRESH:
                return
            # Threshold exceeded
            if self.mouse_substate == 'oncanvas':
                self.mouse_state = ('draggingleft', 'rubberbanding')
                self.deactivate_text_editor()
                self.start_rubberbanding(self.hit_x, self.hit_y)
                self.stretch_rubberband(event.x, event.y)
                return
            if self.mouse_substate == 'onselection':
                if ui.has_dnd:
                    if self.dnd_drag_data is not None:
                        return
                else:
                    if self.local_dnd_json is not None:
                        self.mouse_state = 'draggingleft', 'dragginglocaldnd'
                        self.canvas['cursor']='hand1'
                        #self.vm.mark()
                        #self.vm.add_blocks_from_json()
                        return

                self.mouse_state = ('draggingleft', 'draggingselection')
                self.deactivate_text_editor()
                self.vm.mark()
                for pr in self.selection:
                    pr.start_dragging(self.hit_x, self.hit_y)
                    pr.highlight(True)
                    pr.drag(event.x, event.y)

                self.show_bin(event)
                self.redraw_links()
                return
            if self.mouse_substate == 'ontyping':
                x = self.canvas.canvasx(self.hit_x)
                y = self.canvas.canvasy(self.hit_y)
                self.active_text_editor.mouse_move(event)
                self.mouse_state = ('draggingleft', 'draggingtyping')
            if self.mouse_substate == 'onpresenter':
                pr = self.what_mouse_is_over
                self.vm.mark()
                pr.start_dragging(self.hit_x, self.hit_y)
                pr.highlight(True)
                pr.drag(event.x, event.y)
                self.redraw_links()
                self.mouse_state = 'draggingleft', 'draggingpresenter'
                self.show_bin(event)
                return
            if self.mouse_substate == 'onfactory' and self.new_inst_json is not None:
                newnos = self.vm.get_append_node_nos(self.diag, len(fromJSON(
                    self.new_inst_json)))
                #print('newnos', newnos)
                #print('JSON is', toJSON(self.new_inst_json))

                x, y = self.xy(event)
                self.vm.mark()
                #print('new_inst_json is >>',self.new_inst_json,'<<')
                self.vm.add_blocks_from_json(self.diag, self.new_inst_json,
                                             newnos, True,
                                             [x,
                                              y])  # also emits signal with new diag name and block numbers
                self.clear_selection()

                for node_no in newnos:
                    node = self.diag.nodes[node_no]
                    pres = get_block_item(self, node)
                    self.presenters[node_no] = pres
                    pres.refresh()
                    self.selection.add(pres)
                    pres.start_dragging(self.hit_x, self.hit_y)
                    pres.highlight(True)
                    pres.drag(event.x, event.y)
                self.factory.mouse_over(-20, -20)
                self.mouse_state = 'draggingleft', 'draggingselection'
                self.redraw_links()
        elif self.mouse == 'downright':
            #print('CHECKING DOWNRIGHT mouse move',event.x,event.y,self.hit_x,self.hit_y)
            if abs(event.x - self.hit_x) + abs(
                    event.y - self.hit_y) < DRAG_THRESH:
                return
            if self.mouse_substate == 'oncanvas':
                for presenter in self.presenters.values():
                    presenter.start_dragging(self.hit_x, self.hit_y)
                for presenter in self.presenters.values():
                    presenter.drag(event.x, event.y)
                self.redraw_links()
                self.deactivate_text_editor()
                self.mouse_state = 'draggingright', 'draggingcanvas'
            else:
                self.mouse_state = 'draggingright', 'draggingnothing'
            return
        elif self.mouse == 'draggingright':
            if self.mouse_substate == 'draggingcanvas':
                for presenter in self.presenters.values():
                    presenter.drag(event.x, event.y)
                self.redraw_links()
        elif self.mouse == 'draggingleft':
            if self.mouse_substate == 'sizing':
                self.sizing_widget.size_move_event(event.x, event.y)
                if isinstance(self.sizing_widget, ExecutableBlockPresenter):
                    #print('This should be called when resizing PythonPresenter')
                    self.redraw_links()
            elif self.mouse_substate == 'rubberbanding':
                #print('rubberband stretch')
                self.stretch_rubberband(event.x, event.y)
            elif self.mouse_substate == 'draggingselection':
                self.update_bin(event)
                for pr in self.selection:
                    pr.highlight(True)
                    pr.drag(event.x, event.y)
                self.redraw_links()
            elif self.mouse_substate == 'draggingtyping':
                self.active_text_editor.mouse_move(event)
            elif self.mouse_substate == 'draggingpresenter':
                self.update_bin(event)
                self.what_mouse_is_over.drag(event.x, event.y)
                self.redraw_links()
            elif self.mouse_substate == 'dragginglink':
                self.update_link_drag_pos(event.x, event.y)
            elif self.mouse_substate == 'draggingjson':
                #print('draggingjson')
                pass
            elif self.mouse_substate == 'draggingdnd':
                pass
                #print('draggingdnd')
            elif self.mouse_substate == 'dragginglocaldnd':
                pass
                #print('dragginglocaldnd')
            elif self.mouse_substate == 'sizingeditor':
                #print('sizingeditor', self.edge)
                if self.edge == 'right':
                    wmask = 1
                    hmask = 0
                elif self.edge == 'bottom':
                    wmask = 0
                    hmask = 1
                else:
                    wmask = 1
                    hmask = 1
                _, _, width, height = self.get_window_details()
                x = event.x_root
                y = event.y_root
                new_width = self.size_width + wmask * (x - self.hit_x_root)
                new_height = self.size_height + hmask * (y - self.hit_y_root)
                if new_height < 40:
                    new_height = 40
                if abs(new_width - width) > 3 or abs(new_height - height) > 3:
                    self.resize_canvas(new_width, new_height)

    def resize_canvas(self, new_width, new_height):
        #print(f'Resize canvas to {new_width}x{new_height}')
        self.canvas.config(width=new_width, height=new_height)


    def clear_bin(self):
        self.canvas.delete('bin')
        self.bin=None

    def bin_proximity(self,event):
        if self.bin is None:
            return 'far'
        x,y=self.canvas.canvasx(event.x),self.canvas.canvasy(event.y)

        x=(x-75)/75
        y=(y-self.bin.y+40)/40
        dist=(x*x+y*y)**0.5

        if dist<0.5:
            return 'over'
        elif dist>2:
            return 'far'
        else:
            return 5-2*dist

    def update_bin(self,event):
        if self.bin is not None:
            self.bin.update(self.bin_proximity(event))

    def show_bin(self,event):
        self.bin = Bin(0, self.canvas.winfo_height(),self.canvas)

    def ok_paste_text_as_bubbl(self,text):
        self.vm.mark()
        try:
            b = fromJSON(text)
            if not isinstance(b,
                dict) or any(b[k]["type"] not in block_factory for k in b):
                raise
            x=ui.mx()-self.sx()
            y=ui.my()-self.sy()
            self.vm.add_blocks_from_json(self.diag, text, None, True,
                                         [x, y])
            #print('added blocks')
            self.redraw()
        except Exception as e:
            self.vm.undo()
            #print(f'not pastable bubb source:{e}')
            return False

    def dnd_drop(self, event):
        #print('DND DROP',event)
        #print('VIS STATE',repr(self.visible_state))
        if self.visible_state!=DiagEditorState.editing:
            #print('WRONG STATE TO ACCEPT DROP')
            return
        #print('type', event.type)
        #print('types', ui.root.splitlist(event.type))
        #print('data',event.data)

        x = event.x_root - self.sx()
        y = event.y_root - self.sy()
        self.vm.mark()

        try:

            if event.type=='text/uri-list':
                self.vm.add_blocks_from_json(self.diag,
                    get_json_for_text_or_list(list(ui.root.splitlist(event.data))),
                    None,True,[x,y]
                )
            else:
                #print('DROP EVENT TYPE',event.type)
                self.vm.add_blocks_from_json(self.diag,
                    get_json_for_text_or_list(event.data),
                    None,True,[x,y]
                )
            #print('added blocks')
            self.redraw()
        except Exception as e:
            log('Cannot accept drop:',e,level=2 )
            #print('no add', e)
            self.vm.undo()
        self.mouse_state = 'up', 'off'
        return 'move'

    def dnd_drop_enter(self, event):
        #print('DND DROP ENTER')
        if not self.current:
            #print('SELECTING FOR EDITING')
            self.ide.select_editor_for_editing(self.name)
        return

    def dnd_drop_position(self, event):
        return
        x = event.x_root - self.useful_parent.winfo_x()
        y = event.y_root - self.useful_parent.winfo_y()
        dx = round(x - self.dnd_start_x)
        dy = round(y - self.dnd_start_y)
        self.canvas.move('dnd_dragged', dx, dy)
        self.dnd_start_x += dx
        self.dnd_start_y += dy
        #ui.root.update()
        #ui.root.update_idletasks()

    def dnd_drop_leave(self, *args):
        return
        #print('DND drag_exit', args)
        self.canvas.delete('dnd_dragged')
        self.mouse_state = 'up', 'off'

    def dnd_drag_start(self, event):
        #print('drag starting')
        #print('dnd_drag_data',self.dnd_drag_data)
        if self.dnd_drag_data is None:
            return None
        self.mouse_state = 'draggingleft', 'draggingdnd'
        return COPY, (DND_TEXT,), self.dnd_drag_data

    def update_link_drag_pos(self, x, y):
        widget = self.dragged_join
        x = self.canvas.canvasx(x)
        y = self.canvas.canvasy(y)
        dx = x / render_defaults.grid - widget.node.position[0]
        dy = y / render_defaults.grid - widget.node.position[1]
        self.vm.translate_nodes(self.diag, Iset(widget.node_no), dx, dy, True)
        try:
            widget.refresh()
        except Exception as e:
            pass
        self.redraw_links()

    def clear_selection(self):
        if self.selection:
            for w in self.selection:
                w.highlight(False)
            self.selection.clear()
        self.deactivate_text_editor()

    def snap_selection(self, selection):
        for w in selection:
            if w.snappable:
                p=w.node.position
                dx=round(p[0]*render_defaults.grid) % render_defaults.grid
                dy=round(p[1]*render_defaults.grid) % render_defaults.grid
                break
        else:
            return
        if dx == 0 and dy == 0:
            return

        if dx>=render_defaults.gs_div2:
            dx-=render_defaults.grid
        if dy>=render_defaults.gs_div2:
            dy-=render_defaults.grid
        self.vm.translate_nodes(self.diag,Iset(pres.node_no for pres in selection),-dx/render_defaults.grid,-dy/render_defaults.grid,True)
        for w in selection:
            self.canvas.move(w.uid,-dx,-dy) #w.refresh()#todo here is this correct?
        # w.highlight(True)
        # self.redraw()
        self.redraw_links()

    def deactivate_text_editor(self):
        if self.active_text_editor is not None:
            self.active_text_editor.text_cursor_off()
            self.active_text_editor.highlight(False)
            self.active_text_editor.refresh()
            if self.active_text_editor.is_empty():
                self.canvas.delete(self.active_text_editor.uid)
                self.vm.destroy_blocks(self.diag,
                                       Iset(self.active_text_editor.node_no))
                try:
                    self.presenters.pop(self.active_text_editor.node_no)
                except:
                    log('I didnt think this would happen here',
                        level=Logger.INFO)
            else:
                self.active_text_editor.update_params()
                log('active_text_editor successfully updated params')
            self.active_text_editor = None

    def remove_empty_text_blocks(self):
        to_del = Iset()
        for (node, block) in self.diag.nodes.items():
            if isinstance(block, TextBlock):
                if node in self.presenters and self.presenters[
                    node] == self.active_text_editor:
                    continue
                if (block.params[0].replace('<br />', '') + ' ').isspace():
                    to_del += node
        #self.vm.clean_nodes_from_page_undos(to_del)
        if not to_del.is_empty():
            self.vm.destroy_blocks(self.diag, to_del)
            for node in to_del & Iset(self.presenters):
                pres = self.presenters[node]
                self.canvas.delete(pres.uid)
                self.presenters.pop(node)

    #@debugger
    def mouse_left_release_event(self, event):
        #print('\nMR release',self.mouse,self.mouse_substate)

        self.clear_hover()
        if self.local_dnd_json is not None:
            #print('local dnd json',self.local_dnd_json)
            self.vm.add_blocks_from_json(self.diag,
                self.local_dnd_json,
                None,True,[self.canvas.canvasx(event.x),
                           self.canvas.canvasy(event.y)]
            )
            self.__class__.local_dnd_json=None
            self.mouse_state='up','off'
            #self.canvas['cursor']='arrow'
            self.redraw()
            return

        #print('mouse_left_up_event',event)
        if not self.current:
            return
            #try:
            #    self.ide.select_editor_for_editing(self.name)
            #except KeyError:  #todo fix this hack to cover changing apps bug
            #    pass
            #return
        if self.mouse=='graphics':
            if self.mouse_substate in (
                    'drawing','recting','ellipsing','lining','arcing'):
                self.current_graphic_item=None
            if self.mouse_substate in ('grabbing','cuttingout'):
                if self.current_graphic_item.params[0]=='line':
                    self.current_graphic_item.params[0]='polygon'
                self.canvas.delete(self.current_graphic_item.uid)
                self.canvas.update_idletasks()

                self.presenters.pop(self.current_graphic_item.node_no)
                item=self.current_graphic_item
                self.vm.destroy_blocks(self.diag,Iset(self.current_graphic_item.node_no))
                self.current_graphic_item=None
                #ui.root.after_idle(lambda event=event,item=item:self.do_image_grab(item,event=event))
                ui.root.after(100,lambda event=event,item=item:self.do_image_grab(item,event=event))
            return

        self.edge = None
        self.update_cursor()
        if self.mouse == 'draggingleft':
            if self.mouse_substate == 'dragginglink':
                if self.what_mouse_is_over is not None and not isinstance(
                        self.what_mouse_is_over,
                        (LinkStart, JoinBlockLinkStart)):
                    #print('Looping through',self.linking_presenters)
                    for pres,link_no in self.linking_presenters:
                        #print(f'linking {pres}   Link:{link_no}  to {self.what_mouse_is_over}')
                        self.vm.make_link(self.diag, pres.node_no, link_no,  #todo here make sure in edtiting mode
                                          self.what_mouse_is_over.node_no, True)


                    #print('Destroying self.dragged_join',self.dragged_join.node.type_name)
                    #was self.vm.destroy_blocks(self.diag,Iset(self.dragged_join.node_no))
                    #then was self.vm.move_blocks(self.diag, self.ide._deleted, Iset(self.ide._diag_clipboard.nodes), None, True)
                    self.vm.move_blocks(self.diag, self.ide._deleted, Iset(self.dragged_join.node_no), None, True)

                    self.canvas.delete(self.dragged_join.uid)
                    self.presenters.pop(self.dragged_join.node_no)
                    self.diag.compile_nodes()
                else:
                    #print('PRES is ',pres.node.type_name)
                    self.snap_selection((self.dragged_join,))
                self.redraw_links()
                self.dragged_join = None
            elif self.mouse_substate == 'sizing':
                self.canvas.config(cursor="arrow")
                self.redraw_links()
            elif self.mouse_substate == 'rubberbanding':
                self.canvas.delete(self.rubberband)
            elif self.mouse_substate == 'draggingpresenter':
                if self.bin_proximity(event)=='over':
                    self.vm.undo()
                    self.selection.clear()
                    self.selection.add(self.what_mouse_is_over)
                    self.delete()
                else:
                    if self.what_mouse_is_over.snappable:
                        self.snap_selection((self.what_mouse_is_over,))
                    self.what_mouse_is_over.highlight(False)
                    self.what_mouse_is_over.refresh()
                self.redraw_links()
            elif self.mouse_substate == 'draggingselection':
                if self.bin_proximity(event) == 'over':
                    self.vm.undo()
                    self.delete()
                else:
                    self.snap_selection(self.selection)
                    if self.new_inst_json is not None:
                        self.clear_selection()
                    # self.redraw_links()
            elif self.mouse_substate == 'draggingtyping':
                self.active_text_editor.mouse_up(event)
            elif self.mouse_substate == 'draggingjson':
                pass #print('MOUSE UP draggingjson')
            elif self.mouse_substate == 'draggingdnd':
                pass #print('MOUSE UP draggingjson')
            elif self.mouse_substate == 'sizingeditor':
                pass #print('done sizing editor')
            elif self.mouse_substate == 'movingdragpoint':
                pass #print('done sizing editor')
            else:
                log('UNRECOGNISED substate of draggingleft', self.mouse_substate)
        elif self.mouse == 'downleft':
            if self.mouse_substate == 'oncanvas':
                if self.visible_state!=DiagEditorState.editing:
                    self.mouse_state = 'up', 'off'
                    return
                #print('Start typing here')
                self.text_x, self.text_y = x, y = self.xy(event)
                # self.canvas.delete('temp')
                # self.canvas.create_rectangle(self.text_x-1,self.text_y-1,self.text_x+1,self.text_y+1,tag='temp',fill='#f00')

                new_no = max(list(self.diag.nodes)) + 1
                self.vm.add_blocks_from_json(self.diag,
                                             f'{{"1":{{"params":["","{render_defaults.font}","#000"],"type":"TEXT","size":[0,0],"pos":[0,0],"links":[]}}}}',
                                             Iset(new_no), False, [x, y])

                #print('Successfully added an empty typing block to block')

                self.presenters[
                    new_no] = self.active_text_editor = TextPresenter(self,
                                                                      self.diag.nodes[
                                                                          new_no])
                self.active_text_editor.text_cursor_on()
                self.active_text_editor.refresh()
            elif self.mouse_substate == 'onselection':
                if ctrl(event):
                    self.selection -= set([self.what_mouse_is_over])
                    self.what_mouse_is_over.highlight(False)
            elif self.mouse_substate == 'onpresenter':
                if ctrl(event):
                    self.selection.add(self.what_mouse_is_over)
                else:
                    if isinstance(self.what_mouse_is_over, TextPresenter):
                        if self.active_text_editor is not self.what_mouse_is_over:
                            self.text_x, self.text_y = x, y = self.xy(event)
                            self.active_text_editor = self.what_mouse_is_over
                            self.active_text_editor.position_cursor(
                                self.text_x - self.active_text_editor.xpos(),
                                self.text_y - self.active_text_editor.ypos(),
                                False)
                            self.active_text_editor.text_cursor_on()
                            self.active_text_editor.refresh()
        self.clear_bin()
        self.mouse_state = 'up', 'off'

    def do_image_grab(self,item,event=None):
        image = item.grab_from_screen()

        self.vm.undo()
        self.vm.mark()
        self.redraw()
        try:
            fn = self.bbsm.filevars._get_image_filename()
            image.pil_image.save(fn)
            image_view_json = '{' + image_view_text(fn, icon=False) + '}'
            new_no = max(list(self.diag.nodes)) + 1
            if event is not None:
                x = self.canvas.canvasx(event.x)
                y = self.canvas.canvasy(event.y)
            else:
                x = self.canvas.canvasx(ui.mx())
                y = self.canvas.canvasy(ui.my())
            self.vm.add_blocks_from_json(self.diag,
                                         image_view_json,
                                         Iset(new_no),
                                         False,
                                         [x, y])
            self.redraw()
            pres = self.presenters[new_no]
            self.selection = set([pres])
            self.mouse_state = 'draggingleft', 'draggingselection'
            pres.start_dragging(x, y)
        except Exception as e:
            self.vm.undo()
            log('Failed to save clipped/grabbed image', e,
                level=Logger.INFO)
        self.current_graphic_item = None

    def start_rubberbanding(self, x, y):
        self.rubberband_xo = self.canvas.canvasx(x)
        self.rubberband_yo = self.canvas.canvasy(y)
        self.rubberband = self.canvas.create_rectangle(self.rubberband_xo,
                                                       self.rubberband_yo,
                                                       self.rubberband_xo,
                                                       self.rubberband_yo)

    def stretch_rubberband(self, x, y):
        x = self.canvas.canvasx(x)
        y = self.canvas.canvasy(y)
        x1 = min(self.rubberband_xo, x)
        y1 = min(self.rubberband_yo, y)
        x2 = max(self.rubberband_xo, x)
        y2 = max(self.rubberband_yo, y)
        for widget in self.presenters.values():
            wx = widget.xpos()
            if wx < x2 and wx + widget.scaled_width() > x1:
                wy = widget.ypos()
                if wy < y2 and wy + widget.scaled_height() > y1:
                    if widget in self.selection:
                        continue
                    else:
                        widget.highlight(True)
                        self.selection.add(widget)
                        continue
            if widget in self.selection:
                widget.highlight(False)
                self.selection.remove(widget)
        self.canvas.coords(self.rubberband, x1, y1, x2, y2)

    def add_widget_to_canvas(self, widget, x, y,tag):
        self.canvas.create_window(x, y, window=widget, anchor='nw',tags=(tag,))

    def mouse_right_release_event(self, event):
        if not self.current and self.what_mouse_is_over is not None:
            if self.what_mouse_is_over==self.executable_block_under_mouse(event):
                print('EXECBLOCKUNDERMOUSE')
                options = []
                if self.diag.mach.state == ExState.stopped_on_node:
                    options.append('Run to here')
                elif self.diag.mach.state == ExState.active:
                    options.append('Stop program here')
                if self.ide.is_stacked(self.diag):
                    options.append('Backtrack to here')
                if options:
                    x = event.x_root  # - self.sx()
                    y = event.y_root  # - self.sx()
                    PopupMenu(self.canvas, x, y,
                      options,
                      self.right_click_menu_handler)
                    self.mouse_state = 'up', 'off'
                    return
            else:
                self.what_mouse_is_over=None

                        # if messagebox.askyesnocancel(message=f'Run to here?',
                        #                             icon='question',
                        #                             parent=self.useful_parent):
                        #    self.set_breakpoint(node_no=over.node_no)
                        #    self.ide.console.tell_machine.emit('run')
            if self.what_mouse_is_over is None:
                self.ide.select_editor_for_editing(self.name)
            return
        self.domouse_right_release_event(event)
        #self.debug()

    def domouse_right_release_event(self, event):
        if self.mouse=='graphics':
            if self.mouse_substate=='ongraphic':
                self.what_mouse_is_over.edit(self.hit_x_root,self.hit_y_root)
                return
            x = event.x_root  # - self.sx()
            y = event.y_root  # - self.sx()
            PopupMenu(self.canvas, x, y,
                      ['Exit Graphics',
                       'Pen settings',
                       'Draw',
                       'Line',
                       'Rectangle',
                       'Ellipse',
                       'Arc',
                       'Cut-out',
                       'Snapshot'],
                      self.graphics_menu_handler)
            return
        if self.mouse == 'draggingright':
            if self.mouse_substate == 'draggingcanvas':
                self.snap_selection(self.presenters.values())
        elif self.mouse == 'downright':
            if self.mouse_substate == 'oncanvas':
                if self.visible_state!=DiagEditorState.editing:
                    self.mouse_state = 'up', 'off'
                    return
                x = event.x_root  # - self.sx()
                y = event.y_root  # - self.sx()
                PopupMenu(self.canvas, x, y,
                               ['Undo', 'Paste', 'Graphics','Search/Replace'],
                               self.right_click_menu_handler)
                self.mouse_state = 'up', 'rightclickmenu'
            elif self.mouse_substate in ('oneditable','onnoneditable'):
                #print('mouse_right_release_state is ',self.visible_state)
                if self.visible_state in (
                        DiagEditorState.restricted_editing,
                        DiagEditorState.activated,
                        DiagEditorState.disabled):
                    if isinstance(self.what_mouse_is_over,ExecutableBlockPresenter):
                        self.right_clicked_presenter = self.what_mouse_is_over
                        #print('RIGHT_CLICKED_PRESENTER IS',self.right_clicked_presenter.node.type_name,self.right_clicked_presenter.node_no)

                        x = event.x_root  # - self.sx()
                        y = event.y_root  # - self.sx()
                        options=run_control_options(
                            self.diag.mach.state,
                            self.what_mouse_is_over.node.type_name
                        )
                        PopupMenu(self.canvas, x, y,
                               options,
                               self.right_click_menu_handler)
                else:
                    if self.what_mouse_is_over.node.type_name=='CALL':
                        options=['Edit','Edit block','Find usages']
                        x = event.x_root  # - self.sx()
                        y = event.y_root  # - self.sx()
                        PopupMenu(self.canvas, x, y,
                           options,
                           self.right_click_menu_handler)
                    elif self.what_mouse_is_over.node.type_name == 'INTERFACE':
                            options = ['Edit', 'Find usages']
                            x = event.x_root  # - self.sx()
                            y = event.y_root  # - self.sx()
                            PopupMenu(self.canvas, x, y,
                                      options,
                                      self.right_click_menu_handler)

                    elif self.what_mouse_is_over.node.type_name=='IMAGE_VIEW':
                        options=['Edit','Assign image to variable']
                        x = event.x_root  # - self.sx()
                        y = event.y_root  # - self.sx()
                        PopupMenu(self.canvas, x, y,
                           options,
                           self.right_click_menu_handler)
                    elif self.what_mouse_is_over.node.type_name=='GRAPHIC':
                        if self.what_mouse_is_over.params[0] in (
                                'line','ellipse','arc','rect'):
                            options=['Edit','Copy as polygon/line']
                            x = event.x_root  # - self.sx()
                            y = event.y_root  # - self.sx()
                            PopupMenu(self.canvas, x, y,
                                      options,
                                      self.right_click_menu_handler)
                    elif self.mouse_substate=='oneditable':
                        self.what_mouse_is_over.edit(event.x_root, event.y_root)
            elif self.mouse_substate == 'onselection':
                if self.visible_state!=DiagEditorState.editing:
                    return
                self.mouse_state = 'up', 'rightclickmenu'
                self.right_click_menu(event)
                return
        self.mouse_state = 'up', 'off'

    def mouse_right_down_event(self, event):
        if not self.current:
            over = self.executable_block_under_mouse(event)
            self.what_mouse_is_over=over
            if over is not None:
                return
            """
            if self.diag.mach.state==ExState.stopped_on_node:
                if over is not None:
                    self.what_mouse_is_over=over
                    options=['Run to here']
                    if self.ide.is_stacked(self.diag):
                        options.append('Backtrack to here')
                    x = event.x_root  # - self.sx()
                    y = event.y_root  # - self.sx()
                    PopupMenu(self.canvas, x, y,
                       options,
                       self.right_click_menu_handler)


                    #if messagebox.askyesnocancel(message=f'Run to here?',
                    #                             icon='question',
                    #                             parent=self.useful_parent):
                    #    self.set_breakpoint(node_no=over.node_no)
                    #    self.ide.console.tell_machine.emit('run')
                    self.mouse_state='up','off'
            return
            """
        self.domouse_right_down_event(event)
        #self.debug()

    def domouse_right_down_event(self, event):
        if self.mouse == 'up':
            if self.mouse_substate == 'overfactory':
                widg=self.factory.hl_widget
                if widg is not None:
                    if (widg.type_name=='VARIABLE'):
                        if (widg.text in self.diag.normal_variable_names() and
        messagebox.askyesno(
            f'Variable: {widg.text}:{type(self.diag.variables[widg.text])}',
            f'Delete {widg.text}?',
            parent=self.canvas)):
                            self.diag.variables.pop(widg.text)
                            self.factory.refresh()
                            self.redraw_live_data()
                    if (widg.type_name == 'DBVARIABLE'):
                        if (widg.text not in ('_config','_history') and
                                messagebox.askyesno(
                               f'Variable: {widg.text}:{type(self.diag.mach.database[widg.text])}',
                               f'Delete {widg.text}?',
                                parent=self.canvas)):
                            del self.diag.mach.database[widg.text]
                            self.factory.refresh()
                            self.redraw_live_data()

                    elif (widg.type_name=='TABLE'):
                        if not widg.text.startswith('_'):
                            try:
                                t=self.diag.variables["_DB"][widg.text]
                            except:
                                return
                            def ext(n,pref):
                                if n==1:
                                    return f'1 {pref}'
                                return f'{n} {pref}s'
                            desc='\n'.join([
                                f'Destroy {widg.text}',
                                f'with {ext(len(t.field_names),"field")}',
                                f'and {ext(len(t),"record")}'])
                            if messagebox.askyesno(
                                f'Table:{widg.text}',desc,parent=self.canvas):
                                self.diag.mach.destroy_table(widg.text,True)
                                self.factory.refresh()
                    else:
                        HoverTextPresenter(self,self.factory.hl_widget.create_func)
                return
        if self.what_mouse_is_over is self.factory:
            return
        self.hit_x = event.x
        self.hit_x_root = event.x_root
        self.hit_y = event.y
        self.hit_y_root = event.y_root

        if self.mouse=='graphics':
            if isinstance(self.what_mouse_is_over,GraphicPresenter):
                self.mouse_substate='ongraphic'
            else:
                self.mouse_substate='drawing'
            return

        if self.what_mouse_is_over in self.selection:
            self.mouse_state = 'downright', 'onselection'
        elif isinstance(self.what_mouse_is_over,
                        BaseBlockPresenter):
            if self.what_mouse_is_over.has_editor:
                self.mouse_state = 'downright', 'oneditable'
            else:
                self.mouse_state = 'downright', 'onnoneditable'
        elif self.what_mouse_is_over is None:
            self.mouse_state = 'downright', 'oncanvas'
        else:
            self.mouse_state = 'downright', 'onnothing'

    def right_click_menu(self, event):
        if self.visible_state!=DiagEditorState.editing:
            return

        def menu_options(presenter):
            result = []
            if presenter.has_editor:
                result.append('Edit')
            result += ['Copy', 'Cut', 'Delete']
            if presenter in self.selection:
                if all (isinstance(sel,
                            (GraphicPresenter,
                             ImageViewPresenter,
                             TextPresenter))
                  for sel in self.selection):
                    result.append('Make instructions to draw')
                result.append('Make into new block')
            if isinstance(presenter.node, (CallBlock,InterfaceBlock)):
                result.insert(1,'Edit block')
                result.append('Find usages')
            return result

        presenter = self.what_mouse_is_over
        if presenter:
            x = event.x_root  # -self.sx()
            y = event.y_root  # -self.sy() # - self.window.useful_parent.winfo_y()  # event.y_root #self.canvas.canvasy(event.y_root)
            PopupMenu(self.canvas, x, y, menu_options(presenter),
                               self.right_click_menu_handler)
            return

    def right_click_menu_handler(self, item):
        if item is None:
            self.update_cursor()
        elif item == 'Edit':
            self.mouse_state = 'up', 'editingpresenter'
            self.what_mouse_is_over.edit(self.hit_x_root, self.hit_y_root)
        elif item == 'Edit block':
            self.mouse_state = 'up','off'
            target=self.what_mouse_is_over.node.target_name
            x=self.hit_x
            y=self.hit_y
            self.ide.select_or_open_editor(target,x,y)
        elif item == 'Copy':
            self.copy()
        elif item == 'Cut':
            self.cut()
        elif item == 'Delete':
            self.delete()
        elif item == 'Make into new block':
            self.make_into_block()
        elif item =='Make instructions to draw':
            self.make_instructions_to_draw()
        elif item == 'Assign image to variable':
            item=self.what_mouse_is_over
            varname=os.path.basename(item.params[0]).split('.')[0]
            self.diag.variables[f'{varname}_image']=item.image
            self.redraw_live_data()
        elif item == 'Find usages':
            self.find_usages()
        elif item == 'Paste':
            self.paste()
        elif item == 'Undo':
            self.undo()
        elif item=='Run from here':
            self.select_mach_node()
            if self.diag.mach.state==ExState.stopped_on_node:
                self.ide.console.do_tell_machine('undoablerun')
        elif item=='Step from here':
            self.select_mach_node()
            self.ide.update_console()
            if self.diag.mach.state==ExState.stopped_on_node:
                self.ide.console.do_tell_machine('step')
        elif item=='Step into this':
            #print('step into',self.what_mouse_is_over)
            diag_name=self.right_clicked_presenter.node.target_name
            if diag_name not in self.ide.diag_editors:
                if diag_name in self.diag.mach.diags:
                    self.ide.get_new_diag_editor(
                        diag_name,
                        self.hit_x,self.hit_y,640,480,
                        initial_state=DiagEditorState.disabled)
                    self.ide.console.do_tell_machine('step')
                else:
                    messagebox.showinfo('Step into','Non existent BUBBL block',
                            parent=self.canvas)
            else:
                self.ide.console.do_tell_machine('step')
        elif item=='Step over this':
            #print('step over',self.what_mouse_is_over)
            diag_name=self.right_clicked_presenter.node.target_name
            self.ide.console.cache_editor_list([name for name in self.ide.diag_editors
                                 if name!=diag_name]) #suspend visiblity of editor
            self.ide.console.tell_machine.emit('step')
            self.ide.update_console()   #restore visibilty of editor

        elif item =='Step back':
            self.ide.console.tell_machine.emit('back')
        elif item == 'Run to here':
            self.set_breakpoint()
            if self.diag.mach.state==ExState.stopped_on_node:
                self.ide.console.do_tell_machine('undoablerun',clear_breakpoint=False)
        elif item == 'Backtrack to here':
            self.set_breakpoint()
            self.ide.console.do_tell_machine('back_to_breakpoint')
        elif item == 'Stop program here':
            self.set_breakpoint()

        elif item == 'Search/Replace':
            #print('FINDING')
            self.finder=Finder(self.hit_x_root,self.hit_y_root,self.ide,self.ide.find_settings)

        elif item =='Graphics':
            #print('Graphics')
            self.mouse_state='graphics','drawing'
            self.canvas['cursor']='pencil'

        elif item=='Copy as polygon/line':
            pres=self.what_mouse_is_over
            params=pres.get_polygon_params()
            px=pres.node.position[0]*render_defaults.grid+4
            py=pres.node.position[1]*render_defaults.grid+4
            self.vm.add_blocks_from_json(self.diag,
                f'''{{"1":{{"params":{toJSON(params)},
        "type":"GRAPHIC","size":[0,1],"pos":[0,0],"links":[]}}}}''',
            None,True,[px,py])
            self.redraw()

            #self.what_mouse_is_over.convert_to_polygon()

    def graphics_menu_handler(self, item):
        if item is None:
            self.update_cursor()
        elif item=='Exit Graphics':
            self.current_graphic_item=None
            self.mouse_state = 'up','off'
        elif item=='Pen colour':
            self.ide.choose_pen_colour(self.canvas)
        elif item=='Pen settings':
            self.ide.choose_pen_settings(self.canvas)
        elif item=='Draw':
            self.mouse_state='graphics','drawing'
        elif item=='Line':
            self.mouse_state='graphics','lining'
        elif item == 'Rectangle':
            self.mouse_state='graphics','recting'
        elif item  =='Ellipse':
            self.mouse_state='graphics','ellipsing'
        elif item  =='Arc':
            self.mouse_state='graphics','arcing'
        elif item  == 'Cut-out':
            self.mouse_state='graphics','cuttingout'
        elif item ==  'Snapshot':
            self.mouse_state='graphics','grabbing'

    def select_mach_node(self):
        self.ide.console.select_node(
            self.name,
            self.what_mouse_is_over.node_no)

    def set_breakpoint(self,node_no=None):
        if node_no is None:
            node_no=self.what_mouse_is_over.node_no
        self.ide.console.set_break_point(
            self.name,
            node_no)

    def esc_pressed(self):
        #print('escpressed',self.mouse_state)

        if self.mouse=='graphics':
            self.mouse_state='up','off'
            self.current_graphic_item=None
        self.update_cursor()
        self.deactivate_text_editor()

    def handle_key(self, event):
        #if self.current:
        if ctrl(event):
            c=event.keysym
            #print('CTRL',c)
            if c in ('u','z'):
                #print('UNDO')
                self.undo()
            elif c=='c':
                self.copy()
            elif c=='v':
                self.paste()
            elif c=='x':
                self.cut()
            elif c=='s':
                self.ide.save()
            elif c=='f':
                self.finder = Finder(self.hit_x_root, self.hit_y_root, self.ide,
                                     self.ide.find_settings)

        else:
            log(f'key {event.char} pressed')

    def tab_key(self,event):
        log('diag ed tab')

    def back_tab_key(self,event):
        log('diag ed backtab')

    def up_key(self,event):
        log('diag ed up key')

    def down_key(self,event):
        log('diag ed down key')

    def left_key(self,event):
        log('diag ed left key')

    def right_key(self,event):
        log('diag ed right key')

    def home_key(self,event):
        log('diag ed home')

    def end_key(self,event):
        log('diag ed end')

    def pg_up_key(self,event):
        log('diag ed pgup')

    def pg_dn_key(self,event):
        log('diag ed pgdn')

    def enter_key(self,event):
        log('diag ed enter')

    def f_key(self,event,number):
        log('diag ed f10')

    def enter_key(self,event):
        log('diag ed enter key')


    def cut(self):
        '''
        undoably move _clipboard contents to deleted
        then undoably move selected items to clipboard
        print('clipboard has ',ui.root..clipboard_get()clipboard_append()clipboard_clear())

        '''
        self.clipboard_copy()

        self.vm.mark()
        self.vm.move_blocks(self.ide._diag_clipboard, self.ide._deleted,
                            Iset(self.ide._diag_clipboard.nodes), None, True)
        self.vm.move_blocks(self.diag, self.ide._diag_clipboard,
                            Iset(pres.node_no for pres in self.selection) - 0,
                            None, True)
        for pres in self.selection:
            pres.delete_from_canvas()
            self.presenters.pop(pres.node_no)
        #self.canvas.update_idletasks()
        self.selection.clear()
        self.diag.compile_nodes()
        self.redraw_links()
    def paste(self,json=None):
        '''
        undoably copy _clipboard contents to diag
        '''
        #print('PASTING')
        #self.vm.copy_blocks_and_position(self.vm._diag_clipboard, self.diag,
        #                                 Iset(self.vm._diag_clipboard.nodes),
        #                                 pos, True)
        if json is None:
            clipboard=ui.get_clipboard_file_list()
            if clipboard is None:
                clipboard=ui.get_clipboard_string()
            if clipboard is None:
                log('Nothing to paste here')
                return
            json=get_json_for_text_or_list(clipboard)
        self.vm.mark()

        oldblocks = Iset(self.presenters)
        self.clear_selection()

        self.vm.add_blocks_from_json(self.diag,json,None,True,
                                     [ui.mx()-self.sx(),
                                      ui.my()-self.sy()])

        new_selection = Iset(self.diag.nodes) - oldblocks
        self.redraw()
        for node_no in new_selection:
            pres = self.presenters[node_no]
            pres.highlight(True)
            self.selection.add(self.presenters[node_no])

    def clipboard_copy(self):
        nodes=Iset(pres.node_no for pres in self.selection)-0
        ui.copy_to_clipboard(self.diag.get_json_for_nodes(nodes))

    def copy(self):
        #print(f'going to copy {self.selected_items}')
        self.clipboard_copy()
        return
        #self.vm.mark()
        #self.vm.move_blocks(self.vm._diag_clipboard, self.vm._deleted,
        #                    Iset(self.vm._diag_clipboard.nodes), None,
        #                    True)

        #nodes=Iset(pres.node_no for pres in self.selection)-0
        #self.vm.copy_blocks(self.diag, self.vm._diag_clipboard,nodes,True)


        #todo here copy jsonforblocks to system clipboard
        #print('Copy')

    def delete(self):
        self.vm.mark()
        self.vm.move_blocks(self.diag, self.ide._deleted,
                            Iset(pres.node_no for pres in self.selection) - 0,
                            None,
                            True)
        #print('SUCCESSFULLY DELETED BLOCKS',self.selection)
        self.diag.compile_nodes()
        self.selection.clear()

        #print('active_widget',self.active_widget)
        #print('active_node',self.active_node)
        self.what_mouse_is_over = None
        self.redraw(True)

    def make_into_block(self):
        '''
        creates new block and moves selected items to block's diagram
        creates a call-block to call the block
        :return:
        '''
        def do_make(command,_index):
            self.box.close_window()
            if command!='ok':
                return
            new_name=self.new_diag_name.get()
            if new_name in self.bbsm.diags:
                messagebox.showerror('Making new block',
                                         new_name+' already exists',
                                         parent=self.canvas)
                return
            if (not new_name.replace('_','').isalnum()
                or new_name[0] in '0123456789'):
                messagebox.showerror('Making new block',
                                     'Diag name must only contain'
                                     ' letters, digits and'
                                     ' underscores and must not start with'
                                     'a digit.',
                                      parent=self.canvas)
                return
            self.vm.mark()
            self.vm.make_new_diag(new_name)
            nodes=Iset(pres.node_no for pres in self.selection)-0
            self.vm.move_blocks(self.diag,
                                self.bbsm.diags[new_name],
                                nodes,
                                None,
                                True)
            for pres in self.selection:
                self.canvas.delete(pres.uid)
                self.presenters.pop(pres.node_no)
            self.selection.clear()
            self.factory.refresh()
            init=f'''
{{"1":{{"links":[0],"params": ["{new_name}"],
      "pos": [0,0],
      "size": [7, 1],
      "type": "CALL"}}
}}'''
            self.vm.add_blocks_from_json(self.diag,init,None,True,
                [round(self.canvas.canvasx(self.hit_x)),
                 round(self.canvas.canvasy(self.hit_y))])
            self.redraw()
            self.redraw_links()

        self.new_diag_name = tk.StringVar()
        self.box = InputBox(
            self.useful_parent, ui.mx(),ui.my(),
                {'title': 'New block name','style':'',
                 'rows': [
                     [{'type':'label','text':'New name'},
                      {'type': 'input','weight':1,'var': self.new_diag_name,
                        'contexts':[]}
                     ]
                 ]
              },
             do_make,
            tkinter_file_dialog=self.ide.config['tkinterfiledialog'],
            history=self.ide.history)

    def make_instructions_to_draw(self):
        gx=0
        gy=2
        json='''{"1":{"links":[2],
    "params":[["_xorg,_yorg","0,0"]],
    "pos":[0,0],
    "size":[5,1],
    "type":"ASSIGN"}
'''
        xorg=min(sel.xpos() for sel in self.selection)
        yorg=min(sel.ypos() for sel in self.selection)

        sels=list(self.selection)

        for node_no,sel in enumerate(sels,2):
            link=node_no+1 if node_no<=len(sels) else 0
            try:  #node_no,link,gx,gy,x_org,y_org
                text,gy=sel.get_json_for_disp_thing(node_no,link,gx,gy,xorg,yorg)
                json+=',\n'+text
            except Exception as e:
                log('JJSSONNNOTREADYYY',e,level=Logger.INFO)
        json+='}'

        #print ('JSON for  ITD',json)
        self.paste(json=json)

    def undo(self):
        #print('undo')
        if self.active_text_editor is not None:
            self.active_text_editor.text_cursor_off()
        self.selection = set()
        self.vm.undo()
        self.diag.compile_nodes()
        self.redraw()

    def get_resources(self,defn=None):
        db=self.diag.variables['_db']
        tables=[t  for t in vars(db) if isinstance(db[t],Table)]
        sysresources=['_db','_pg','_ev','_fs','_os',
                      '_Iset','_eval','_rec','_rn',
                      '_nw','_mach']
        variables=[v for v in self.diag.variables
                    if not v.startswith('_')]
        globs=[f'_db.{v}' for v in vars(db) if not v in tables and v!='_list']

        tfns={tn:list(db[tn].field_names) for tn in tables}
        for p in self.presenters.values():
            if p.node.type_name!='CREATE':
                continue
            if p.params[0] in tfns:
                continue
            tfns[p.params[0]]=[p.split(':')[0] for p in p.params[1:] if p]

        result= {'table':tables,
                 'fieldnames':tfns,
                 'variable':variables,
                 'system':sysresources,
                 'global':globs}
        #print('GET_RESOURCES is',result)
        return result

    def find_usages(self):
        presenter=self.what_mouse_is_over()
        this=not isinstance(presenter.node, CallBlock)
        if not this:
            target=presenter.params[0]
        else:
            target=self.diag.name
        finds={}
        dns=list(self.bbsm.diags)
        print('target',target)

        for dn in dns:
            diag=self.bbsm.diags[dn]
            if not this or dn!=target:
                res=[node for node in diag.nodes
                     if diag.nodes[node].type_name=='CALL'
                        and diag.nodes[node].params[0]==target]
                if res:
                    finds[dn]=res
        print('finds',finds)
        if not finds:
            tk.messagebox.showinfo('No usages found',message='No usages found',parent=self.canvas)
            return
        dns=list(finds)
        choices=[f'{find} ({len(finds[find])})' for find in dns]
        print('choices',choices,self.hit_x,self.hit_y)
        def callback(choice):
            print('CHOSEN',choice)
            if choice is not None:
                dn=dns[choices.index(choice)]
                self.ide.found(dn,finds,{})


        PopupMenu(self.canvas, ui.mx(),ui.my(),
                  choices,
                  callback)




