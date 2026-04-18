"""sysvars creates access to system resources.
Resources are accessed via the following multi-attribute objects
which are mapped in every diagram namespace:
_os  Accesses various os functions
_fs  Accesses the file system
_nw  Accesses network sockets
_pg  Accesses the display and 'windows' (pages) and graphics etc
_db  Accesses global variables and tables
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import base64
import socket
import time
from ast import literal_eval
from contextlib import closing

import platform
import threading
import os, sys, shutil, zipfile, datetime

import tkinter

from . import network
from .base64icons import icons
from .bubblpage import BubblPage
from .globaldefs import valid_sys_var_names
from .iset import Iset
from .logger import Logger
from .network import TCPClient
from .uiserver import ui
from .utils import home, desktop, documents, downloads, log, runtime_log
from .bubblevent import TimerEvent, RxEvent, RqEvent
from .bubbljson import jsonable, toJSON, fromJSON
from .filetable import FileTable
from .gutils import BUBBLImage, universal_fonts, truetype_fonts, cursors, \
    BubblFont, get_image, save_canvas_message
from .processmanager import ProcessManager, SynchProcess
from .processtable import ProcessTable
from .table import Table, RawTable

def encryptorWriter(self, val, mach):
    mach.cypher.seedInit(str(val))

def levDistWriter(self, val, mach):
    try:
        mach.levDistMax = int(val)
    except:
        pass

class SysVars:
    def apply_deltas(self, deltas):
        for d in deltas:
            self._mach.log(f'sysvar applying delta:{d}={deltas[d]}')
            if d in self.__dict__:
                self.__dict__[d] = deltas[d]

class IconAccessor:
    def __init__(self):
        self.names=list(icons)

    def __getitem__(self,index):
        try:
            return f'base64:{icons[index]}'
        except:
            return None

    def __iter__(self):
        return self.names.__iter__()

class PageVars(SysVars):
    """Display
Bubbl can create 'windows' on the computer display. These are
referred to as 'pages' and can be directly accessed through the
system class '_pg'. _pg behaves as the current page and, if indexed
with the name of a page, behaves as that page.
Pages have the following attributes/properties:
    Attr/Prop   Type     Description
    ---------   ----     -----------
    name        r        The unique name of the page given when created
    ink         r/w      Default colour for text and lines added to the page
    paper       r/w      Background colour of the page
    width       r/w      Width in pixels of drawing area of the page
    height      r/w      Height in pixels of drawing area of the page
    cx          r/w      Default x-coord of next added item
    cy          r/w      Default y-coord of next added item
    font        r/w      Default font for text items added
    cursor      r/w      Mouse cursor
    closeable   r/w      If True (default) clicking the 'close' icon closes the page
                         otherwise a 'Close' event is sent to the running program
    fixed_size  r/w      If True the page cannot be resized
    scrollable  r/w      If True scroll-bars are created automatically if the
                         page's canvas is larger than its window
    table       r        A table with each row referencing an item drawn on the page.
                         The items are drawn in the same order as the rows.
                         The table's 'field_names' attribute returns:
                            ['thing','x','y','width','height','tags','points',
                            'dxys']
                         These can be used in table searches and updates (e.g.
                         the 'Select' and 'Update' instructions), with changes
                         to values automatically updating the displayed items.
                         Each row of the table may have additional fields which
                         correspond to the 'markups' of the instruction which
                         creates the item. These fields can be referenced in
                         table 'Select' and 'Update' instructions using
                         '_rec.&lt;field&gt;' syntax.
    contents    r/w      A list of dictionaries, each of which specifies an
                         item which has been, or is to be, drawn on the page.
    markups     r/w      A dictionary of the page's settings
    fullscreen  r/w      If set to True the page takes up the whole screen for
                         5 seconds. The time limit is to prevent accidentally
                         disabling other programs on the computer.  The page
                         will remain in fullscreen mode if it is re-enabled
                         before the 5-second time limit.
                         Setting it to False returns the page to normal
                         immediately.
    focus                Name of the page (window) with the current keyboard focus.
                         '' if focus is outside the program
    ui          r        a mapping of page's tkinter Canvas item-id to displayed item
    left_margin r/w      Left margin for printing and saving to file (in 'points'=1/72in)
    top_margin  r/w      Top margin for printing and saving to file (in 'points'=1/72in)
    dragged     r/w      Contents of data for a drag initiated on this page.
                         Set this to a string, or list of strings, or None to
                         disable DND dragging from the page.
    mime        r/w      Can be set to 'DND_Files' or 'DND_Text' to indicate
                         the meaning of dragged data from this page (see
                         'dragged' above).
    canvas               The Tkinter Canvas object onto which is drawn

Pages also have the following methods:
    scaled_contents(scale_factor)
        Returns list of dictionaries like 'contents' above, but which produce
        a resized page (including individual elements). This method can be used
        in conjunction with 'contents' above to increase the resolution of the
        image returned by 'get_pil' below.
    get_pil(monochrome=False,background=False)
        Returns a 'PIL' image rendered from the canvas. If the 'background'
        parameter is False, the image returned is in 'RGBA' format with a
        transparent background, otherwise it is rendered in 'RGB' or 'L' format.
    tagged(tag)
        Returns the first item in the display list whose tags contain tag, or
        None if no items have the tag.

