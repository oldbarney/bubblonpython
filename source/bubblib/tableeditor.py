"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from collections import deque
import sys

from bubblib.bubbljson import fromJSON
from bubblib.gutils import BubblFont
from bubblib.iset import Iset
from bubblib.popupchoice import PopupChoice
from bubblib.sizeableheader import SizeableHeader, ColumnSpec
from bubblib.uiserver import ui
from bubblib.utils import log, print_

if __name__ == '__main__':
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tkinter as tk
from .mywidgets import PopupMenu
from .table import Table


def clipboard_contents():
    text = ui.get_clipboard_string()
    try:
        return fromJSON(text)
    except:
        return text


class ClipTable(Table):
    def __init__(self, source, rows, columns=None):
        if columns is None:
            columns = Iset(range(len(source.field_names)))
        Table.__init__(self, 'clip',
                       [f'{source.field_names[i]}:{source.field_types[i]}'
                        for i in columns])
        for r in rows:
            self.insert_row(-1, [getattr(source[r], fn)
                                 for fn in self.field_names])
        log('CLIP TABLE')
        log(f'[{self.field_names}]')
        log(f'[{self.field_types}]')
        for i, r in enumerate(self):
            log(i, r.get_list())
        log('END OF CLIP TABLE')


class TableEdVm:
    # edit_control = Signal(str,bool,bool)  #"up"|"down"|"enter"|"esc"|"tab",shift,ctrl
    undo_map = {}
    clipboard = []

    def __init__(self, table):
        self.table = table
        self.name = table.table_name
        try:
            self.undos = self.undo_map[table]
        except:
            self.undos = self.undo_map[table] = deque(maxlen=10000)

    def cut(self, row_nos, col_nos):  # todo here blank non whole-row fields
        def undo(row_no):
            # undo cut
            clip = self.clipboard.pop()
            for row in reversed(clip):
                self.table.insert_row(row_no, row, False)

        clip = ClipTable(self.table, row_nos)
        self.clipboard.append(clip)
        for rn in reversed(row_nos):
            self.table.remove_row(rn, False)
        self.undos.append(lambda r=row_nos[0]: undo(r))

    def copy(self, row_nos, col_nos=None):
        clip = ClipTable(self.table, row_nos, col_nos)
        self.clipboard.append(clip)
        self.undos.append(self.clipboard.pop)

    def paste(self, row_no, col_no=0, insert=True):

        clip = self.clipboard[-1]
        if insert:
            for row in reversed(clip):
                self.table.insert_row(row_no, row, False)
            delrows = Iset(range(row_no, row_no + len(clip)))

            def undo(delrows=delrows):
                # undo paste insert
                for rn in reversed(delrows):
                    self.table.remove_row(rn, False)

            self.undos.append(undo)
        else:
            row_nos = Iset(range(row_no, row_no + len(clip)))
            col_nos = Iset(range(col_no, col_no + len(clip.field_names)),
                           indexed=self.table.field_names)
            # src_field_names=[self.table.field_names[i] for i in col_nos]
            start_row = row_nos[0]
            original = ClipTable(self.table, row_nos, col_nos)
            for i, clip_row in enumerate(clip, start_row):
                for cn, clip_cn in zip(col_nos.indexed, clip.field_names):
                    setattr(self.table[i], cn, getattr(clip_row, clip_cn))

            def undo(original=original,start_row=start_row,col_nos=col_nos):
                # undo paste over
                for i, orig_row in enumerate(original,start_row,col_nos):
                    for cn, orig_cn in zip(col_nos.indexed,
                                           original.field_names):
                        setattr(self.table[i], cn, getattr(orig_row, orig_cn))

            self.undos.append(undo)

    def delete(self, row_nos, col_nos):  # todo here blank entries
        original = ClipTable(self.table, row_nos)
        insrow = row_nos[0]
        for rn in reversed(row_nos):
            self.table.remove_row(rn, False)

        def undo(insrow=insrow,original=original):
            # undo delete
            for row in reversed(original):
                self.table.insert_row(insrow, row)

        self.undos.append(undo)

    def insert_blank_row(self, index):
        def undo(index=index):
            self.table.remove_row(index, False)

        self.table.insert_row(index, self.table.blank_row)
        self.undos.append(undo)

    def update_field(self, row_no, field_name, value):
        original = getattr(self.table[row_no], field_name)
        setattr(self.table[row_no], field_name, value)

        def undo(original=original,row_no=row_no,field_name=field_name):
            setattr(self.table[row_no], field_name, original)

        self.undos.append(undo)

    def undo(self):
        try:
            undo = self.undos.pop()
        except IndexError:
            log('No more undos to undo',level=2)
            return
        undo()

