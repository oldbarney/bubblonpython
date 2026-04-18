"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"

import zipfile

from PIL import Image, ImageTk

import os
import sys
icon_path=os.path.dirname(os.path.abspath(__file__))+os.sep
#icon_path='bubblib.zip/' #'__file__+os.sep
#print('icon_path =',icon_path)

icons={
    'licences':'icons/info.png',
    'info':'icons/info.png',
    'open':'icons/logic.png',
    'ok':'icons/ok.png',
    'save':'icons/save.png',
    'saveas':'icons/saveas.png',
    'exit':'icons/close.png',
    'new':'icons/bubblIcon.png',
    'assign':'icons/let.png',
    'if':'icons/if.png',
    'wait':'icons/wait.png',
    'switch':'icons/switch.png',
    'output':'icons/output.png',
    'for':'icons/for.png',
    'link':'icons/end.png',
    'library':'icons/library.png',
    'watch':'icons/watch.png',
    'table':'icons/tables.png',
    'files':'icons/files.png',
    'user':'icons/user.png',
    'widget':'icons/dialog.png',
    'python':'icons/python.png',
    'up':'icons/up.png',
    'down':'icons/down.png',
    'ins':'icons/add.png',
    'del':'icons/close.png',
    'page':'icons/page.png',
    'clr_page':'icons/rectangle.png',
    'page_upd':'icons/page_upd.png',
    'copy':'icons/copy.png',
    'cut':'icons/cut.png',
    'paste':'icons/paste.png',
    'delete':'icons/delete.png',
    'block':'icons/instr.png',
    'undo':'icons/undo.png',
    'formula':'icons/formula.png',
    'create':'icons/create.png',
    'io':'icons/backfwd.png',
    'start':'icons/start.png',
    'edit':'icons/edit.png',
    'loop':'icons/loop.png',
    'for':'icons/for.png',
    'image':'icons/pic.png',
    'polygon':'icons/polygon.png',
    'keyboard':'icons/keyboard.png',
    'view':'icons/watch.png',
    'font':'icons/font.png',
    'file':'icons/files.png',
    'linestyle':'icons/line.png',
    'colour':'icons/colour.png',
    'insert':'icons/insert.png',
    'tabledelete':'icons/tabledelete.png',
    'tableupdate':'icons/tableupdate.png',
    'tableselect':'icons/select.png',
    'choice':'icons/choice.png',
    'askuser':'icons/askuser.png',
    'menu':'icons/menu.png',
    'alert':'icons/alert.png',
    'sound':'icons/clip.png',
    'filechooser':'icons/files.png',
    'rectangle':'icons/rectangle.png',
    'ellipse':'icons/circle.png',
    'arc':'icons/sector.png',
    'edit':'icons/edit.png',
    'dialog':'icons/dialog.png',
    'sort':'icons/sort.png',
    'page_refresh':'icons/page_upd.png',
    'line':'icons/line.png',
    'sector':'icons/sector.png',
    'button':'icons/button.png',
    'print':'icons/print.png',
    'scrollbar':'icons/hscroller.png',
    'fileappend':'icons/append.png',
    'fileexec':'icons/launcher.png',
    'filerename':'icons/filerename.png',
    'filemkdir':'icons/filemkdir.png',
    'filedelete':'icons/filedelete.png',
    'filecopy':'icons/filecopy.png',
    'playsound':'icons/clip.png',
    'saveimage':'icons/saveimage.png',
    'savetable':'icons/savetable.png',
    'playvideo':'icons/playvideo.png',
    'outputat':'icons/at.png',
    'var':'icons/var.png',
    'vars':'icons/vars.png',
    'blank':'icons/blank.png',
    'blankpage':'icons/blankpage.png',
    'minimise':'icons/minimise.png',
    'tableview':'icons/tableview.png',
    'radio':'icons/radio.png',
    'cascade':'icons/cascade.png',
    'www':'icons/www.png',
    'folder':'icons/folder.png',
    'svars':'icons/svars.png',
    'find':'icons/find.png',
    'pencil':'icons/pencil.png',
    'toolkit':'icons/toolkit.png',
    'settings':'icons/settings.png',
    'bubbl':'icons/bubblIcon.png',
    'logs':'icons/logs.png',
    'popupmenu':'icons/popupmenu.png',
    'gold':'icons/gold.png',
    'silver':'icons/silver.png',
    'hole':'icons/hole.png',
    'hole2': 'icons/hole2.png',
    'hole3': 'icons/hole3.png',
    'question':'icons/question.png',
    'archive':'icons/archive.png'

}

if 'bubblib.icons.zip' in sys.path:
    icon_zip_file=zipfile.ZipFile('bubblib/icons.zip','r')
else:
    icon_zip_file=None

def icon(key,icon_size=20,pil_images=None):
    if pil_images is not None:
        return ImageTk.PhotoImage(image=pil_images[key],size=f'{icon_size}x{icon_size}')
    if icon_zip_file is None:
        image=Image.open(icon_path+icons[key])
    else:
        image=Image.open(icon_zip_file.open(icons[key]))
    image=image.resize((icon_size,icon_size))
    result=ImageTk.PhotoImage(image=image,size=f'{icon_size}x{icon_size}')
    return result
