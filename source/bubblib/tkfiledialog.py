"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import os
from tkinter import filedialog

from bubblib.utils import home, log

default_history=[]

class TkFileDialog:
    def __init__(self, default, callback,
                 saveas=False,
                 directory=False,
                 multiple=False,
                 title=None,
                 history=default_history,
                 show_hidden=False,
                 icon_view=False,
                 filter='All files:*',
                 widths=[200, 50, 80, 150]):

        self._callback=callback
        filetypes=[]
        for item in filter.split(','):
            parts=item.split(':')
            if len(parts)==1:
                filetypes.append((parts[0],parts[0]))
            elif len(parts)==2:
                filetypes.append(parts)
            else:
                filetypes.append((parts[0],parts[1:]))
        if isinstance(default,str):
            initialdir=os.path.dirname(os.path.abspath(default))
            initialfile=default
        else:
            initialdir=home()
            initialfile=''

        if saveas:
            if title is None:
                title='Save as'
            filename=filedialog.asksaveasfilename(
                initialdir=initialdir,
                initialfile=initialfile,
                confirmoverwrite=False,
                title=title,
                filetypes=filetypes)
            if not filename:
                self._callback(None)
            self._callback(filename)
        else:
            if directory:
                if title is None:
                    title='Folder'
                result=filedialog.askdirectory(initialdir=initialdir,
                                               mustexist=True,
                                               title=title)
                if not result:
                    self._callback(None)
                    return
                if result!='/' and not result.endswith(os.sep):
                    result+=os.sep
                self._callback(result)
            else:
                if multiple:
                    if title is None:
                        title='File selection'
                    result=filedialog.askopenfilenames(
                        initialdir=initialdir,
                        filetypes=filetypes,
                        title=title)
                    if not result:
                        self._callback(None)
                        return
                    folder=os.path.dirname(os.path.abspath(result[0]))
                    if not folder.endswith(os.sep):
                        folder+=os.sep
                    result=[folder]+[os.path.abspath(fn)[len(folder):] for
                                         fn in result]
                    self._callback(result)
                else:
                    if title is None:
                        title='Open'
                    filename = filedialog.askopenfilename(initialdir=initialdir,
                                                          initialfile=default,
                                                          filetypes=filetypes,
                                                          title=title)
                    if not filename:
                        self._callback(None)
                        return
                    self._callback(filename)
    def close(self):
        log('Dont know how to close tkinter file_dialog')