The system class _pg has the following additional attributes:
    Attr/Prop   Type     Description
    ---------   ----     -----------
    mx          r        Mouse screen x-coordinate
    my          r        Mouse screen y-coordinate
    screen_size r        (width,height) of the current display screen in pixels
    current     r        The currently selected page for output
    refresh()   function Update the display
    fonts       r        A non-exhaustive list of available font families
    icons       r        A copy of a dict of Base64 encoded Icon .png images
    ppp         r/w      The number of display pixels per 'point' (printer's
                         point = 1/72"). Changing this value affects the size
                         of the printed output of images and pages sent to a
                         printer. It does not affect font sizes
    base_ppp    r        The value of _pg.ppp on startup

Indexing _pg or _pg[&lt;page_name&gt;] with integers accesses the page's contents,
with items drawn in index order.  Each item has directly accessible fields
which can be used to update its appearance (e.g. position on the page) in
real time.  The accessible fields correspond to the available 'markups' in
the item's 'create-block'.

When creating a page a 'top-line' menu can be added via the 'menu' markup.
The menu structure is made up of a list of items. If an item is a string, it
is a single menu entry, if it is a list, the first element is the name of a
dropdown menu and the rest of the elements are the dropdown items.
When the user selects a menu item, a MenuEvent is generated with a value
of the name of the top-line menu, or a list of the top-line menu name and
dropdown selection.

Printing
--------
Pages can be printed with the 'Print' block.  The page's contents
is converted to a suitable output format and written to a file
which is then optionally sent to a printer. The available
output formats are '.png', '.jpg', '.txt','.ps','.eps','.pdf'*

*Note: To output to a .pdf file, ghostscript needs to be installed on
       the system.

For .ps, .eps and .pdf files there can be discrepancies between
monitor and printer resolutions. This can be adjusted for using
the configuration setting 'print_scale' which is also accessible
programmatically via _mach.config['print_scale'].
The configuration parameters 'left_margin' and 'top_margin' add
space to the left of and above the printed output on the page and
can be overridden on a per-page basis by setting the pages'
'left_margin' and 'right_margin' parameters.
"""
    def __init__(self, mach):
        self._mach = mach
        for name in ('ink','paper','width','height',
                     'cx','cy','font','cursor','x','y'):
            valid_sys_var_names.add(f'_pg.{name}')
        self.icon_accessor=IconAccessor()
        self._base_ppp=float(ui.root.call('tk','scaling'))

    @property
    def screen_size(self):
        return ui.root.winfo_screenwidth(), ui.root.winfo_screenheight()

    @property
    def focus(self):
        for p in self._mach.pages:
            if self._mach.pages[p].focus:
                return p
        return None

    @focus.setter
    def focus(self, value):
        try:
            self._mach.pages[value].focus = True
        except:
            self._mach.log(f'Failed to set focus on {value}',level=Logger.INFO)

    @property
    def current(self):
        return self._mach.current_page

    def refresh(self):
        try:
            self.current.refresh()
        except:
            self._mach.log('Unable to refresh page',level=Logger.INFO)


    @property
    def base_ppp(self):
        return self._base_ppp

    @property
    def ppp(self):
        return ui.ppp

    @ppp.setter
    def ppp(self,value):
        if not ui.ok_set_ppp(value):
            self._mach.log('Unable to set pixels per point',level=Logger.INFO)

    @property
    def pages(self):
        return list(self._mach.pages.values())

    def _tables(self):
        return [page._contents_table for page in self.pages]

    def tagged(self,tag):
        try:
            return self._mach.current_page.tagged(tag)
        except:
            return None

    def __len__(self):
        try:
            return len(self._mach.current_page)
        except:
            try:
                return len(self._mach.pages)
            except:
                return 0

    def __iter__(self):
        return self._mach.pages.__iter__()

    def __getitem__(self, index):
        if isinstance(index, str):
            try:
                return self._mach.pages[index]
            except:
                return None
        else:
            try:
                return self._mach.current_page[index]
            except:
                return None

    def __setitem__(self, key, value):
        if isinstance(key, str):
            try:
                setattr(self._mach.current_page, key, value)
            except Exception as e:
                self._mach.log(f'failed to set current page attribute {key} to {value}',
                      e,level=Logger.INFO)

    @property
    def table(self):
        try:
            return self._mach.current_page.table
        except:
            return None

    @property
    def contents(self):
        try:
            return self._mach.current_page.contents
        except:
            return None
    @contents.setter
    def contents(self,contents):
        try:
            self._mach.current_page.contents=contents
        except:
            pass

    @property
    def markups(self):
        try:
            return self._mach.current_page.markups
        except:
            return None
    @markups.setter
    def markups(self,markups):
        try:
            self._mach.current_page.markups=markups
        except:
            pass

    @property
    def mouse_over(self):
        try:
            return self._mach.current_page.mouse_over
        except:
            return []

    def ui(self, key):
        try:
            return self._mach.current_page.ui[key]
        except:
            return None

    @property
    def mx(self):
        return ui.mx()
    @property
    def my(self):
        return ui.my()

    @property
    def width(self):
        try:
            return self._mach.current_page.width
        except:
            return 0

    @width.setter
    def width(self, value):
        try:
            self._mach.current_page.width = value
        except:
            pass

    @property
    def height(self):
        try:
            return self._mach.current_page.height
        except:
            return 0

    @height.setter
    def height(self, value):
        try:
            self._mach.current_page.height = value
        except:
            pass

    @property
    def ink(self):
        try:
            return self._mach.current_page.ink
        except:
            return None

    @ink.setter
    def ink(self, value):
        try:
            self._mach.current_page.ink = value
        except:
            pass

    @property
    def paper(self):
        try:
            return self._mach.current_page.paper
        except:
            return None

    @paper.setter
    def paper(self, value):
        try:
            self._mach.current_page.paper = value
        except:
            pass

    @property
    def x(self):
        try:
            return self._mach.current_page.x
        except:
            return 0

    @x.setter
    def x(self, value):
        try:
            self._mach.current_page.x = value
        except:
            pass

    @property
    def y(self):
        try:
            return self._mach.current_page.y
        except:
            return None

    @y.setter
    def y(self, value):
        try:
            self._mach.current_page.y = value
        except:
            pass

    @property
    def cx(self):
        try:
            return self._mach.current_page.cx
        except:
            return 0

    @cx.setter
    def cx(self, value):
        try:
            self._mach.current_page.cx = value
        except:
            pass

    @property
    def cy(self):
        try:
            return self._mach.current_page.cy
        except:
            return None

    @cy.setter
    def cy(self, value):
        try:
            self._mach.current_page.cy = value
        except:
            pass

    @property
    def font(self):
        try:
            return self._mach.current_page.font
        except:
            return None

    @font.setter
    def font(self, value):
        try:
            self._mach.current_page.font = BubblFont(value)
        except Exception as e:
            log('Unable to set font',e,level=2)

    @property
    def fullscreen(self):
        try:
            return self._mach.current_page.fullscreen
        except:
            return False
    @fullscreen.setter
    def fullscreen(self,value):
        try:
            self._mach.current_page.fullscreen=value
        except Exception as e:
            log('Unable to set fullpage mode',e,level=2)



    @property
    def name(self):
        return self._mach.current_page.name

    @property
    def cursor(self):
        return self._mach.current_page.cursor

    @cursor.setter
    def cursor(self, value):
        self._mach.current_page.cursor = value

    @property
    def fonts(self):
        return universal_fonts + truetype_fonts

    @property
    def cursors(self):
        return list(cursors)

    @property
    def icons(self):
        return self.icon_accessor

    @property
    def dragged(self):
        try:
            return self._mach.current_page.dragged
        except:
            return None
    @dragged.setter
    def dragged(self,value):
        try:
            self._mach.current_page.dragged=value
        except Exception as e:
            self._mach.log('Illegal setting of _pg.dragged',e,level=2)

    @property
    def mime(self):
        try:
            return self._mach.current_page.mime
        except:
            return None
    @mime.setter
    def mime(self,value):
        try:
            self._mach.current_page.mime=value
        except Exception as e:
            self._mach.log('Illegal setting of _pg.mime',e,level=2)
    @property
    def canvas(self):
        try:
            return self._mach.current_page.canvas
        except:
            return None

    @property
    def menu(self):
        try:
            return self._mach.current_page.menu
        except:
            return None
    @menu.setter
    def menu(self,value):
        try:
            self._mach.current_page.menu=value
        except Exception as e:
            self._mach.log('Illegal setting of _pg.menu',e,level=2)

    def text_width(self, font, text):
        return BubblFont(font).width(text)

    def get_pil(self, background=False, monochrome=False):
        try:
            return self._mach.current_page.get_pil(background=background,
                                                   monochrome=monochrome)
        except:
            return None


    def scaled_contents(self, scale):
        try:
            return self._mach.current_page.scaled_contents(scale)
        except:
            return None

    def tagged(self,tag):
        try:
            return self._mach.current_page.tagged(tag)
        except:
            return None


class FileVars(SysVars):
    """_fs System Variable
===================
This variable gives access to the underlying file system
(e.g. Windows or Linux). It has the following properties
which can be referenced with '_fs.&lt;property&gt;'

Property    Type    Description
--------    ----    -----------
program     r/o     Full path of bubbl executable
home        r/o     Full path of user 'home' folder/directory
separator   r/o     Path separator for underlying operating system
sep         r/o     Same as separator
working     r/w     Current working folder/directory
media       r/w     Current image/sound file cache directory
desktop     r/o     Full path to user's desktop folder/directory
encoding    r/w     Encoding used for text files (default 'utf_8')
encodings   r/o     Non-exhaustive list of available text encodings
message     r/w     Description of last file operation ('Ok' for success)
folder      r/w     A table containing the contents of a folder/directory.
                    Writing a 'path' to the variable fills the table '_fs.files' with
                    the folder/directory contents of the path.
                    If the path contains a comma, the text before the comma
                    should refer to a zip file, and the text after the comma
                    a folder within the zip file
files       r/o     A table of the contents of the folder '_fs.folder' with
                    the following field names:
                        ["Name","Ext","Dir","Size","Time"]
                    where Dir  is true if the entry is a directory,
                          Size is the size of the file in bytes or the
                               number of directory entries
                          Time is 'Seconds since 00:00 hrs on 1.1.1970 CE UTC'

It has the following methods:

_fs.root(filename)
        Returns the root (e.g. 'C:/' for Windows) of the expanded
        absolute path to filename
_fs.filled_out_filename(filename)
        Returns the fully expanded absolute path to filename
_fs.read(filename,json=False,python=False)
        Returns the contents of a text file as follows:
            If 'json' parameter is True it returns the JSON contents of the file
            decoded into a Python object.

            If 'python' parameter is True, it returns a list of the lines of the
            file each interpreted as a Python 'literal' value.

            Otherwise, it returns the lines of the file as a list of strings.

        Files can be read from 'zip' files by including a comma in the
        filename separating the 'zip' filename from the filename within
        the 'zip' file.
_fs.image(source)
        Returns a BubblImage. If source is a file, the image is loaded from
        the file (e.g. .png, .jpeg, .gif and other file types). If not
        it attempts to load the image interpreting source as a base64
        encoded '.png' image.
_fs.exists(filename)
        Returns True if filename is an existing file or directory
_fs.save(filename,object)
_fs.json(object)
        Returns a JSON representation of the object or None if it cannot
        be represented as JSON
_fs.name(filepath)
        Returns the filename part without the path or extension
_fs.path(filepath)
        Returns the path part of a filename after fully expanding it
_fs.ext(filepath)
        Returns the extension of a filename (including the '.')
"""

    def __init__(self, mach):
        self._mach = mach
        self.encoding = 'utf_8'
        self.message = 'Ok'
        self._file_table = FileTable()
        self._folder=''
        for name in ('working','media','encoding','message','folder'):
            valid_sys_var_names.add(f'_fs.{name}')
        # self._file_table=None #FileTable()

    def read(self, filename, json=False,python=False):
        parts = filename.split(',')
        if len(parts) == 2:
            try:
                with zipfile.ZipFile(parts[0], 'r') as f:
                    with f.open(parts[1]):
                        contents = f.read()
            except Exception as e:
                self.message = f'Failed to read zip file:{e}'
                return ''
        else:
            try:
                with open(filename, "r") as f:
                    contents = f.read()
            except Exception as e:
                self.message = f'Failed to read file:{e}'
                return ''
        try:
            if json:
                return fromJSON(contents)
            elif python:
                return [literal_eval(line) for line in contents.splitlines()]
            else:
                return contents.splitlines()
        except Exception as e:
            self.message = f'Failed to read file:{e}'
            return ''

    @property
    def program(self):
        return os.path.abspath(sys.argv[0])

    def exists(self, filename):
        filename=f'{filename}'
        if filename.endswith(os.sep):
            return os.path.isdir(self.filled_out_filename(filename[:-1]))
        return os.path.isfile(self.filled_out_filename(filename))

    @property
    def encodings(self):
        result = ('utf_8', 'utf_16', 'utf_16_be', 'utf_16_le')

    @property
    def home(self):
        return home()

    @property
    def separator(self):
        return os.sep

    @property
    def sep(self):
        return os.sep

    @property
    def working(self):
        return os.getcwd() + self.separator

    @working.setter
    def working(self, value):
        if value.endswith(os.sep):
            value=value[:-len(os.sep)]
        try:
            os.chdir(value)
        except Exception as e:
            self._mach.log(f'Failed to change directory: {e}',level=Logger.INFO)

    @property
    def media(self):
        return self.working + 'media' + self.separator

    def _make_dirs(self, path):
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            self._mach.log('Failed to make directory', e,level=Logger.INFO)

    def _get_image_filename(self):
        if not self.exists(self.media):
            self._make_dirs(self.media)
        already = [item.name
                   for item in os.scandir(self.media)
                   if item.name.startswith('image_')]
        exts = Iset(range(100000))  # should be enough...
        for name in already:
            try:
                exts -= int(name[6:-4])
            except:
                pass
        return self.media + f'image_{exts[0]}.png'

    @property
    def desktop(self):
        return desktop()

    @property
    def documents(self):
        return documents()

    @property
    def downloads(self):
        return downloads()

    @property
    def folder(self):
        return self._folder

    @folder.setter
    def folder(self, value):
        try:
            if ',' in value:
                if not value.endswith('/'):
                    value+='/'
            else:
                if not value.endswith(os.sep):
                    value += os.sep
            self._file_table.update(value)
            self._folder=value
        except Exception as e:
            runtime_log(f'Unable to set _fs.folder:{e}',loglevel=3)

    @property
    def files(self):
        return self._file_table

    def root(self, file):
        path = os.path.abspath(file)
        result = os.path.dirname(path)
        while os.path.isdir(result):
            if result == os.path.dirname(result):
                break
            result = os.path.dirname(result)
        return result

    def filled_out_filename(self, name, default_ext=''):
        #print(f'FILLEDOUTFILELNAME:{name}')
        if not name.endswith(default_ext):
            name = name + default_ext
        result=os.path.realpath(os.path.expanduser(name))
        #print(f'BECOMES:{result}')
        return result

    def _ok_delete_file(self, filename):
        if not os.path.exists(filename):
            self.message = 'File already non-existant'
            return True
        if os.path.isfile(filename):
            try:
                os.remove(filename)
                self.message = 'Ok'
                return True
            except Exception as e:
                self.message = f'{e}'
                return False
        if os.path.isdir(filename):
            try:
                os.rmdir(filename)
                self.message = 'Ok'
                return True
            except Exception as e:
                self.message = f'{e}'
                return False
        self.message = 'Unknown problem trying to delete file'
        return False

    def path(self,fn):
        return os.path.dirname(self.filled_out_filename(fn))+os.sep

    def name(self,fn):
        return os.path.basename(os.path.splitext(fn)[0])

    def ext(self,fn):
        return os.path.splitext(fn)[1]

    def image(self,spec):
        #print(f'_fs.image({spec})')
        if os.path.isfile(spec):
            image=get_image(spec)
            if isinstance(image,str):
                self.message=('Failed to read image from file')
                return None
        else:
            image=get_image(base64_data=spec)
            if isinstance(image,str):
                self.message=('Failed to read image from base64 string')
                return None
        #print(f'_fs.image({spec}),{image}')
        self.message='Ok'
        return image

    def json(self, thing):
        try:
            return toJSON(thing)
        except:
            return None

    def _ok_save_to_file(self, thing, filename):
        thing_text=f'{thing}'[:24]
        self._mach.log(f'saving {thing_text} of type {type(thing)} to {filename}',level=1)
        ext = filename.split('.')[-1].upper()
        if ext == filename:
            ext = ''
        if isinstance(thing, str):
            try:
                with open(filename, "w", encoding=self.encoding) as f:
                    f.write(thing)
                self.message = 'Ok'
                return True
            except Exception as e:
                self.message = f'Failed to save {filename}:{e}'
                return False
        if isinstance(thing, (list,tuple)):
            if all(isinstance(el, int) for el in thing):
                if ext.upper() == '.HEX':
                    self.message = 'hex output not ready'  # todo
                    return False
            if all(isinstance(el,str) for el in thing):
                try:
                    with open(filename, "w", encoding=self.encoding) as f:
                        for line in thing:
                            f.write(f'{line}\n')
                    self.message = 'Ok'
                    return True
                except Exception as e:
                    self.message = f'Failed to save {filename}:{e}'
                    return False
        if isinstance(thing, (bytes, bytearray)):
            if ext.upper() == '.HEX':
                self.message = 'hex output not ready'  # todo
                return False
            elif ext.upper() == '.BASE64':
                try:
                    with open(filename,'w') as f:
                        if isinstance(thing,bytes):
                            thing=bytearray(thing)
                        f.write(base64.b64encode(thing))
                        self.message = 'Ok'
                        return True
                except:
                    self.message=f'Failed to save {filename}'
                    return False
            try:
                with open(filename, "w+b") as f:
                    f.write(thing)
                    self.message = 'Ok'
                    return True
            except Exception as e:
                self.message = f'Failed to save {filename}:{e}'
                return False
        try:
            if thing.image is not None:
                thing = thing.image
        except:
            pass
        self._mach.log('Type of Save thing is', type(thing),level=1)
        if isinstance(thing, BUBBLImage):
            if thing.ok_save_to_file(filename):
                self.message = 'Ok'
                return True
            else:
                self.message = thing.error_message
                return False

        if isinstance(thing, PageVars):
            thing = thing.current

        if isinstance(thing, BubblPage):
            """canvas,
            filename,
            scale = 1,
            landscape = False,
            monochrome = False,
            left_margin = 0,
            top_margin = 0,
            paper_size = None
"""
            self.message = save_canvas_message(
                thing.canvas,filename,
                left_margin=thing.left_margin,
                top_margin=thing.top_margin
                )
            if self.message == 'Ok':
                return True
            self.message(f'Failed to save page:{self.message}')
            return False
        if isinstance(thing, tkinter.Canvas):
            self.message=save_canvas_message(
                thing,
                filename
            )
            if self.message == 'Ok':
                return True
            self.message(f'Failed to save canvas:{self.message}')
            return False
        if isinstance(thing, RawTable):
            if ext in ('.HTM', 'HTML'):
                try:
                    with open(filename, "w", encoding=self.encoding) as f:
                        f.write(thing.to_html())
                        f.write('\n')
                    self.message = 'Ok'
                    return True
                except Exception as e:
                    self.message = f'Failed to save table to {filename}:{e}'
                    return False
            if ext == '.CSV':
                try:
                    with open(filename, "w", encoding=self.encoding) as f:
                        lines = thing.to_csv()
                        for line in lines:
                            f.write(line)
                            f.write('\n')
                    self.message = 'Ok'
                    return True
                except Exception as e:
                    self.message = f'Failed to save table to {filename}:{e}'
                    return False
            self._mach.log('sysvars._ok_save_to_file is saving a raw table')

        if jsonable(thing):  # , debug=True):
            text = toJSON(thing)
            try:
                with open(filename, 'w', encoding=self.encoding) as f:
                    f.write(text)
                self.message = 'Ok'
                return True
            except Exception as e:
                self.message = f'Failed to save JSON to {filename}:{e}'
                return False

        self.message = f'Cannot save {thing} to {filename}'
        return False

    def _ok_append_to_file(self, thing, filename):
        ext = filename.split('.')[-1].upper()
        if ext == filename:
            ext = ''

        if isinstance(thing, str):
            try:
                with open(filename, "a", encoding=self.encoding) as f:
                    f.write(thing)
                self.message = 'Ok'
                return True
            except Exception as e:
                self.message = f'Failed to append to {filename}:{e}'
                return False
        if (isinstance(thing, (list,tuple))
            and all(isinstance(el, str) for el in thing)):
            try:
                with open(filename, "a", encoding=self.encoding) as f:
                    for line in thing:
                        f.write(line)
                        f.write('\n')
                self.message = 'Ok'
                return True
            except Exception as e:
                self.message = f'Failed to append to {filename}:{e}'
                return False
        if isinstance(thing, Table):
            if ext in ('.HTM', 'HTML'):
                try:
                    with open(filename, "a", encoding=self.encoding) as f:
                        f.write(thing.to_html())
                        f.write('\n')
                    self.message = 'Ok'
                    return True
                except Exception as e:
                    self.message = f'Failed to append table to {filename}:{e}'
                    return False
            if ext == '.CSV':
                try:
                    with open(filename, "a", encoding=self.encoding) as f:
                        lines = thing.to_csv()
                        for line in lines:
                            f.write(line)
                            f.write('\n')
                        self.message = 'Ok'
                    return True
                except Exception as e:
                    self.message = f'Failed to append table to {filename}:{e}'
                    return False
        if jsonable(thing):
            text = toJSON(thing)
            try:
                with open(filename, 'a', encoding=self.encoding) as f:
                    f.write(',')
                    f.write(text)
                self.message = 'Ok'
                return True
            except Exception as e:
                self.message = f'Failed to append JSON to {filename}:{e}'
                return False

        self.message = f'Cannot append {thing} to {filename}'
        return False

    def _ok_copy_file(self, src, dest):
        if dest.startswith('ZIP:'):
            dest = dest[4:]
            if dest.startswith('DEFLATE:'):
                kwargs = {'compress_type': zipfile.ZIP_DEFLATED}
                dest = dest[7:]
            else:
                kwargs = {}
            if self.exists(dest):
                mode = 'a'
            else:
                mode = 'w'
            try:
                zf = zipfile.ZipFile(dest, mode)
                if os.path.isdir(src):
                    for dirname, subdirs, files in os.walk(src):
                        zf.write(dirname, arcname=dirname[
                                                  len(src):])  # todo here write relative path only, -last directory of src path only
                        fn = os.path.join(dirname, filename)
                        for filename in files:
                            zf.write(fn, arcname=fn[len(src):], **kwargs)
                else:
                    zf.write(
                        src)  # todo here write relative path only, -last directory of src path only
                zf.close()
                self.message = 'Ok'
                return True
            except Exception as e:
                self.message = f'{e}'
                return False
        try:
            shutil.copy(src, dest)
            self.message = 'Ok'
            return True
        except Exception as e:
            self.message = f'{e}'
            return False

    def _ok_rename_file(self, src, dest):
        try:  # todo here, make sure dest is same directory as source
            os.rename(src, dest)
            self.message = 'Ok'
            return True
        except Exception as e:
            self.message = f'{e}'
            return False

class Env:
    def __getitem__(self, item):
        try:
            return os.environ[item]
        except:
            return ''

    def __setitem__(self, key, value):
        try:
            os.putenv(key, value)
        except:
            pass


class OSVars(SysVars):
    """
_os System Variable
==================
This variable allows access to various operating system facilities
It has the following properties, referenced with: '_os.&lt;property&gt;'

Property    Type     Description
--------    ----     -----------
name        r/o      Name of the operating system (e.g. Linux or Windows)
version     r/o      Version string
env         r/o      Mapping of environment variables (e.g. _os.env['PATH'])
                     Environment variables may be written as well as read
timer       r/w      Writing a tuple (duration,tag) to this property creates a
                     'Timer' event, with Id=tag, duration seconds later.
processes   r/o      A table of processes created with 'Execute OS Command' instruction
                     Its fields are:
                        Command  -Command line which started the process
                        Id       -Process ID from o/s
                        Ended    -True if the process has finished, False otherwise
                        Exitcode -Exit code of the process when it finished
                        Out      -Standard output stream of the process.
                                  Either a filename where output is redirected,
                                  or 'PIPE' indicating stdout output from the
                                  process creates 'StdOut' events.
                        Err      -Standard error stream of the process
                                  Either a filename where errors are redirected
                                  or'PIPE' indicating stderr output from the
                                  process creates 'StdErr' events.
                        In       -Standard input stream of the process. Assigning
                                  a string to this sends the string plus new-line
                                  to the input stream of the process.

message     r/o      Result of last 'Execute OS Command' instruction
time        r/o      Current local time in 'Seconds since 00:00hrs 1.1.1970 CE'
utc         r/o      Current UTC time in  'Seconds since 00:00hrs 1.1.1970 CE'
datim(time) function Gives a datetime object with the following fields:
                        year, month, day, hour, second

children    mapping  (TBI) Writing _os.children[name]=(filename,diag,node) creates a mapping
                     to a BUBBL app loaded from filename, and run from diag,node.
                     Deleting (using _os.children.pop(name)) closes and destroys the app.
                     While running, the app can communicate with the main app via
                     message events.
"""

    def __init__(self, mach):
        self._mach = mach
        self.env = Env()
        self._last_timer = ''
        self._process_table = ProcessTable()
        self.message='Ok'
        for name in ('timer',):
            valid_sys_var_names.add(f'_os.{name}')

    @property
    def name(self):
        return platform.system().lower()

    @property
    def version(self):
        return platform.version()

    @property
    def timer(self):
        return self._last_timer

    @timer.setter
    def timer(self, pars):
        try:
            duration = float(pars[0])
            name = pars[1]
        except:
            try:
                duration = float(pars)
                name = ''
            except:
                return
        self._last_timer = name
        threading.Timer(duration, self._timer_action, [name]).start()

    def _timer_action(self, tag):
        self._mach.queue_event(TimerEvent(tag))

    @property
    def processes(self):
        return self._process_table

    def _ok_create_async_process(self, command, mach,delete_on_exit=False):
        if delete_on_exit:
            kwargs={'process_table':self._process_table,
                    'event_name':'ClipEnd'}
        else:
            kwargs={}
        try:
            p = ProcessManager(command, mach,**kwargs)
            self._process_table.add_process(p)
            return True
        except Exception as e:
            self.message = f'Unable to run command:{e}'
            return False

    def _created_sync_process(self, command, mach,exited):
        try:
            self.message = 'Ok'
            p = SynchProcess(command, mach, exited)
            return p
        except Exception as e:
            self.message = f'Failed to run process:{e}'
            return None

    def _close_down(self):
        for p in self._process_table:
            p._pm.process.kill()

    @property
    def utc(self):
        return int(time.time())
    @property
    def time(self):
        t=int(time.time())
        lt=time.localtime(t)
        if not lt.tm_isdst:
            return int(t)
        return int(t+lt.tm_gmtoff)

    def datim(self,time=None):
        if time is None:
            time=self.time
        return datetime.datetime.fromtimestamp(time)




class NWClientManager:
    def __init__(self, TCP_client, mach):
        self.connection = TCP_client
        self.connection.register_receiver(self.rx)
        self.mach = mach

    def __str__(self):
        return (f'TPC Connection address={self.address}' + \
                f' port={self.port} host={self.host}')

    @property
    def address(self):
        return self.connection.address

    @property
    def port(self):
        return self.connection.port

    @property
    def host(self):
        return self.connection.host

    @property
    def send(self):
        return None

    @send.setter
    def send(self, message):
        if not message:
            self.connection._close()
        else:
            self.connection.send(message)

    def rx(self, message):
        self._mach.log('NWClientManager.rx', message)
        if not message:
            self.connection._close()
            return
        self.mach.queue_event(RxEvent(True,
                                      self.host,
                                      self.address,
                                      self.port,
                                      message))


class NetworkVars(SysVars):
    """
_nw system variable
===================
The following functions/attributes
_nw.host        ID of local host
_nw.IPv4(url)   Gives the IPv4 address of the url as '&lt;url&gt;/&lt;IPv4 Address&gt;
_nw.TCPPort     Gives an unused TCP port number
_nw.UDPPort     Gives an unused UDP port number

_nw.TCPServer(address,port)  returns a TCP server on the port.
    address is an IPV4 address or 'localhost' or '' for all available
    addresses.
    The server can be closed by setting the attribute 'closed' to True

    Connection requests generate Rq events which has the following field:
        conn A TCPConnection object with the following fields:
            conn.send     Write a string to this field to send a message
                          Write an empty string or None to close the connection
            conn.address  IPV4 Address of the remote connection
            conn.port     The port number used for communication
    E.g. to refuse the connection (by closing it immediately) use
        _ev.conn.send=None

    if the event is discarded (i.e. not waited for in the next 'wait'
    instruction) it is automatically closed

_nw.TCPConnect(address,port) Attempts to connect to TCP server at address on port.
    If successful, returns a TCPConnection object with the following fields:
        conn.send       Write a string to this field to send a message.
                        Write an empty string or None to close the connection.
                        To ensure transmission and reception, strings must be terminated
                        with '\\n'.
        conn.address    IPV4 Address of the remote connection
        conn.port       The port number used for communication

    The TCPConn object generates 'Rx' events with the fields:
        _ev.text  The received (string) message with '\\n' removed
        _ev.address The IPV4 address of the remote server
        _ev.host The IPV4 address of this computer
        _ev.port The port over which the message was sent

    Incoming messages must be terminated with a new-line character.

_nw.UDPServer(address,port [,binary=False])
    Returns a UDP server which binds to the first connection it receives.
    'address' is an IPV4 address or 'localhost' or '' for all available
    addresses.
    Writing data to server.send sends a datagram containing the data to the
    bound connection.
    If 'binary' is set to True, the data should be a 'bytes' object, otherwise
    it should be a string.
    Data received generates 'Rx' events containing the data and port number.
    The data size is restricted to 1024 bytes in length.

_nw.UDPConnect(address,port[,binary=False)
    Returns a UDP client connection to the address and port, or None if it
    fails.  Writing to client.send transmits a datagram to the server.
    Received datagrams generate 'Rx' events with address, port and data.
    If the parameter 'binary' is set to true data sent/received should be
    'bytes' objects otherwise it should be strings.
"""

    def __init__(self, mach):
        self.mach = mach
        self.servers = []

    def help_text(self):
        return self.__doc__

    @property
    def TCPPort(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('localhost', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    @property
    def UDPPort(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
            s.bind(('localhost', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    def TCPConnect(self, address, port):
        try:
            connection = TCPClient(address, port)
            return NWClientManager(connection, self.mach)
        except Exception as e:
            self._mach.log('Failed to get connection',level=Logger.INFO)
            return None

    def _put(self, connection):
        self.mach.queue_event(RqEvent(NWClientManager(connection, self.mach)))

    def TCPServer(self, address, port):
        try:
            server = network.TCPServer(address, port, self)
        except Exception as e:
            self._mach.log('Failed to create server', e,level=Logger.INFO)
            return None
        self.servers.append(server)
        return server

    def UDPServer(self, address, port, binary=False):
        def message_handler(message, address=address, port=port):
            #self._mach.log('UDPServer on ', address, port, ' got message:', message)
            self.mach.queue_event(
                RxEvent(False, '_server', address, port, message))
            #self._mach.log('Rx Event has been queued')

        try:
            server = network.UDPServer(address, port, message_handler,
                                       binary=binary)
        except Exception as e:
            self._mach.log('Failed to create server', e,level=Logger.INFO)
            return None
        self.servers.append(server)
        return server

    def UDPConnect(self, address, port, binary=False):
        def message_handler(message):
            self.mach.queue_event(
                RxEvent(False, '_client', address, port, message))

        try:
            client = network.UDPClient(address, port, message_handler,
                                       binary=binary)
        except Exception as e:
            self._mach.log('Failed to create UDP client', e,level=Logger.INFO)
            client = None

        return client

    def _delete(self, server):
        try:
            self.servers.remove(server)
        except ValueError:
            pass

    def _close_down(self):
        for server in list(self.servers):
            server.closed = True


"""
  def __init__(self):
        self.SHIFT=False
        self.CTRL=False
        self.ALT=False
        self.META=False
        self.MX=0
        self.MY=0
        self.MW=0
        self.KEY=0
        self.TYPED=0
        self.UI=0
        self._ev=''
        self.CX=0
        self.CY=0
        self.PW=640
        self.PH=480
        self.PT=''
        self.TH=18
        self.BW=2
        self.PX=0
        self.PY=0
        self.DH=480
        self.DW=640
        self.SW=1920
        self.SH=1080

        self.INK=0
        self.PAPER=0xD0F0F0
        self.BOLD=False
        self.ITALIC=False
        self.SIZE=10
        self.FONT='Lato'
        self.PAGE='main'
        self.CURSOR='ARROW'
        self.ENCODING='UTF-8'
        self.FOCUS=''
        self.PROG_FILE=''
        self.RECORD=0
        self.USER_HOME=''
        self.USER_NAME=''
        self.USER_DESKTOP=''
        self.WORKING=''
        self.DRAG_START=''
        self.DRAG_PAGE=''
        self.DROP_OK=''
        self.MOUSE_OVER=[]
        self.MOUSE_RADIUS=5
        self.SEPARATOR='/'
        self.FILE_MESSAGE='Ok'
        self.PI=3.141592653589793
"""

'''
'DIALOGUE':sysvar(),
'DIST_FROM_MAX':sysvar(lambda self,mach:mach.levDistMax,levDistWriter),
'DROP_OK':sysvar(),
'DRP':sysvar(),
'DSP':sysvar(),
'DUMP':sysvar(),
'DW':sysvar(lambda self,mach:mach.page.page.pageMap['Desktop'].params.PW),
'ENCODING':sysvar(),
'_ev':sysvar(lambda self,mach:mach.getNextEvent,writeEVENT),
'EVENT_MESSAGE':sysvar(lambda self,mach:mach.messPars,emptyWrite),
'EVENTS':sysvar(),
'EXTRN_DB':sysvar(),
'FALSE':sysvar(),
'FILE_MESSAGE':sysvar(),
'FILE_PATH':sysvar(),
'FOCUS':sysvar(),
'FONT':sysvar(),
'FREE_MEM':sysvar(),
'HOST':sysvar(),
'HOUR':sysvar(lambda self,mach:86400,emptyWrite),
'HTML_ENTITIES':sysvar(lambda self,mach:htmlEntities,emptyWrite),
'IMAGE':sysvar(),
'INET':sysvar(),
'INFO_FILE':sysvar(),
'INFO_KEY':sysvar(),
'INK':sysvar(lambda self,mach:mach.page.params.ink),
'ITALIC':sysvar(),
'JAR_FILES':sysvar(),
'JAR_PATH':sysvar(),
'KEY':sysvar(),
'LANDSCAPE':sysvar(),
'LEFT_MARGIN':sysvar(),
'MEM_POOL':sysvar(),
'MIME':sysvar(),
'MOUSE_OVER':sysvar(lambda self,mach:mach.page.mouse_over(mach.MX,mach.MY)),
'MOUSE_OVERLAY':sysvar(),
'MOUSE_RADIUS':sysvar(),
'MP':sysvar(lambda self,mach:mach.MP,emptyWrite),
'MW':sysvar(lambda self,mach:mach.MW,emptyWrite),
'MX':sysvar(lambda self,mach:mach.MX,emptyWrite),
'MY':sysvar(lambda self,mach:mach.MY,emptyWrite),
'NXT':sysvar(),
'OWN_PORT':sysvar(),
'PAPER':sysvar(lambda self,mach:mach.page.params.paper),
'PAPER_HEIGHT':sysvar(),
'PAPER_WIDTH':sysvar(),
'PH':sysvar(lambda self,mach:mach.page.params.PH,emptyWrite),
'PI':sysvar(lambda self,mach:3.14159265358979323846,emptyWrite),
'PIN':sysvar(),
'PIN_CTL':sysvar(),
'PORT':sysvar(),
'PROCESS':sysvar(),
'PROG_FILE':sysvar(),
'PW':sysvar(lambda self,mach:mach.page.params.PW,emptyWrite),
'PV':sysvar(),
'PT':sysvar(),
'PX':sysvar(lambda self,mach:mach.page.params.x,emptyWrite),
'PY':sysvar(lambda self,mach:mach.page.params.y,emptyWrite),
'RECORD':sysvar(),
'REMOTE_PROG':sysvar(),
'REMOTE_TABLE':sysvar(),
'RIGHT_MARGIN':sysvar(),
'RTMS':sysvar(),
'SEED':sysvar(lambda self,mach:mach.cypher.seed,encryptorWriter),
'SELF':sysvar(),
'SEPARATOR':sysvar(lambda self,mach:os.sep,emptyWrite),
'SH':sysvar(),
'SHIFT':sysvar(lambda self,mach:mach.SHIFT,emptyWrite),
'SIZE':sysvar(lambda self,mach:mach.page.params.fnt.size),
'STDERR':sysvar(),
'STDOUT':sysvar(),
'SW':sysvar(),
'SYSTEM':sysvar(),
'SYSV_NAMES':sysvar(),
'SYS_TABLE':sysvar(),
'TIME':sysvar(lambda self,mach:int(time.time())-946684800,emptyWrite),
'TOP_MARGIN':sysvar(),
'TRUE':sysvar(),
'TYPED':sysvar(),
'UI':sysvar(lambda self,mach:mach.UI),
'UNDO_DUMP_FILE':sysvar(),
'USED_MEM':sysvar(),
'USER_HOME':sysvar(),
'USER_NAME':sysvar(),
'USR_TABLE':sysvar(),
'UTC':sysvar(lambda self,mach:round(time.mktime(time.gmtime()))-946684800,emptyWrite),
'VERSION':sysvar(),
'WINDOW':sysvar(lambda self,mach:mach.page.mode,emptyWrite),
'WORKING':sysvar()}

#log(htmlEntities)
#log(html.entities.html5['acirc']) '''