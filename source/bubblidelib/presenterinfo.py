"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from bubblib.globaldefs import markup_type_map, render_defaults
from bubblib.gutils import cropped_string
from bubblib.utils import try_eval, log
from bubblib.machineimports import get_imported_machine_init


def get_mu_text(param):
    if param[0] == '':
        return param[1]
    mu_type = markup_type_map[param[0]]
    #print('MUTYPE=',mu_type,param[1])
    return param[1]


class LoopPresenterInfo:
    """
    Loop block

    This block causes the linked 'For' block to run 'loopback' code instead of
    'loop-setup' code. It also works similarly for programmed blocks with 'loop'
    checked in their interfaces.  A 'For' block's loop-setup code creates a
    sequence which is iterated through via the loop block.  A programmed
    block allows a more generalised looping behaviour.
    """
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, _index):
        return '  Loop'


class CreatePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return f'Create {self.params[0]}'
        return f'{self.params[index]}'

class SortPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)-1

    def display_line(self, index):
        if index == 0:
            return f'Sort {self.params[0]}'+(
                ' (desc)' if self.params[1]=='1' else'')
        return f'{self.params[index+1]}'


class DestroyPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, _index):
        return f'Destroy {self.params[0]}'


class DeletePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 2

    def display_line(self, index):
        if index == 0:
            return f'Delete {self.params[1]}'
        return f'From {self.params[0]}'


class SelectPresenterInfo:
    headings = ["Select", "From", "Where", "Filter"]

    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 4 if self.params[3]!='' else 3

    def display_line(self, index):
        return f'{self.headings[index]} {self.params[index]}'


class InsertPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return f'Insert into {self.params[0]}'
        elif index == 1:
            return f'@ index {self.params[1]}'
        else:
            return (f'{self.params[index][0]} = {self.params[index][1]}')


class JoinPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 0


class UpdatePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return f'Update {self.params[0]}'
        elif index == 1:
            return f'Row(s) {self.params[1]}'
        else:
            return (f'{self.params[index][0]} = {self.params[index][1]}')


class ForPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 2

    def display_line(self, index):
        if index == 0:
            return f'For each {self.params[0]}'
        else:
            return f'in {self.params[1]}'



def get_string(value):
    if isinstance(value,str):
        return value
    if isinstance(value,(int,float,complex,bool)):
        return value.__str__()
    if isinstance(value,list):
        return f'{value}'
        if len(value)==0:
            return value.__str__()
        if len(value)==1:
            return f'[{get_string(value[0])}]'
        if len(value)==2:
            return f'[{get_string(value[0])},{get_string(value[1])}]'
        return f'[{get_string(value[0])},{get_string(value[1])},...]'
    if isinstance(value,tuple):
        if len(value)==0:
            return '()'
        if len(value)==1:
            return f'({get_string(value[0])})'
        if len(value)==2:
            return f'({get_string(value[0])},{get_string(value[0])})'
        return f'[{get_string(value[0])},{get_string(value[1])},...]'
    return str(value)

class FormulaPresenterInfo:
    def __init__(self, params, globs):
        self.params = params
        self.globs = globs
        self.cache={}



    def ndisplay_lines(self):
        return 1 + len(self.params)

    def display_line(self, index):
        if index == 0:
            return 'Live data'
        try:
            return self.cache[index]
        except KeyError:
            p = self.params[index - 1]
            if p.startswith('='):
                self.cache[index]=result=get_string(try_eval(p[1:], self.globs))
            else:
                self.cache[index]=result=f'{p} = {get_string(try_eval(p, self.globs))}'
            return result


class WritePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return f'Write {self.params[0]}'
        return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'

class ButtonPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return f'Button {self.params[0]}'
        return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'

class PolygonPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)-1

    def display_line(self, index):
        if index == 0:
            return f'Polygon ({self.params[0]},{self.params[1]})'
        return f'{self.params[index+1][0]} = {get_mu_text(self.params[index+1])}'


class RectanglePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params) - 1

    def display_line(self, i):
        if i == 0:
            return f'Rectangle ({self.params[0]},{self.params[1]})'
        return f'{self.params[i + 1][0]} = {get_mu_text(self.params[i + 1])}'


class EllipsePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params) - 1

    def display_line(self, i):
        if i == 0:
            return f'Ellipse ({self.params[0]},{self.params[1]})'
        return f'{self.params[i + 1][0]} = {get_mu_text(self.params[i + 1])}'

class ArcPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params) - 1

    def display_line(self, i):
        if i == 0:
            return f'Arc ({self.params[0]},{self.params[1]})'
        return f'{self.params[i + 1][0]} = {get_mu_text(self.params[i + 1])}'


class LinePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params) - 1

    def display_line(self, i):
        if i == 0:
            return f'Line({self.params[0]},{self.params[1]})'
        return f'{self.params[i + 1][0]} = {get_mu_text(self.params[i + 1])}'


class ImagePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return f'Show ({self.params[0]})'
        return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'


class WaitPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, index):
        return ' ' + self.params[0]


class MenuPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1 + len(self.params)

    def display_line(self, index):
        if index == 0:
            return 'Menu'
        return self.uncentered_display_line(index)

    def uncentered_display_line(self, index):
        p = self.params[index - 1]
        if isinstance(p, str):
            return p
        else:
            return f'{p[0]} = {get_mu_text(p)}'


class ColourMenuPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return f'Colour Menu @{self.params[0]}'
        return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'


class FileMenuPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return (f'File open @{self.params[0]}')
        # print('FILE_MENUUUUU',self.params[index])
        return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'


class AlertPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return (f'Alert: {self.params[0]}')
        return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'


class AskUserPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return (f'Ask: {self.params[0]}')
        return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'


class InputPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return (f'Input {self.params[0]}')
        return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'


class ChoicePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return (f'Choose @{self.params[0]}')
        elif index == 1:
            return (f'from {self.params[1]}')
        return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'


class AssignPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return max(1, len(self.params))

    def display_line(self, index):
        if len(self.params) == 0:
            return ' = '
        return f'{self.params[index][0]} = {self.params[index][1]}'


class IfPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, index):
        return ' ?'


class PagePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return (f'Page {self.params[0]}')
        return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'


class PageClosePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, index):
        return 'Destroy page'


class PageClearPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, index):
        return 'Clear page'


class PageUpdatePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params) + 1

    def display_line(self, i):
        if i == 0:
            return (f'Update page')
        return f'{self.params[i - 1][0]} = {get_mu_text(self.params[i - 1])}'

class PrintPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, i):
        if i == 0:
            return (f'Print {self.params[0]}')
        return f'{self.params[i][0]} = {get_mu_text(self.params[i])}'

class TableViewPresenterInfo:
    def __init__(self, params):
        self.params = params

    def line(self,fields):
        return ''.join([cropped_string(f'{f}',self.params[2][i],self.font,render_defaults.grid)
                for i,f in enumerate(fields)])


    def ndisplay_lines(self):
        return 1
    def display_line(self,i):
        return self.params[0]

class TextPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params[0].split('<br />'))

    def display_line(self, index):
        # print('RETURNING',self.params[0].split('<br />')[index])
        return self.params[0].split('<br />')[index]


class CallPresenterInfo:
    def __init__(self, params, diag_params):
        self.params = params
        self.diag_params = diag_params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return (f'{self.params[0]}')
        return f'{self.diag_params[index]} = {self.params[index]}'

class ImportPresenterInfo:
    def __init__(self, params):
        init=get_imported_machine_init(params[0])
        try:
            self.ipars=init['diags'][params[1]]["signature"]["params"]
        except:
            self.ipars=[]
        self.params = params

    def ndisplay_lines(self):
        return len(self.ipars)+2

    def display_line(self, index):
        if index == 0:
            return (f'Imported {self.params[1]}')
        elif index == 1:
            return (f'from {self.params[0]}')
        v=self.params[index] if index<len(self.params) else ""
        return f'{self.ipars[index-2]}={v}'

class AsyncPresenterInfo:
    def __init__(self, params):
        init=get_imported_machine_init(params[0])
        try:
            self.ipars=init['diags'][params[1]]["signature"]["params"][1:]
        except:
            self.ipars=[]
        self.params = params

    def ndisplay_lines(self):
        return len(self.ipars)+2

    def display_line(self, index):
        if index == 0:
            return (f'From {self.params[0]}')
        elif index == 1:
            return (f'Call {self.params[1]}')
        try:
            par=self.params[index]
        except IndexError:
            par=''
        return f'{self.ipars[index-2]}={par}'