class PopupEntry(tk.Entry):
    def __init__(self, parent, default_text, client_handler, history=None,
                 **kwargs):
        tk.Entry.__init__(self, parent, **kwargs)
        self.parent = parent
        self.client_handler = client_handler
        self.history = history
        self.insert(0, default_text)
        self['exportselection'] = False
        self.focus_force()
        # self.select_all()
        self.bind('<Return>', lambda _event:self.enter())
        self.bind('<FocusOut>', lambda event:self.enter(event=None))
        self.bind('<Escape>', self.escape)
        self.bind('<Control-a>', lambda *args: self.select_all)
        self.bind('<Tab>', self.tab)
        if sys.version_info[1]>=12:
            self.bind('<ISO_Left_Tab>', self.left_tab)
        self.bind('<3>', self.right_click)
        self.exited=False

    def tab(self, _event):
        self.enter(event='right')
        pass

    def left_tab(self, _event):
        self.enter(event='left')

        # self.parent.event_generate('<ISO_Left_Tab>')

    def enter(self, event='down'):
        # print('POPUP Enter called with',event)
        if self.exited:
            return
        text = self.get()
        if self.history is not None:
            if text in self.history:
                self.history.remove(text)
            self.history.insert(0, text)
        self.exited=True
        self.client_handler(text, event)

    def escape(self, event):
        self.exited=True
        self.client_handler(None)
        self.destroy()

    def right_click(self, event):
        if self.history is not None:
            if len(self.history) >= 1:
                def callback(index):
                    if index is not None:
                        instext = self.history[index]
                        self.insert(self.index('insert'), instext)

                PopupChoice(self.parent,
                            ui.mx(),
                            ui.my(),
                            self.history,
                            client_handler=callback)


class Column:
    def __init__(self, parent_canvas, column_spec, font):
        self.parent_canvas = parent_canvas
        self.column_spec = column_spec
        self.font = font

    def redraw(self, x1, x2, line_height, table, offset, nrows, hl_range):
        # print('Redrawing column',hl_range)
        col = self.column_spec.header
        if self.column_spec.range_right:
            x = x2 - 2
            anchor = 'ne'
        else:
            x = x1 + 2
            anchor = 'nw'
        width = x2 - x1 - 2
        disp_func = self.column_spec.display_func
        canvas = self.parent_canvas
        canvas.delete(col)
        for i, row_no in enumerate(
                Iset(range(offset, offset + nrows))):
            y1 = i * line_height
            y2 = y1 + line_height

            if row_no in hl_range:
                canvas.create_rectangle(
                    x1, y1, x2, y2, fill='#BBB', tags=[col])

            # print(f'table[{row_no}]={table[row_no]}')
            # canvas.create_line(x1,y2,x2,y2,x2,y1,fill='#000',tags=[col])
            if row_no < len(table):
                canvas.create_text(x, y1 + 2,
                                   text=self.font.cropped(
                                       disp_func(getattr(table[row_no], col)),
                                       width),
                                   anchor=anchor, tags=[col])
            else:
                canvas.create_rectangle(
                    x1, y1, x2, y2, fill='#E8E8E8', tags=[col])
                canvas.create_text(x1 + 2, y1 + 2, text='-', anchor='nw',
                                   fill='#999', tags=[col])

        # print('did column')


