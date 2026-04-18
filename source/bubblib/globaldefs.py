"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from enum import IntEnum
from dataclasses import dataclass

svnames = ['_ev', '_PR', '_fs', '_pg', '_os', '_nw', '_db']
executable_types = ["ASSIGN", "IF", "WRITE", "IMAGE", "POLYGON", "RECT",
                    "ELLIPSE", "ARC","LINK", "PAGE", "PAGE_CLOSE",
                    "PAGE_CLEAR", "PAGE_UPDATE", "WAIT", "CALL", "FOR", "LOOP",
                    "INPUT", "CREATE", "INSERT",
                    "DELETE", "DESTROY", "UPDATE", "SELECT", "CHOICE",
                    "ASK_USER", "MENU", "ALERT", "FILE_MENU",
                    "COLOUR_MENU", "PYTHON", "LINE", "FILE_MKDIR", "FILE_SAVE",
                    "FILE_APPEND", "FILE_DELETE",
                    "FILE_RENAME", "FILE_COPY", "FILE_EXECUTE", "SWITCH",
                    "JOIN",
                    "EDITOR", "DIALOG", "SORT", "BUTTON", "SCROLLBAR",
                    'INPUTDISP', 'CHOICEDISP', 'CHECKBOX', 'RADIO',
                    'TEXTED',
                    "SECTOR", "PLAY", "OUTPUT_AT", "PAGE_REFRESH",
                    ]

event_types = ['Button', 'Scroll', 'Input', 'Check', 'Radio', 'Choice', 'Text',
               'MouseDn', 'MouseUp', 'MouseMv', 'MouseWh', 'MouseDbl',
               'OffPage',
               'Key', 'KeyUp',
               'WinClose', 'WinDrag', 'WinDrop', 'WinSize','Menu',
               'Enter', 'Esc', 'Up', 'Dn', 'Left', 'Right',
               'Tab', 'BackTab', 'PgUp', 'PgDn', 'Ins', 'Del', 'Home', 'End',
               'Back',
               'Play', 'Rewind', 'Reverse', 'FFwd', 'VolUp', 'VolDn', 'ClipEnd',
               'Timer', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9',
               'F10', 'F11', 'F12',
               'Rq', 'Rx', 'StdOut', 'StdErr', 'ProcExit','Async', 'Any', 'Msg',
               ]
non_editable_types = ["LINK", "PAGE_CLOSE", "PAGE_CLEAR", "LOOP", "JOIN"]
centre_text_types = ["MENU", "LINK", "SWITCH"]
nav_events = ['Up', 'Down', 'Left', 'Right', 'Home', 'End', 'Tab', 'BackTab']
dispmarkups = {
    'line': ["x", "y", "colour", "active_colour","line_width", "joins","ends","points", "tags"],
    'rect': ["x", "y", "colour", "fill", "active_colour", "active_fill",
             "scale", #"rotate", "cx", "cy",
             "width", "height",
             "line_width","tags"],
    'ellipse': ["x", "y", "colour", "fill", "active_colour", "active_fill",
                "scale", #"rotate", "cx", "cy",
                 "width", "height",
                "line_width", "tags"],
    'arc':["x", "y", "colour", "fill", "active_colour", "active_fill",
                "width", "height", "start","angle","style",
                "line_width", "tags"],
    'polygon': ["x","y","colour", "fill", "active_colour", "active_fill", "joins",
                "line_width", "points","tags"],
    'write': ["x", "y", "nl", "colour", "fill", "active_colour", "active_fill",
              "scale", "rotate", "anchor", "font", "tags"],

    'button': ["x", "y", "width", "colour", "fill", "active_colour",
               "active_fill", "font","enabled","tags","disabled_colour"],
    'checkbox': ["x", "y", "width", "colour", "fill", "active_colour",
                 "active_fill", "value", "font", "enabled","tags",
                 "disabled_colour"],
    'radio': ["x", "y", "prompt", "value", "colour", "fill", "active_colour",
              "active_fill","width", "enabled","tags"],
    'scrollbar': ["x", "y", "colour", "active_colour","fill",
                  "width","height", "orientation","value", "step",
                  "enabled", "tags"],
    'inputdisp': ["x", "y", "colour", "fill", "font", "history", "prompt",
                  "width","button","enabled", "tags"],
    'texted': ["x", "y", "colour", "fill", "font", "width", "height",
               "enabled","tags"],

    'choicedisp': ["prompt", "x", "y", "multiple","colour", "fill", "font",
                   "width","tags","length","enabled"],

    'image': ["x", "y", "width", "height", "scale", "rotate", "clip", "anchor",
              "tags"],

    'image_view': ["icon", "width", "height", "scale", "rotate", "tags"],
    'page': ["x", "y", "width", "height", "font", "paper", "ink", "title",
             "fixed_size","scrollable","closeable", "focus","menu",
             "cursor",
             "fullscreen","markups","left_margin","top_margin","on_top"],
    'colourmenu': ["title", "default", "x", "y", "history"],
    'filechooser': ["title","saveas", "folder", "multiple", "hidden",
                    "history", "view", "filetypes"],
    'alert': ["title", "colour", "fill", "active_colour", "active_fill", "x",
              "y", "font"],
    'menu': ["title", "colour", "fill", "active_colour", "active_fill", "x",
             "y", "default", "font"],
    'ask': ["title", "colour", "fill", "active_colour", "active_fill", "x", "y",
            "font"],
    'input': ["prompts", "defaults", "title", "colour", "fill", "x", "y",
              "font", "history", "prompt_colour", "prompt_fill"],

    'choice': ["multiple", "default", "title", "colours", "x", "y",
               "colour", "fill", "font", "length"],
    'dialog': ["x", "y", "modal"],
    'tableview': ["icon", "colour", "fill"],
    'graphic':['line_width','colour','fill','active_colour','active_fill',
        'arrow','arrow_shape','start','angle','style','ends','joins'],
    'editor':["x","y","title","width","length","view_mode"],
    'print':["printer","landscape","monochrome","filename",
             "command","paper_size","postscript"]
}

