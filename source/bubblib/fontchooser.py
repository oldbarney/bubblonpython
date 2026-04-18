"""tkinter fontchooser wrapper
There is a fudge to fix a bug in the Linux implementation
which returns the wrong font size from the chosen font
(there appears to be a multiply where there should be a
divide somewhere in the tcl code.
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
#This code has been copied from https://bugs.python.org/file49459/fontchooser.py
from tkinter import Frame

from tkinter.commondialog import Dialog
from tkinter.font import Font

from bubblib import utils


class Chooser(Dialog):

    def __init__(self, *args, **kw):
        # We use commondialog simply for the master handling logic
        super().__init__(*args, **kw)
        self.w = Frame(self.master).winfo_toplevel()


    def hide(self):
        """Hide the font selection dialog if visible."""
        self.w.tk.call("tk", "fontchooser", "hide")

    def show(self, **options):
        """Show and wait for the font selection dialog."""
        # update instance options
        for k, v in options.items():
            self.options[k] = v

        self.w = w = Frame(self.master).winfo_toplevel()
        self.options["parent"] = w
        if self.options.get("command"):
            self.options["command"] = self._wrapper(self.options["command"])
        w.bind("<<TkFontchooserVisibility>>", self._vischange)
        w.tk.call(("tk", "fontchooser", "configure", *w._options(self.options)))
        w.tk.call(("tk", "fontchooser", "show"))
        # "Depending on the platform, may return immediately or only once the dialog has been withdrawn."
        # https://www.tcl.tk/man/tcl/TkCmd/fontchooser.htm
        # Therefore, we need to vwait to ensure we do not return early
        print("vwait")
        w.tk.call(("vwait", "fontdone"))

    def configure(self, **options):
        """Set the values of one or more options."""
        for k in options:
            self[k] = options[k]

    config = configure

    def _vischange(self, event):
        if not self.w.tk.call(("tk", "fontchooser", "configure", "-visible")):
            self.w.tk.call(("set", "fontdone", "done"))

    def _wrapper(self, command):
        def wrap(font):
            actual = self.w.tk.call(("font", "actual", font))
            font = Font(**{i[1:]: j for i, j in zip(actual[::2], actual[1::2])})
            command(font)

        return wrap

    def __setitem__(self, key, value):
        self.w.tk.call("tk", "fontchooser", "configure", "-" + key, value)

    def __getitem__(self, key):
        return self.w.tk.call("tk", "fontchooser", "configure", "-" + key)


def askfont(**options):
    "Ask for a font"

    def setrtn(font):
        nonlocal rtnval
        rtnval = font

    rtnval = None
    options = options.copy()
    options["command"] = setrtn
    chooser = Chooser(**options)
    chooser.show()
    return rtnval


def get_actual_linux_size(family,apparent_size):
    #approx=round(apparent_size/1.4)
    print('apparent_size',apparent_size)
    for approx in range(apparent_size//3,apparent_size):
        start = Font(family=family, size=approx)
        print('approx', approx, start.actual('size'))
        if start.actual('size')==apparent_size:
            return approx

        #error=(apparent_size-start.actual('size'))
        #if round(error)==0:
        #    return approx
        #approx+=error
    return approx

def get_font(default=None):
    result=askfont()
    if result is not None:
        a=result.actual()
        family=f"{a['family']}"
        size=a['size']
        if not utils.windows:
            size=get_actual_linux_size(family,get_actual_linux_size(family,size))
        font=f"{family},{size}"
        if a['slant']=='italic':
            font+=',i'
        if a['weight']=='bold':
            font+=',b'
        return font
    return default


if __name__ == "__main__":
    askfont()