class LinkPresenterInfo:
    def __init__(self, params, link_names=[]):
        self.params = params
        self.link_names = link_names

    def ndisplay_lines(self):
        return 2

    def display_line(self, index):
        try:
            text = self.link_names[int(
                self.params[0])]  # todo here this should not generate exception
        except:
            text = ''
        if index == 0:
            return 'Link'
        return text


class PythonPresenterInfo:

    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        try:
            return self.params[index]
        except:
            return ''

class DialogPresenterInfo:
    def __init__(self,params):
        self.params=params
    def ndisplay_lines(self):
        return len(self.params)+1

    def display_line(self, ind):
        if ind==0:
            return 'Dialog'
        elif ind<3:
            return self.params[ind-1]
        return f'{self.params[ind-1][0]} = {get_mu_text(self.params[ind-1])}'

class EditorPresenterInfo:
    def __init__(self,params):
        self.params=params
    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, ind):
        if ind==0:
            return f'{self.params[0]} Editor'
        elif ind==1:
            if self.params[0]=='Text':
                return f'Variable: {self.params[1]}'
            return f'Table: {self.params[1]}'
        try:
            return f'{self.params[ind][0]} = {get_mu_text(self.params[ind])}'
        except Exception as e:
            return f'ERROR line {ind}:{e}'

class FileMkDirPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, index):
        return f'Make folder {self.params[0]}'


class FileSavePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 2

    def display_line(self, index):
        if index == 0:
            return f'Save: {self.params[0]}'
        return f'to: {self.params[1]}'


class FileDeletePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, index):
        return f'Delete: {self.params[0]}'


class FileExecPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        if self.params[1]=='1':
            return 2
        return 1

    def display_line(self, index):
        if index==0:
            return f'Execute: {self.params[0]}'
        if index==1:
            return 'Synchronously'

class PlayMediaPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        if self.params[2]=='1':
            return 3
        return 2

    def display_line(self, index):
        if index==0:
            return f'{self.params[0]}'
        if index==1:
            return f'{self.params[1]}'
        if index==2:
            return 'Synchronously'


class FileAppendPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 2

    def display_line(self, index):
        if index == 0:
            return f'Append: {self.params[0]}'
        return f'to: {self.params[1]}'


class FileCopyPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 2

    def display_line(self, index):
        if index == 0:
            return f'Copy: {self.params[0]}'
        return f'to: {self.params[1]}'


class FileRenamePresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 2

    def display_line(self, index):
        if index == 0:
            return f'Rename: {self.params[0]}'
        return f'to: {self.params[1]}'


class SwitchPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return f'Switch {self.params[0]}'
        return self.params[index]


class ImageViewPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return f'Button {self.params[0]}'
        return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'


class ScrollbarPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)-1

    def display_line(self, index):
        if index == 0:
            return f'Scrollbar {self.params[0]}..{self.params[1]}'
        else:
            return f'{self.params[index+1][0]} = {get_mu_text(self.params[index+1])}'

class InputDispPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return f'TextInput {self.params[0]}'
        else:
            return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'

class TextedPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return f'TextEd {self.params[0][:8]}...'
        else:
            return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'

class CheckboxPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)

    def display_line(self, index):
        if index == 0:
            return f'Checkbox {self.params[0]}'
        else:
            return f'{self.params[index][0]} = {get_mu_text(self.params[index])}'

class RadioPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)+1

    def display_line(self, index):
        if index == 0:
            return f'Radio group'
        else:
            p=self.params[index-1]
            if isinstance(p,list):
                return f'{p[0]} = {get_mu_text(p)}'
            else:
                return p

class ChoiceDispPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return len(self.params)+1

    def display_line(self, index):
        if index == 0:
            return f'Chooser from'
        elif index==1:
            return f'{self.params[0]}'
        else:
            p=self.params[index-1]
            return f'{p[0]} = {get_mu_text(p)}'

class InterfacePresenterInfo:
    def __init__(self, diag):
        self.diag=diag

    def ndisplay_lines(self):
        return len(self.diag.params)

    def display_line(self, index):
        if index == 0:
            return ' Interface'
        return self.diag.params[index]

class DefaultVariableInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, index):
        return self.params[0]

class BubblPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, _index):
        return self.params[0]

class WeblinkPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, _index):
        return self.params[0]

class CommandPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, _index):
        return self.params[0]

class GraphicPresenterInfo:
    def __init__(self, params):
        self.params = params

    def ndisplay_lines(self):
        return 1

    def display_line(self, _index):
        return self.params[0]