class Columns:
    def __init__(self, editor, canvas, header_frame, mouse_func, font):
        self.editor = editor
        self.header_frame = header_frame
        self.mouse_func = mouse_func
        self.font = font

        self.canvas = canvas

        # print('multicolumn canvas made')
        self.line_height = font.line_space + 4
        self.columns = [Column(canvas, spec, font=self.font)
                        for spec in header_frame.column_specs]

        # print('Got columns')
        self.drawing = False
        self.doresize = None
        self.doitagain = False
        self.data = None
        self.canvas.bind('<1>', self.mouse_left)
        self.canvas.bind('<2>', self.mouse_right)
        self.canvas.bind('<3>', self.mouse_right)
        self.canvas.bind('<B1-ButtonRelease>', self.mouse_left_up)
        self.canvas.bind('<B2-ButtonRelease>', self.mouse_right_up)
        self.canvas.bind('<B3-ButtonRelease>', self.mouse_right_up)
        self.canvas.bind('<Motion>', self.mouse_move)

    def rc_from_mouse(self, event):
        x = round(self.canvas.canvasx(event.x))
        y = round(self.canvas.canvasy(event.y))
        r = self.editor.offset + y // self.line_height
        for i in range(len(self.header_frame.column_specs)):
            if self.header_frame.x_coords[i] > x:
                c = i - 1
                break
        else:
            c = len(self.header_frame.column_specs) - 1
        return r, c

    def mouse_left(self, event):
        log('mouse_left on columns')
        r, c = self.rc_from_mouse(event)
        self.mouse_func('left', r, c)

    def mouse_left_up(self, event):
        r, c = self.rc_from_mouse(event)
        self.mouse_func('leftup', r, c)

    def mouse_move(self, event):
        r, c = self.rc_from_mouse(event)
        self.mouse_func('move', r, c)

    def mouse_right(self, event):
        log('mouse_right on columns')
        r, c = self.rc_from_mouse(event)
        self.mouse_func('right', r, c)

    def mouse_right_up(self, event):
        r, c = self.rc_from_mouse(event)
        self.mouse_func('rightup', r, c)

    def resize(self, newxs, newws):
        if self.drawing:
            self.doresize = newxs, newws
            return
        # self.canvas['width']=newxs[-1]
        # for i,(x,w) in enumerate(zip(newxs,newws)):
        #    #print(i,'x',x,'w',w)
        #    self.columns[i].column_spec.width=w
        #    self.columns[i].column_spec.x=x
        self.doresize = None
        self.redraw_all(self.editor.offset,
                        self.editor.hl_rows,
                        self.editor.hl_cols)

    def nrows(self):
        return round(self.editor.data_canvas.winfo_height() /
                     self.line_height + 0.5)


    def redraw_all(self, offset, hl_rows, hl_cols):
        # self.canvas['height']=self.font.line_space*(len(self.data)+1)
        # row nos

        nrows = self.nrows()
        can = self.editor.line_no_canvas
        can.delete('all')
        x = int(can['width']) - 2
        h = self.line_height
        for i, rn in enumerate(range(offset, offset + nrows)):
            if len(hl_cols) == len(self.columns) and rn in hl_rows:
                can.create_rectangle(0, i * h, x + 2, (i + 1) * h, fill='#BBB')
            can.create_text(x, i * h + 2, text=f'{rn}', anchor='ne')

        for i, (x1, x2, column) in enumerate(zip(self.header_frame.x_coords,
                                                 self.header_frame.right_x_coords,
                                                 self.columns)):
            if i not in hl_cols:
                hrows = range(0)
            else:
                hrows = hl_rows

            column.redraw(x1, x2, self.line_height, self.editor.table, offset,
                          nrows, hrows)

        self.editor.data_canvas.delete('grid')
        length = nrows * self.line_height
        for x in self.header_frame.right_x_coords:
            self.editor.data_canvas.create_line(x, 0,
                                                x, length,
                                                fill='#777',
                                                tags=['grid'])
        length = self.header_frame.right_x_coords[-1]
        for y in range(nrows):
            self.editor.data_canvas.create_line(0, y * self.line_height,
                                                length, y * self.line_height,
                                                fill='#777',
                                                tags=['grid'])


