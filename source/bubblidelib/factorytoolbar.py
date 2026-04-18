"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from bubblib.globaldefs import render_defaults
from bubblib.gutils import BubblFont,icon
#from bubblib.iconmap import icons, icon
from bubblib.blockfactory import *
from bubblib.bubbldiag import NodeHolder
from bubblib.bubbljson import toJSON
from bubblib.presentation import variable_presentation, get_presentation
from bubblib.utils import log
from .presenterinfo import get_presenter_info
from .renderer import render


class FactoryWidget:
    def __init__(self, editor, container, image, text, x_pos, y_pos, size,
                 type_name, create_func, index=None,
                 always_visible=False, min_width=None,fill='#dcd'):
        #print('FactoryWidget',text,size,type_name,index)
        self.editor = editor
        self.canvas = editor.canvas
        self.container = container
        self.diag = editor.diag
        self.image = icon(image, icon_size=size) if image is not None else None
        # print('widget image from',image,'is',self.image)
        self._x_pos = x_pos
        self.y_pos = y_pos
        self.size = size
        self.min_width = size if min_width is None else min_width
        self.text = text
        self.fill = fill
        self.font = BubblFont()
        self.create_func = create_func
        self.uid = f'fi{type_name}{index}'
        self.tags = 'factory', self.uid
        self.highlighted = False
        self.index = index
        self.type_name = type_name
        self.always_visible = always_visible
        self._visible = always_visible
        self.mx = 0
        self.my = 0

    @property
    def visible(self):
        return self._visible or self.always_visible

    @visible.setter
    def visible(self, value):
        self._visible = value
        self.draw()

    @property
    def width(self):
        base = 0 if self.image is None else self.size
        tw = 0 if self.text is None else self.font.width(self.text)
        return max(base + tw, self.min_width)

    @property
    def x_pos(self):
        if self.container is None:
            return self._x_pos
        return self.container.x_pos

    @property
    def height(self):
        if self.image is None:
            return (self.size*2) // 3
        return self.size

    def contains_mouse(self, x, y):
        return x in range(self.x_pos, self.x_pos + self.width) and y in range(self.y_pos, self.y_pos + self.height)

    def create(self, x, y):
        dummy_diag = NodeHolder('_', {}, mach=self.editor.bbsm)
        if self.index != None:
            node = self.create_func(dummy_diag, 1, self.index)
        else:
            node = self.create_func(dummy_diag, 1)
        node.init["pos"][0] = (x - self.x_pos) / render_defaults.grid
        node.init["pos"][1] = (y - self.y_pos) / render_defaults.grid

        if (isinstance(node, CallBlock)
            and self.editor.bbsm.diags[node.params[0]].has_loop) or \
                isinstance(node, (ForBlock,DialogBlock)):
            loop_node = LoopBlock(dummy_diag, 2, target=1)
            loop_node.init["pos"][0] = node.init["pos"][0] + (loop_node.init["size"][0] + node.init["size"][0]) // 2 + 1
            loop_node.init["pos"][1] = node.init["pos"][1]
            # print(f'FORNODE.INIT=:{toJSON(node.init)}')
            # print(f'LOOPNODE.INIT=:{toJSON(loop_node.init)}')

            text = f'{{"1":{toJSON(node.init)},"2":{toJSON(loop_node.init)} }}'
            # print(f'INIT TEXT IN NODE CREATION IS :{text}')
        else:
            text = f'{{"1":{toJSON(node.init)}}}'
        return text

    def hide(self):
        if self.visible:
            self.visible = False

    def highlight(self, highlight, mx, my):
        self.mx = mx
        self.my = my
        if highlight:
            # print('Widget highlighting',self.text)
            if self.highlighted:
                return
            # print('GOING Ahead',self.text)
            self.highlighted = True
            self.draw()
        else:
            if not self.highlighted:
                return
            # print('Widget unhighlighting',self.text)
            self.highlighted = False
            self.draw()
        self.canvas.lift('factorycreation')

    def draw_background(self):
        x2 = x1 = self.x_pos
        y1 = self.y_pos
        if self.image is not None:
            x2 += self.size
            if self.text is not None:
                x2 += self.font.width(self.text)
            y2 = y1 + self.size
        else:
            x2 += self.width
            y2 = y1 + (self.size*2) // 3
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.fill, outline='', tags=self.tags)

    def draw(self):
        can = self.editor.canvas
        can.delete(self.uid)
        if not self.visible:
            return
        #print('widget drawing with',self.create_func.__name__,self.text)
        self.draw_background()
        # print('drawn background now',self.image)
        if self.image is not None:
            # print('creating image',self.x_pos,self.y_pos,self.image)
            can.create_image(self.x_pos, self.y_pos, image=self.image, tags=self.tags, anchor='nw')
            if self.text is not None:
                can.create_text(self.x_pos + self.size, self.y_pos, text=self.text, tags=self.tags, anchor='nw',
                                font=self.font.font)
        else:
            can.create_text(self.x_pos, self.y_pos, text=self.text, tags=self.tags, anchor='nw', font=self.font.font)
        if self.highlighted:
            pres = get_presentation(self.type_name, self.index)
            #print('FACTORY type_name',self.type_name)
            init = pres["default_init"]

            #print('factory toolbar init=',init)
            width = init["size"][0] * render_defaults.grid
            height = init["size"][1] * render_defaults.grid
            shape = pres["shape"]
            # print('THIS IS TYPE',self.type_name)
            if self.type_name=='CALL':
                fill=self.editor.bbsm.diags[self.text].sig["params"][0]
            else:
                fill = pres["block"]["colour"]
            outline = '#000'

            #if init['type']==''##

            #]

            if init['type']=='LINK':
                try:
                    ind=self.diag.sig['linknames'].index(self.text)
                except:
                    ind=0
                info=get_presenter_info(init['type'], [ind], self.diag)
            else:
                info = get_presenter_info(init['type'], init['params'], self.diag)

            if self.type_name == 'VARIABLE':
                info.params=[f'Variable: {self.text}']
                text_colour = '#ff0'
            elif self.type_name == 'DBVARIABLE':
                    info.params = [f'_db Variable: {self.text}']
                    text_colour = '#ff0'
            elif self.type_name=='TABLE':
                #print('table_view',self.text)
                info.params[0]=f'Table: {self.text}'
                text_colour = '#000'
            else:
                text_colour = '#000'
            lines = [info.display_line(i) for i in range(info.ndisplay_lines())]
            #print('factory toolbar lines',lines)
            try:
                render(self.canvas, self.x_pos + 5, self.y_pos +5, width, height,
                       self.tags + ('factorycreation',), self.type_name, shape, fill, outline, lines,
                       font=self.font,
                       text_colour=text_colour)
            except TypeError:
                log('TypeError', init)
                raise
        self.canvas.lift('factorycreation')