info_factory = {
    'ASSIGN': AssignPresenterInfo,
    'IF': IfPresenterInfo,
    'WAIT': WaitPresenterInfo,
    'SWITCH': SwitchPresenterInfo,
    'FOR': ForPresenterInfo,
    'LOOP': LoopPresenterInfo,
    'PYTHON': PythonPresenterInfo,
    'JOIN': JoinPresenterInfo,

    'CREATE': CreatePresenterInfo,
    'SORT': SortPresenterInfo,
    'INSERT': InsertPresenterInfo,
    'DELETE': DeletePresenterInfo,
    'DESTROY': DestroyPresenterInfo,
    'UPDATE': UpdatePresenterInfo,
    'SELECT': SelectPresenterInfo,

    'PAGE': PagePresenterInfo,
    'PAGE_CLOSE': PageClosePresenterInfo,
    'PAGE_CLEAR': PageClearPresenterInfo,
    'PAGE_UPDATE': PageUpdatePresenterInfo,
    'PRINT':PrintPresenterInfo,
    'WRITE': WritePresenterInfo,
    'LINE': LinePresenterInfo,
    'IMAGE': ImagePresenterInfo,
    'POLYGON': PolygonPresenterInfo,
    'RECT': RectanglePresenterInfo,
    'ELLIPSE': EllipsePresenterInfo,
    'ARC':ArcPresenterInfo,

    'INPUT': InputPresenterInfo,
    'CHOICE': ChoicePresenterInfo,
    'ASK_USER': AskUserPresenterInfo,
    'MENU': MenuPresenterInfo,
    'ALERT': AlertPresenterInfo,
    'FILE_MENU': FileMenuPresenterInfo,
    'COLOUR_MENU': ColourMenuPresenterInfo,

    'FILE_MKDIR': FileMkDirPresenterInfo,
    'FILE_SAVE': FileSavePresenterInfo,
    'FILE_APPEND': FileAppendPresenterInfo,
    'FILE_DELETE': FileDeletePresenterInfo,
    'FILE_RENAME': FileRenamePresenterInfo,
    'FILE_COPY': FileCopyPresenterInfo,
    'FILE_EXECUTE': FileExecPresenterInfo,
    'PLAY':PlayMediaPresenterInfo,


    'VARIABLE': DefaultVariableInfo,
    'DBVARIABLE': DefaultVariableInfo,

    'TABLE': DefaultVariableInfo,
    'TEXT': TextPresenterInfo,
    'IMAGE_VIEW': ImageViewPresenterInfo,
    'BUTTON': ButtonPresenterInfo,
    'SCROLLBAR': ScrollbarPresenterInfo,
    'INPUTDISP':InputDispPresenterInfo,
    'CHECKBOX':CheckboxPresenterInfo,
    'RADIO':RadioPresenterInfo,
    'DIALOG': DialogPresenterInfo,
    'EDITOR': EditorPresenterInfo,
    'CHOICEDISP':ChoiceDispPresenterInfo,
    'TEXTED':TextedPresenterInfo,
    'BUBBL':BubblPresenterInfo,
    'WEBLINK':WeblinkPresenterInfo,
    'COMMAND':CommandPresenterInfo,
    'GRAPHIC':GraphicPresenterInfo,
    'ASYNC':AsyncPresenterInfo,
    'IMPORT':ImportPresenterInfo,

}

# print('","'.join([n for n in blockFactory]))

'''
    'EDITOR'
    'DIALOG'
    'SORT',
    'PAGE_REFRESH',
    'SECTOR'
    'OUTPUT_AT'
'''

def get_presenter_info(type_name, params, diag,index=0):
    if type_name in info_factory:
        return info_factory[type_name](params)
    if type_name == 'CALL':
        #result=
        return CallPresenterInfo(params, diag.mach.diags[params[0]].params)
        #return result #CallPresenterInfo(params, diag.mach.diags[params[0]].params)
    elif type_name == 'LINK':
        return LinkPresenterInfo(params,  diag.sig["linknames"])
    elif type_name == 'FORMULA':
        return FormulaPresenterInfo(params, diag.variables)
    elif type_name == 'INTERFACE':
        return InterfacePresenterInfo(diag)
    else:
        log('UNKNOWN BLOCK TYPE',type_name)

def main():
    loop=LoopPresenterInfo([])

if __name__=='__main__':
    main()