class TableEditor:
    history = []

    def __init__(self, parent, table,
                 finished_func,
                 x=None,
                 y=None,
                 offset=0, length=20,
                 col_widths=None,
                 font=None,
                 read_only=False,
                 allow_record_view=False):
        self.window = tk.Toplevel(parent)
        self.window.title('Table: ' + table.table_name)
        self.window.protocol("WM_DELETE_WINDOW", self.ask_close)
        self.window.grid_rowconfigure(0, weight=1)
        if x is None:
            x=ui.mx()
        if y is None:
            y=ui.my()

        self.window.geometry(f'+{x}+{y}')
        self.table = table
        self.finished_func = finished_func
        self.vm = TableEdVm(table)
        self.restore_point = len(self.vm.undos)
        self._offset = 0
        self.offset=offset
        self.read_only = read_only
        if font is None:
            font = BubblFont()
        self.font = font

        self.main_frame = tk.Frame(self.window)
        self.main_frame.grid(row=0, column=0, sticky='nsew')

        if col_widths == None:
            col_widths = [
                font.width(field_name)
                for field_name in table.field_names]
            for i in range(offset,min(offset+length,len(table))):
                for f,v in enumerate(table[i].get_list()):
                    col_widths[f]=min(300,max(col_widths[f],font.width(v)))
            log('COLWIDTHS new =',col_widths)
        else:
            log('COLWIDTHS spec=',col_widths)

        self.headers = [
            ColumnSpec.get_header(i, field, field_type, width)
            for i, (field, field_type, width) in enumerate(zip(
                table.field_names,
                table.field_types, col_widths))
        ]

        self.hl_rows = Iset()
        self.hl_cols = Iset()
        self.rc_org = None
        self.popup = None
        self.on_append = False

        self.header_frame = SizeableHeader(self.main_frame,
                                           self.header_callback,
                                           self.headers)
        self.header_frame.grid(row=0, column=1, sticky='nw')
        self.line_no_canvas = tk.Canvas(self.main_frame, width=60)
        self.line_no_canvas.grid(row=1, column=0, sticky='nsw')
        self.line_no_canvas.bind('<1>',
                                 lambda event: self.mouse_on_line_no('left',
                                                                     event))
        self.line_no_canvas.bind('<3>',
                                 lambda event: self.mouse_on_line_no('right',
                                                                     event))
        self.line_no_canvas.bind('<B1-ButtonRelease>',
                                 lambda event: self.mouse_on_line_no('leftup',
                                                                     event))
        self.line_no_canvas.bind('<B3-ButtonRelease>',
                                 lambda event: self.mouse_on_line_no('rightup',
                                                                     event))
        self.line_no_canvas.bind('<Motion>',
                                 lambda event: self.mouse_on_line_no('move',
                                                                     event))
        self.data_canvas = tk.Canvas(self.main_frame,
                                     height=length * self.line_height(),
                                     width=self.header_frame.width,
                                     borderwidth=1,
                                     relief='solid')
        self.data_canvas.bind('<MouseWheel>', self.mouse_wheel)  # Windows
        self.data_canvas.bind('<4>', self.up_one)  # linux
        self.data_canvas.bind('<5>', self.down_one)

        self.window.bind('<Up>', lambda event: self.up(False))
        self.window.bind('<Down>', lambda event: self.down(False))
        self.window.bind('<Left>', lambda event: self.left(False))
        self.window.bind('<Right>', lambda event: self.right(False))
        self.window.bind('<Next>', lambda event: self.pg_dn(False))
        self.window.bind('<Prior>', lambda event: self.pg_up(False))
        self.window.bind('<Home>', lambda event: self.home(False))
        self.window.bind('<End>', lambda event: self.end(False))

        self.window.bind('<Shift-Up>', lambda event: self.up(True))
        self.window.bind('<Shift-Down>', lambda event: self.down(True))
        self.window.bind('<Shift-Left>', lambda event: self.left(True))
        self.window.bind('<Shift-Right>', lambda event: self.right(True))
        self.window.bind('<Shift-Next>', lambda event: self.pg_dn(True))
        self.window.bind('<Shift-Prior>', lambda event: self.pg_up(True))
        self.window.bind('<Shift-Home>', lambda event: self.home(True))
        self.window.bind('<Shift-End>', lambda event: self.end(True))

        self.window.bind('<Tab>', lambda event: self.tab())
        if sys.version_info[1]>=12:
            self.window.bind('<ISO_Left_Tab>', lambda event: self.left_tab())

        self.window.bind('<Return>', lambda event: self.enter())
        self.window.bind('<Escape>', lambda _event: self.close(False))
        self.window.bind('<Control-z>', lambda _event: self.undo())

        # self.window.bind_all('<MouseWheel>',self.mouse_wheel)

        self.data_canvas.grid(row=1, column=1, sticky='nsew')
        self.slider_frame = tk.Frame(self.main_frame)
        self.slider_frame.grid(row=1, column=2, sticky='ns')
        #self.slider_frame.bind('<Configure>', self.resize_slider)
        self.slider_pos = tk.IntVar(value=offset)
        self.slider = tk.Scale(self.slider_frame,
                               variable=self.slider_pos,
                               from_=0,
                               to=len(table) - 1,
                               resolution=1,
                               showvalue=False,
                               length=length * self.line_height())
        self.slider.bind('<MouseWheel>', self.mouse_wheel)  # Windows
        self.slider.bind('<4>',self.up_one)
        self.slider.bind('<5>',self.down_one)
        self.slider.grid(row=0, column=0, sticky='ns')
        self.main_frame.rowconfigure(0, weight=0)
        self.main_frame.columnconfigure(0, weight=0)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.columnconfigure(2, weight=0)
        self.main_frame.rowconfigure(1, weight=1)
        self.main_frame.rowconfigure(2, weight=0)
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.grid(row=2, column=0, columnspan=3, sticky='ew')

        tk.Button(self.button_frame,
                  text='Cancel',
                  command=self.close
                  ).grid(row=0, column=0, sticky='w')
        tk.Button(self.button_frame,
                  text='Undo',
                  command=self.undo
                  ).grid(row=0, column=1, sticky='w')
        tk.Button(self.button_frame,
                  text='Insert row(s)',
                  command=self.insert_rows
                  ).grid(row=0, column=2, sticky='w')

        if allow_record_view:
            tk.Button(self.button_frame,
                      text='record-view',
                      command=self.switch_to_record_view
                     ).grid(row=0, column=2,sticky='w')

        tk.Label(self.button_frame, text='').grid(row=0, column=4, sticky='ew')
        tk.Button(self.button_frame,
                  text='Ok',
                  command=lambda: self.close(True)
                  ).grid(row=0, column=5, sticky='e')

        self.button_frame.columnconfigure(4, weight=1)

        self.data_display = Columns(self,
                                    self.data_canvas,
                                    self.header_frame,
                                    self.mouse,
                                    font)

        self.state = 'up'  # onrow oncell
        self.slider_pos.trace_add('write', self.slider_moved)

        self.window.bind(
            '<Configure>',
            lambda *args: self.draw_all(),
            add=True
        )
        self.key_rc = offset, 0

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self,value):
        if value>len(self.table)-1:
            value=len(self.table)-1
        if value<0:
            value=0
        self._offset=value

    def insert_rows(self):
        nrows = max(1, len(self.hl_rows))
        if len(self.hl_rows) == 0:
            r, _ = self.key_rc
        else:
            r = self.hl_rows[0]
        for i in range(nrows):
            self.vm.insert_blank_row(r)
        self.draw_all()

    def update_hls(self, r, c, one_cell=False):
        if one_cell:
            self.hl_cols = Iset(c)
            self.hl_rows = Iset(r)
            self.rc_org = r, c
            self.key_rc = r, c
            if self.offset > r:
                self.offset = r
            elif r - self.offset >= self.nrows() - 1:
                self.offset = r - self.nrows()
            return
        ro, co = self.rc_org
        self.hl_rows = Iset(
            range(min(r, ro), min(len(self.table), max(r, ro) + 1)))
        if co != -1:
            self.hl_cols = Iset(range(max(0, min(c, co)), max(c, co) + 1))

    @property
    def editing(self):
        return self.popup is not None

    def stop_editing(self):
        if self.editing:
            self.popup.enter()
            self.state = 'up'

    def up(self, shift):
        r, c = self.key_rc
        if r > 0:
            self.stop_editing()
            r -= 1
            self.update_hls(r, c, not shift)
            self.draw_all()

    def down(self, shift):
        r, c = self.key_rc
        if r < len(self.table):
            self.stop_editing()
            r += 1
            self.update_hls(r, c, not shift)
            self.draw_all()

    def left(self, shift):
        if self.editing:
            return

        r, c = self.key_rc
        if c > 0:
            c -= 1
            self.update_hls(r, c, not shift)
            self.draw_all()

    def right(self, shift):
        if self.editing:
            return
        r, c = self.key_rc
        if c < len(self.table.field_names) - 1:
            c += 1
            self.update_hls(r, c, not shift)
            self.draw_all()

    def pg_up(self, shift):
        if self.editing:
            self.stop_editing()
        r, c = self.key_rc
        if r > 0:
            r = max(0, r - (self.nrows() - 1))
            self.update_hls(r, c, not shift)
            self.draw_all()

    def pg_dn(self, shift):
        if self.editing:
            self.stop_editing()
        r, c = self.key_rc
        if r < len(self.table):
            r = min(len(self.table), r + self.nrows() - 1)
            self.update_hls(r, c, not shift)
            self.draw_all()

    def home(self, shift):
        if self.editing:
            return
        r, c = self.key_rc
        if c == 0:
            if r == self.offset:
                if r == 0:
                    return
                else:
                    r = 0
            else:
                r = self.offset
        else:
            c = 0
        self.update_hls(r, c, not shift)
        self.draw_all()

    def end(self, shift):
        if self.editing:
            return
        r, c = self.key_rc
        if c == len(self.table.field_names) - 1:
            if r == len(self.table):
                return
            if r == self.offset + self.nrows() - 1:
                r = len(self.table)
            else:
                r = self.offset + self.nrows() - 1
        else:
            c = len(self.table.field_names) - 1
        self.update_hls(r, c, not shift)
        self.draw_all()

    def tab(self):
        if self.state == 'editing':
            self.stop_editing()
            r, c = self.key_rc
            if c == len(self.table.field_names) - 1:
                if r >= len(self.table) - 1:
                    return
                c = 0
                r += 1
            else:
                c += 1
            self.update_hls(r, c, True)
            self.draw_all()
            self.edit_cell(r, c)
        else:
            self.right(False)

    def left_tab(self):
        if self.state == 'editing':
            self.stop_editing()
            r, c = self.key_rc
            if c == 0:
                if r == 0:
                    return
                c = len(self.table.field_names) - 1
                r -= 1
            else:
                c -= 1
            self.update_hls(r, c, True)
            self.draw_all()
            self.edit_cell(r, c)
        else:
            self.left(False)

    def enter(self):
        try:
            self.edit_cell(*self.key_rc)
        except:
            pass

    def col_widths(self):
        return [col.width for col in self.headers]

    def paste_options(self, row, col=0):
        """
        can paste whole rows replacing highlighted rows or
           inserted
        can paste block over compatible blocks if lines exist
            and highlight is not present or matches block size
        """
        compatible = {'int': ('int', 'float', 'none'),
                      'float:': ('float', 'none'),
                      'str': ('str', 'none'),
                      'none': ('str', 'none'),
                      'iset':('int','iset'),
                      }
        if len(self.vm.clipboard) == 0:
            return []
        result = []
        clip_table = self.vm.clipboard[-1]
        if (len(self.table.field_names) == len(clip_table.field_names)
                and all(tft in compatible[cft] for
                        tft, cft in zip(self.table.field_types,
                                        clip_table.field_types))):
            if col == 0:
                result.append('Paste (insert)')
                if len(self.table) - row >= len(
                        clip_table) and not self.on_append:
                    result.append('Paste (overwrite)')
            return result

        if col + len(clip_table.field_names) >= len(self.table.field_names):
            return []

        for ccol in range(len(clip_table.field_names)):
            tft = self.table.field_types[ccol + col]
            cft = clip_table.field_types[ccol]

            if cft not in compatible[tft]:
                return []

        if len(self.hl_rows) <= 1 and len(self.hl_cols) <= 1:
            return ['Paste (overwrite)']

        if len(self.table) - row < len(clip_table):
            return []

        for ccol in range(len(clip_table.field_names)):
            ft = self.table.field_types[ccol + col]
            if ft not in compatible[clip_table.field_types[ccol]]:
                return []

        return ['Paste (overwrite)']

        # Its multiple cells

    def mouse_wheel(self, event):  # todo here apply ctrl and shift modifiers
        new_offset = self.offset + event.delta//120
        self.offset = max(0,min(len(self.table) - 1, max(0, new_offset)))
        self.slider_pos.set(self.offset)
        # self.draw_all()

    def up_one(self, event):
        self.offset -= 1
        self.slider_pos.set(self.offset)
            # self.draw_all()

    def down_one(self, event):
        self.offset += 1
        self.slider_pos.set(self.offset)

    def mouse_on_line_no(self, action, event):
        y = round(self.line_no_canvas.canvasy(event.y))
        row = self.offset + y // self.line_height()
        self.mouse(action, row, -1)

        # if row<len(self.table):
        #    self.row_select(row)

    def slider_moved(self, p1, p2, p3):
        self.offset=self.slider_pos.get()
        self.draw_all()

    def line_height(self):
        return self.font.line_space + 4

    def nrows(self):
        h = (int(self.main_frame.winfo_height())
             - int(self.header_frame.winfo_height()))

        return h // self.line_height() + 1

    def ask_close(self):
        self.close(True)

    def close(self, update=True):  #None is update and switch view
        width = self.header_frame.right_x_coords[-1]
        height = self.nrows()

        if update is False:
            while len(self.vm.undos) > self.restore_point:
                self.vm.undo()
        self.window.destroy()
        self.finished_func(update, self.offset, self.col_widths(), width,
                           height)

    def switch_to_record_view(self):
        self.close(update=None)

    def mouse(self, action, r, c):
        if r > len(self.table):  # Make sure insert point is valid for undoing
            r = len(self.table)
        if action == 'move':
            if self.state in ('down', 'oncell', 'onlineno'):
                self.update_hls(r, c)
                self.draw_all()
            return
        if action == 'left':
            self.rc_org = r, c
            self.key_rc = r, c
            if self.editing:
                self.stop_editing()
            if r in self.hl_rows and c in self.hl_cols:
                self.update_hls(r, c, True)
                self.draw_all()
                self.state = 'oncell'
            else:
                if c == -1:
                    self.hl_cols = Iset(range(len(self.table.field_names)))
                else:
                    self.hl_cols = Iset(c)
                if r < len(self.table):
                    self.hl_rows = Iset(r)
                else:
                    self.hl_rows = Iset()
                self.state = 'down'
            self.draw_all()
            return

        if action == 'leftup':
            if self.state == 'oncell':
                ro, co = self.rc_org
                if c == co and r == ro:
                    self.state = 'editing'
                    self.edit_cell(r, c)
                else:
                    self.state = 'up'
            else:
                self.state = 'up'  # default
            return
        if action == 'right':
            self.rc_org = r, c
            if self.editing:
                self.stop_editing()
            self.state = 'rightdown'

        if action == 'rightup':
            if r < len(self.table):
                self.on_append = False

            options = ['Cancel']
            ro, co = self.rc_org
            if r != ro or r < len(self.table) and c != co:
                return
            log('mouse right', self.state)

            self.state = 'up'
            if r not in self.hl_rows or c != -1 and c not in self.hl_cols:
                self.hl_rows = Iset()
                self.hl_cols = Iset()
                self.draw_all()
                if r < len(self.table):
                    options.append('Edit')
                paste_options = self.paste_options(r, c)
            else:
                if len(self.hl_cols) == 1 and len(self.hl_rows) == 1:
                    options.append('Edit')
                options += ['Copy', 'Cut', 'Delete']
                try:
                    mr = self.hl_rows[0]
                    mc = self.hl_cols[0]
                    paste_options = self.paste_options(mr, mc)
                except IndexError:
                    paste_options = []
            options += paste_options
            if len(self.vm.undos) > 0:
                options.append('Undo')
            x, y = self.sxy_from_rc(r, c)
            # x+=self.data_canvas.winfo_x()+self.header_frame.winfo_x()+self.window.winfo_x()
            # y+=self.data_canvas.winfo_y()+self.header_frame.winfo_y()+self.window.winfo_y()
            x += self.header_frame.winfo_x() + self.window.winfo_x()
            y += self.data_canvas.winfo_y() + self.window.winfo_y()
            PopupMenu(self.window, x=x, y=y,
                      # todo here could make it less transient
                      choices=options,
                      callback=self.menu_callback)

    def menu_callback(self, item):
        log('MENU callback', item)
        r, c = self.rc_org
        if item == 'Cancel':
            return
        elif item == 'Edit':
            self.state = 'editing'
            self.edit_cell(r, c)
        elif item == 'Copy':
            self.vm.copy(self.hl_rows, self.hl_cols)
        elif item == 'Cut':
            self.vm.cut(self.hl_rows, self.hl_cols)
            self.hl_rows = Iset()
            self.hl_cols = Iset()
        elif item == 'Delete':
            self.vm.delete(self.hl_rows,
                           self.hl_cols)  # todo blank columns if not whole rows
            self.hl_rows = Iset()
            self.hl_cols = Iset()
        elif item == 'Paste (insert)':
            self.vm.paste(r, insert=True)
        elif item == 'Paste (overwrite)':
            self.vm.paste(r, c, insert=False)
        elif item == 'Undo':
            self.undo()
        self.draw_all()

    def undo(self):
        self.vm.undo()
        self.hl_rows = Iset()
        self.hl_cols = Iset()
        self.draw_all()

    def whole_rows_selected(self):
        return len(self.hl_cols) == len(self.table.field_names)

    def sxy_from_rc(self, r, c):

        x = 0  # self.data_canvas.winfo_x()
        y = 0  # self.data_canvas.winfo_y()
        if c == -1:
            dx = -20
        else:
            dx = self.header_frame.x_coords[c]
        return x + dx, y + (r - self.offset) * self.line_height()

    def cell_val(self, r, c):
        return f'{getattr(self.table[r], self.table.field_names[c])}'

    def write_cell(self, r, c, value):
        cell_type = self.table.field_types[c]
        if cell_type == 'int':
            try:
                value = int(value)
            except:
                return
        elif cell_type == 'float':
            try:
                value = float(value)
            except:
                return
        elif cell_type=='iset':
            try:
                value=Iset(value)
            except:
                return

        self.vm.update_field(r, self.table.field_names[c], value)

    def edit_cell(self, r, c):
        x, y = self.sxy_from_rc(r, c)
        if self.editing:
            self.stop_editing()

        def write_back(value, action):
            print_('CELL', r, c, 'Writing back', value,action)

            log('CELL', r, c, 'Writing back', value)
            if value is not None:
                self.write_cell(r, c, value)
                self.draw_all()
            self.popup.destroy()
            self.popup = None
            self.state = 'up'
            if action=='down':
                self.down(False)    #todo here insert line?
            if action=='right':
                self.right(False)
            elif action=='left':
                self.left(False)

        self.popup = PopupEntry(self.data_canvas, self.cell_val(r, c),
                                write_back,
                                history=self.history)
        self.popup.place(
            x=x,
            y=y,
            width=(self.header_frame.right_x_coords[c]
                   - self.header_frame.x_coords[c]),
            height=self.line_height(),
            anchor='nw')

    def row_select(self, row):
        log('row select', row)

    def header_callback(self, action, *args):
        #print('header action:', action, 'args:', args)
        self.draw_all()

    def draw_all(self):
        # print('redraw all')
        #print('OFFSET IS ',self.offset)
        self.slider['length']=(self.data_display.nrows()-1)*self.line_height()
        self.data_display.redraw_all(self.offset, self.hl_rows, self.hl_cols)