markup_type_map = {"x": "expr",
                   "y": "expr",
                   "colour": "colour",
                   "disabled_colour":"colour",
                   "prompt_colour": "colour",
                   "prompt_fill": "colour",
                   "fill": "colour",
                   "active_colour": "colour",
                   "active_fill": "colour",
                   "line_width": "expr",
                   "line_style": "expr",
                   "scale": "expr",
                   "rotate": "expr",
                   "tags": "expr",
                   "nl": "check",
                   "focus": "check",
                   "width": "expr",
                   "height": "expr",
                   "icon": "check",
                   "border": "choice:'none','frame','blank','raise','lower'",
                   # todo here use tkinter names 'groove' etc ?
                   "xs": "expr",
                   "ys": "expr",
                   "paper": "colour",
                   "ink": "colour",
                   "title": "expr",
                   "closeable": "check",
                   "fixed_size": "check",
                   "scrollable": "check",
                   "font": "font",
                   "history": "expr",
                   "top": "expr",
                   "bottom": "expr",
                   "step": "expr",
                   "file": "file",
                   "multiple": "check",
                   "folder": "check",
                   "hidden": "check",
                   "save": "check",
                   "saveas": "check",
                   "view": "choice:'list','icons'",
                   "filter": "expr",
                   "default": "expr",
                   "defaults": "expr",
                   "prompt": "expr",
                   "prompts": "expr",
                   "image": "image",
                   "joins": "choice:'round','mitre','bevel'",
                   "ends": "choice:'round','butt','projecting'",
                   "style": "choice:'pieslice','chord','arc'",
                   'start':"expr",
                   "angle":"expr",
                   "clip": "expr",
                   "items": "expr",
                   "value": "expr",
                   "length": "expr",
                   "modal": "expr",
                   "extension": "expr",
                   "filetypes": "expr",
                   "field": "expr",
                   "multi": "expr",
                   "colours": "expr",
                   "highlights": "expr",
                   "graphic":"choice:'line','rect','ellipse','arc','polygon'",
                   "points":"expr",
                   "button":"choice:colour,file,folder",
                   "menu":"expr",
                   "anchor":"choice:nw,n,ne,e,se,s,sw,w,center",
                   "view_mode":"choice:list-view,record-view",
                   "enabled":"check",
                   "orientation":"choice:horizontal,vertical",
                   "markups":"expr",
                   "on_top":"check",
                   "fullscreen":"check",
                   "filename":"expr",
                   "monochrome":"check",
                   "landscape":"check",
                   "printer":'expr',
                   "paper_size": "choice:'A3','A4','A5','A6','B3','B4','B5','Letter','Legal'",
                   "postscript":'check',
                   "command":"expr",
                   }