class FactoryContainerWidget:
    def __init__(self, factory,image,tag=''):
        self.factory=factory
        self.editor = factory.editor
        self.canvas = self.editor.canvas
        self.y_pos = factory.y_pos
        self.size = factory.icon_size
        self.image = None if image is None else icon(image, self.size)
        self.widgets = []
        self.uid = f'fc{image}{tag}'
        self.tags = 'factory', self.uid
        self.highlighted = False
        # print('New container widget image_key',image)


    @property
    def x_pos(self):
        return (self.factory.x_pos+
                self.factory.icon_size*self.factory.column_list.index(self))

    def xy(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        return x, y

    def draw_background(self):
        x1 = self.x_pos
        y1 = self.y_pos
        y2 = y1 + self.size
        x2 = x1 + self.size
        self.canvas.create_rectangle(x1, y1, x2, y2, fill='#dcd', outline='', tags=self.tags)

    def mouse_over_top(self, x, y):
        return x in range(self.x_pos, self.x_pos + self.size) and y in range(self.y_pos, self.y_pos + self.size)

    def widget_with_mouse(self, x, y):
        result = None
        for row, widget in enumerate(self.widgets, 1):
            if widget.contains_mouse(x, y):
                widget.highlight(True, x, y)
                result = row
            else:
                widget.highlight(False, x, y)
        return result

    def draw(self):
        # print('Container drawing',self.image,self.x_pos,self.y_pos,self.size)
        self.canvas.delete(self.uid)
        # self.canvas.create_image(self.x_pos,self.y_pos,image=self.editor.image)
        self.draw_background()
        self.canvas.create_image(self.x_pos, self.y_pos, image=self.image, tags=self.tags, anchor='nw')
        if self.highlighted:
            for widget in self.widgets:
                # print('COLUMNWIDGET',widget,widget.x_pos,widget.y_pos,widget.visible,widget.image,widget.text)
                widget.visible = True
                widget.draw()
        self.canvas.lift('factorycreation')

    def highlight(self, highlight):
        if highlight:
            # print('column highlighting')
            if not self.highlighted:
                self.highlighted = True
                for widget in self.widgets:
                    widget.visible = True
                    widget.draw()
        else:
            # print('Column unhighlighting')
            if self.highlighted:
                self.highlighted = False
                for widget in self.widgets:
                    widget.visible = False
                    widget.draw()
        self.canvas.lift('factorycreation')

    def add_widget(self, image, text, type_name, create_func, index=None, min_width=None,fill='#dcd'):
        # print('container widget image in is',image)
        if image is None:
            y_size = (self.size *2)//3
        else:
            y_size = self.size

        widget = FactoryWidget(self.editor, self, image, text, self.x_pos,
                               self.y_pos + self.size + y_size * len(self.widgets), self.size, type_name, create_func,
                               index=index, min_width=min_width,fill=fill)
        # print('Container widget',widget.x_pos,widget.y_pos,widget.image)
        self.widgets.append(widget)

    def clear_widgets(self):
        for widget in self.widgets:
            widget.hide()
        self.widgets = []

class DragFactory:
    def __init__(self, editor, icon_size, x_pos, y_pos):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.column_map = {}
        self.column_list = []
        self.editor = editor
        self.icon_size = icon_size
        self.hl_col = None
        self.hl_widget = None
        self.mx = 0
        self.my = 0

    def hide(self):
        self.editor.canvas.delete('factory')

    def draw(self, full=False):
        # self.editor.canvas.delete('factory')
        for col in self.column_list:
            if isinstance(col, FactoryWidget):
                # print('factory draw',col,self.hl_widget)
                col.highlight(col == self.hl_widget, self.mx, self.my)
            else:
                col.highlight(self.hl_col is not None and col == self.column_list[self.hl_col])

            if full:
                col.draw()

    def add_widget_to_factory(self, image, text, type_name, create_func):
        s = self.icon_size
        widget = FactoryWidget(self.editor, None, image, text,
                               self.x_pos + len(self.column_list) * self.icon_size,
                               self.y_pos, s, type_name, create_func, always_visible=True)
        self.column_list.append(widget)

    def add_widget_to_container(self, image, text, type_name, create_func, index=None, min_width=None,fill='#dcd'):
        container = self.column_map[self.last_key]
        container.add_widget(image, text, type_name, create_func, index=index, min_width=min_width,fill=fill)

    def add_container_to_factory(self, image, container_key,insert_index=''):
        container = FactoryContainerWidget(self, image,tag=insert_index)
        self.column_map[container_key] = container
        if insert_index !='':
            self.column_list.insert(insert_index,container)
        else:
            self.column_list.append(container)
        self.last_key = container_key


    def rc(self, x, y):
        for col, item in enumerate(self.column_list):
            if isinstance(item, FactoryWidget):
                if item.contains_mouse(x, y):
                    return 0, col
            else:
                if item.mouse_over_top(x, y):
                    return 0, col
                if item.highlighted:
                    row = item.widget_with_mouse(x, y)
                    if row is not None:
                        return row, col
        return None, None

    def mouse_over(self, x, y):
        self.mx = x
        self.my = y
        r, c = self.rc(x, y)
        if r == None:
            self.hl_col = None
            self.hl_widget = None
            self.draw()
            return
        if r == 0:
            col = self.column_list[c]
            if isinstance(col, FactoryWidget):
                self.hl_widget = col
                self.hl_col = None
            else:
                self.hl_col = c
                self.hl_widget = None
        else:
            self.hl_widget = self.column_list[c].widgets[r - 1]
        self.draw()

    def refresh(self):
        try:
            self.do_refresh()
        except Exception as e:
            print('FACTORY REFRESH EXCEPTION',e)

    def do_refresh(self):
        #print('FACTORY TOOLBAR REFRESHING')
        editor=self.editor
        container = self.column_map['Links']
        container.clear_widgets()
        self.last_key = 'Links'
        if len(editor.diag.sig["linknames"]) > 0:
            for i, linkName in enumerate(editor.diag.sig["linknames"]):
                #print('adding link widget to link_container')
                self.add_widget_to_container(
                    'link', linkName, 'LINK',
                    lambda node_holder, node, index=i:
                        get_link_block(node_holder,node, index), index=i)
        else:
            self.add_widget_to_container('link', None, 'LINK',
                lambda node_holder, node, index=0:
                    get_link_block(node_holder,node, 0), index=0)
        #calls
        conts=[col for col in self.column_map if col.startswith('Library')]
        for cont in conts:
            self.column_map[cont].clear_widgets()

        self.last_key = 'Library0'

        def get_call_block(node_holder, node_no, init, target_name=None):
            try:
                target = editor.bbsm.diags[target_name]
            except:
                return CallBlock(editor, node_holder, node_no)

            nlinks = len(target.sig["linknames"])
            npars = len(target.params) - 1
            init = {"params": [target_name] + [""] * npars, "type": "CALL", "size": [5, max(npars + 1, (nlinks + 1) // 2)],
                    "pos": [0, 0], "links": [0] * max(nlinks, 1)}
            return CallBlock(node_holder, node_no, init)

        diag_names=[name for name in editor.bbsm.diags if name!='main']
        for i,diag_name in enumerate(sorted(diag_names)):
            ins_index=self.column_list.index(self.column_map[self.last_key])
            key=f'Library{i//10}'
            if key not in self.column_map:
                self.add_container_to_factory('library', key,
                                              insert_index=ins_index+1)
            else:
                self.last_key=key
            self.add_widget_to_container(
                None, diag_name, 'CALL',
                lambda diag, node, init, target_name=diag_name:
                    get_call_block(diag, node, init,target_name=target_name),
                index=diag_name,fill=editor.bbsm.diags[diag_name].params[0])
        #vars
        container = self.column_map['Variables']
        container.clear_widgets()
        self.last_key = 'Variables'

        def get_variable_block(node_holder, node_no, var_name):
            init = variable_presentation["default_init"]
            init["params"]=[var_name]
            return VariableBlock(node_holder, node_no, init)

        container.clear_widgets()
        # print('redoing vars')
        for vn in editor.diag.normal_variable_names(include_params=True):
            self.add_widget_to_container(None, vn, 'VARIABLE', get_variable_block, index=vn, min_width=60)
        #tables
        container = self.column_map['Tables']
        container.clear_widgets()
        self.last_key = 'Tables'

        def get_tableview_block(node_holder, node_no, table_name):
            init={"params": [table_name,0,[100]],
                   "type": "TABLE",
                   "size": [11, 3],
                   "pos": [0, 0],
                   "links": []}
            return TableViewBlock(node_holder, node_no, init)

        def get_db_variable_block(node_holder, node_no, var_name):
            init = db_variable_presentation["default_init"]
            init["params"] = [var_name]
            return DBVariableBlock(node_holder, node_no, init)

        # print('redoing vars')
        for vn,is_table in editor.bbsm.get_db_list():
            if is_table:
                self.add_widget_to_container(None,
                                             vn,
                                            'TABLE',
                                             get_tableview_block,
                                             index=vn,
                                             min_width=60)
            else:
                self.add_widget_to_container(None,
                                             vn,
                                             'DBVARIABLE',
                                             get_db_variable_block,
                                             index=vn,
                                             min_width=60)
        self.draw(full=True)

def get_drag_factory(editor, icon_size=30):
    result = DragFactory(editor, icon_size, 0, 0)

    result.add_widget_to_factory("assign", None, 'ASSIGN', AssignBlock)
    result.add_widget_to_factory("if", None, 'IF', IfBlock)
    result.add_widget_to_factory("switch", None, 'SWITCH', SwitchBlock)
    result.add_widget_to_factory("for", None, 'FOR', ForBlock)
    result.add_widget_to_factory("wait", None, 'WAIT', WaitBlock)
    result.add_widget_to_factory("python", None, 'PYTHON', PythonBlock)

    result.add_container_to_factory("page", 'Page')
    result.add_widget_to_container("page", 'Select Page', 'PAGE', PageBlock)
    result.add_widget_to_container("del", 'Destroy Page', 'PAGE_CLOSE', PageCloseBlock)
    result.add_widget_to_container("clr_page", 'Clear Page', 'PAGE_CLEAR', PageClearBlock)
    result.add_widget_to_container("page_upd", 'Update Page', 'PAGE_UPDATE', PageUpdateBlock)
    result.add_widget_to_container("print","Print",'PRINT', PrintBlock)

    result.add_container_to_factory("output", 'Output')
    result.add_widget_to_container("output", "Write", 'WRITE', WriteBlock)
    result.add_widget_to_container("image", "Image", 'IMAGE', ImageBlock)
    result.add_widget_to_container("rectangle", "Rectangle", 'RECT', RectangleBlock)
    result.add_widget_to_container("ellipse", "Ellipse", 'ELLIPSE', EllipseBlock)
    result.add_widget_to_container("arc","Arc",'ARC',ArcBlock),
    result.add_widget_to_container("polygon", "Polygon", 'POLYGON', PolygonBlock)
    result.add_widget_to_container("line", "Line(polyline)", 'LINE', LineBlock)

    result.add_container_to_factory("user","User")
    result.add_widget_to_container("button", "Button", 'BUTTON', ButtonBlock)
    result.add_widget_to_container("scrollbar", "Scrollbar", 'SCROLLBAR', ScrollbarBlock)
    result.add_widget_to_container("keyboard", "TextInput", 'INPUTDISP', InputDispBlock)
    result.add_widget_to_container("ok", "Checkbox", 'CHECKBOX', CheckboxBlock)
    result.add_widget_to_container("radio", "Radio group", 'RADIO', RadioBlock)
    result.add_widget_to_container("choice", "Choice", 'CHOICEDISP', ChoiceDispBlock)
    result.add_widget_to_container("keyboard", "Text", 'TEXTED', TextEdBlock)
    result.add_widget_to_container("sound", "Play media", 'PLAY', PlayMediaBlock)

    result.add_container_to_factory("dialog", "Popup")
    result.add_widget_to_container("keyboard", "Input", 'INPUT', InputBlock)
    result.add_widget_to_container("alert", "Alert", 'ALERT', AlertBlock)
    result.add_widget_to_container("menu", "Menu", 'MENU', MenuBlock)
    result.add_widget_to_container("choice", "Choice", 'CHOICE', ChoiceBlock)
    result.add_widget_to_container("askuser", "Question", 'ASK_USER', AskUserBlock)
    result.add_widget_to_container("filechooser", "File-chooser", 'FILE_MENU', FileMenuBlock)
    result.add_widget_to_container("colour", "Colour-chooser", 'COLOUR_MENU', ColourMenuBlock)
    result.add_widget_to_container("dialog", "Dialog", 'DIALOG', DialogBlock)
    result.add_widget_to_container("edit", "Editor", 'EDITOR', EditorBlock)


    result.add_container_to_factory("table", "Table")
    result.add_widget_to_container("tableselect", "Search table ('select')", 'SELECT', SelectBlock)
    result.add_widget_to_container("create", "Create table", 'CREATE', CreateBlock)
    result.add_widget_to_container("insert", "Insert into table", 'INSERT', InsertBlock)
    result.add_widget_to_container("tabledelete", "Delete from table", 'DELETE', DeleteBlock)
    result.add_widget_to_container("tableupdate", "Update rows in table", 'UPDATE', UpdateBlock)
    result.add_widget_to_container("delete", "Destroy table", 'DESTROY', DestroyBlock)
    result.add_widget_to_container("sort", "Sort table", 'SORT', SortBlock)


    result.add_container_to_factory("file", "File")
    result.add_widget_to_container("filemkdir", 'Make folder', 'FILE_MKDIR', FileMkDirBlock)
    result.add_widget_to_container("save", 'Save File', 'FILE_SAVE', FileSaveBlock)
    result.add_widget_to_container("fileappend", 'Append to file', 'FILE_APPEND', FileAppendBlock)
    result.add_widget_to_container("filecopy", 'Copy file(s)', 'FILE_COPY', FileCopyBlock)
    result.add_widget_to_container("filedelete", 'Delete file', 'FILE_DELETE', FileDeleteBlock)
    result.add_widget_to_container("filerename", 'Rename file', 'FILE_RENAME', FileRenameBlock)
    result.add_widget_to_container("fileexec", 'Execute OS command', 'FILE_EXECUTE', FileExecBlock)
    result.add_widget_to_container("bubbl", 'Run Async block','ASYNC',AsyncBlock)


    result.add_container_to_factory("link", 'Links')
    result.add_container_to_factory('library', "Library0")

    result.add_container_to_factory("toolkit", "Toolkit")
    result.add_widget_to_container("formula", "Live data", 'FORMULA', FormulaBlock)
    result.add_widget_to_container("fileexec", "Bubbl program", 'BUBBL', BubblBlock)
    result.add_widget_to_container("www", "Web Link", 'WEBLINK', WeblinkBlock)
    result.add_widget_to_container("fileexec", "O/S Command", 'COMMAND', CommandBlock)

    result.add_container_to_factory("tableview", "Tables")
    result.add_container_to_factory('view', 'Variables')


    '''
    'TABLE': lambda diag, no, init: TableViewBlock(diag, no, init),
    'TEXT': lambda diag, no, init: TextBlock(diag, no, init),
    'IMAGE_VIEW':lambda diag,no,init:ImageViewBlock(diag,no,init),
    '''
    result.refresh()
    return result