valid_sys_var_names=set()

def is_sys_var(vname):
    return vname in valid_sys_var_names

@dataclass
class Defaults:
    size:str
    grid: int
    gs_div2:int
    gs_by2:float
    gs_by3:float
    image_icon_size: int
    font: str
    dpi:int

render_defaults = Defaults('normal',18,9,9,6, 80, 'TkDefaultFont,10',72)

#grid_size = 18
#image_icon_size = 80
#default_font = 'TkDefaultFont,10'

def scale_view(size):
    if size == 'tiny':
        render_defaults.size=size
        render_defaults.grid = 8
        render_defaults.gs_div2=4
        render_defaults.gs_by2=4
        render_defaults.gs_by3=8/3
        render_defaults.image_icon_size = 35
        render_defaults.font = 'TkDefaultFont,5'
    elif size == 'small':
        render_defaults.size=size
        render_defaults.grid = 12
        render_defaults.gs_div2=6
        render_defaults.gs_by2=6
        render_defaults.gs_by3=4
        render_defaults.image_icon_size = 60
        render_defaults.font = 'TkDefaultFont,8'
    elif size == 'large':
        render_defaults.size=size
        render_defaults.grid = 24
        render_defaults.gs_div2=12
        render_defaults.gs_by2=12
        render_defaults.gs_by3=8
        render_defaults.image_icon_size = 120
        render_defaults.font = 'TkDefaultFont,16'
    elif size == 'huge':
        render_defaults.size=size
        render_defaults.grid = 36
        render_defaults.gs_div2=18
        render_defaults.gs_by2=18
        render_defaults.gs_by3=12
        render_defaults.image_icon_size = 160
        render_defaults.font = 'TkDefaultFont,20'
    else:
        render_defaults.size='normal'
        render_defaults.grid = 18
        render_defaults.gs_div2=9
        render_defaults.gs_by2=9
        render_defaults.gs_by3=6
        render_defaults.image_icon_size = 60
        render_defaults.font = 'TkDefaultFont,10'

def contains_snaps(init):
    try:
        return any(init[n]['type'] in executable_types for n in init)
    except:
        return False

class ExState(IntEnum):
    quiescent = 1
    stopped_on_node = 2
    stopped_on_link = 3
    active = 4
    dying = 5
    exited = 6

class Activity(IntEnum):
    none = 0
    stepping = 1
    stepping_back = 2
    stepping_back_to = 3
    running = 4
    undoably_running = 5
    running_to = 6
    undoably_running_to = 7

class DiagEditorState(IntEnum):
    disabled = 0  # no editing, factory of flashing
    editing = 1  # full editing allowed, no flashing, factory showing
    restricted_editing = 2  # only non-exectuable block and position editing
    # no factory or link editing
    activated = 3  # flashing on node or link, factory not showing
    activated_but_stacked = 4  # not flashing, factory not showing

class BubblWaitException(Exception):
    def __init__(self,type_name):
        Exception.__init__(self)
        self.type_name=type_name

class PythonBlockException(Exception):
    def __init__(self,exception,code_text):
        Exception.__init__(self)
        self.exception=exception
        self.code_text=code_text

class PythonBlockSyntaxException(Exception):
    def __init__(self,message,line_no,col_no):
        Exception.__init__(self)
        self.message=message
        self.line_no=line_no
        self.col_no=col_no

def run_control_options(
        mach_state,
        diag_node_type):
    if diag_node_type == 'CALL':
        step_options = ['Step into this', 'Step over this']
    else:
        step_options = []
    if mach_state == ExState.stopped_on_node:
        return ['Run from here',
                'Step from here'
                ] + step_options + [
                   'Step back',
                   'Run to here',
                   'Backtrack to here']
    if mach_state == ExState.stopped_on_link:
        return ['Step back']
    if mach_state == ExState.active:
        return ['Stop program here']
    print('NO RUN CONTROL OPTIONS FOR ',f'mach_state:{repr(mach_state)},{diag_node_type}')

# scale_view('small')
