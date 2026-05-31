"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
#from idlelib.config import idleConf
import string
from tkinter import TclError
import builtins
import keyword
import re
import time

from bubblib.utils import print_


class Delegator:

    def __init__(self, delegate=None):
        self.delegate = delegate
        self.__cache = set()
        # Cache is used to only remove added attributes
        # when changing the delegate.

    def __getattr__(self, name):
        attr = getattr(self.delegate, name) # May raise AttributeError
        setattr(self, name, attr)
        self.__cache.add(name)
        return attr

    def resetcache(self):
        "Removes added attributes while leaving original attributes."
        # Function is really about resetting delegator dict
        # to original state.  Cache is just a means
        for key in self.__cache:
            try:
                delattr(self, key)
            except AttributeError:
                pass
        self.__cache.clear()

    def setdelegate(self, delegate):
        "Reset attributes and change delegate."
        self.resetcache()
        self.delegate = delegate

class UndoDelegator(Delegator):

    max_undo = 1000

    def __init__(self):
        Delegator.__init__(self)
        self.reset_undo()

    def setdelegate(self, delegate):
        if self.delegate is not None:
            self.unbind("<<undo>>")
            self.unbind("<<redo>>")
            self.unbind("<<dump-undo-state>>")
        Delegator.setdelegate(self, delegate)
        if delegate is not None:
            self.bind("<<undo>>", self.undo_event)
            self.bind("<<redo>>", self.redo_event)
            self.bind("<<dump-undo-state>>", self.dump_event)

    def dump_event(self, event):
        from pprint import pprint
        pprint(self.undolist[:self.pointer])
        print("pointer:", self.pointer, end=' ')
        print("saved:", self.saved, end=' ')
        print("can_merge:", self.can_merge, end=' ')
        print("get_saved():", self.get_saved())
        pprint(self.undolist[self.pointer:])
        return "break"

    def reset_undo(self):
        self.was_saved = -1
        self.pointer = 0
        self.undolist = []
        self.undoblock = 0  # or a CommandSequence instance
        self.set_saved(1)

    def set_saved(self, flag):
        if flag:
            self.saved = self.pointer
        else:
            self.saved = -1
        self.can_merge = False
        self.check_saved()

    def get_saved(self):
        return self.saved == self.pointer

    saved_change_hook = None

    def set_saved_change_hook(self, hook):
        self.saved_change_hook = hook

    was_saved = -1

    def check_saved(self):
        is_saved = self.get_saved()
        if is_saved != self.was_saved:
            self.was_saved = is_saved
            if self.saved_change_hook:
                self.saved_change_hook()

    def insert(self, index, chars, tags=None):
        self.addcmd(InsertCommand(index, chars, tags))

    def delete(self, index1, index2=None):
        self.addcmd(DeleteCommand(index1, index2))

    # Clients should call undo_block_start() and undo_block_stop()
    # around a sequence of editing cmds to be treated as a unit by
    # undo & redo.  Nested matching calls are OK, and the inner calls
    # then act like nops.  OK too if no editing cmds, or only one
    # editing cmd, is issued in between:  if no cmds, the whole
    # sequence has no effect; and if only one cmd, that cmd is entered
    # directly into the undo list, as if undo_block_xxx hadn't been
    # called.  The intent of all that is to make this scheme easy
    # to use:  all the client has to worry about is making sure each
    # _start() call is matched by a _stop() call.

    def undo_block_start(self):
        if self.undoblock == 0:
            self.undoblock = CommandSequence()
        self.undoblock.bump_depth()

    def undo_block_stop(self):
        if self.undoblock.bump_depth(-1) == 0:
            cmd = self.undoblock
            self.undoblock = 0
            if len(cmd) > 0:
                if len(cmd) == 1:
                    # no need to wrap a single cmd
                    cmd = cmd.getcmd(0)
                # this blk of cmds, or single cmd, has already
                # been done, so don't execute it again
                self.addcmd(cmd, 0)

    def addcmd(self, cmd, execute=True):
        if execute:
            cmd.do(self.delegate)
        if self.undoblock != 0:
            self.undoblock.append(cmd)
            return
        if self.can_merge and self.pointer > 0:
            lastcmd = self.undolist[self.pointer-1]
            if lastcmd.merge(cmd):
                return
        self.undolist[self.pointer:] = [cmd]
        if self.saved > self.pointer:
            self.saved = -1
        self.pointer = self.pointer + 1
        if len(self.undolist) > self.max_undo:
            ##print "truncating undo list"
            del self.undolist[0]
            self.pointer = self.pointer - 1
            if self.saved >= 0:
                self.saved = self.saved - 1
        self.can_merge = True
        self.check_saved()

    def undo_event(self, event):
        if self.pointer == 0:
            self.bell()
            return "break"
        cmd = self.undolist[self.pointer - 1]
        cmd.undo(self.delegate)
        self.pointer = self.pointer - 1
        self.can_merge = False
        self.check_saved()
        return "break"

    def redo_event(self, event):
        if self.pointer >= len(self.undolist):
            self.bell()
            return "break"
        cmd = self.undolist[self.pointer]
        cmd.redo(self.delegate)
        self.pointer = self.pointer + 1
        self.can_merge = False
        self.check_saved()
        return "break"


class Command:
    # Base class for Undoable commands

    tags = None

    def __init__(self, index1, index2, chars, tags=None):
        self.marks_before = {}
        self.marks_after = {}
        self.index1 = index1
        self.index2 = index2
        self.chars = chars
        if tags:
            self.tags = tags

    def __repr__(self):
        s = self.__class__.__name__
        t = (self.index1, self.index2, self.chars, self.tags)
        if self.tags is None:
            t = t[:-1]
        return s + repr(t)

    def do(self, text):
        pass

    def redo(self, text):
        pass

    def undo(self, text):
        pass

    def merge(self, cmd):
        return 0

    def save_marks(self, text):
        marks = {}
        for name in text.mark_names():
            if name != "insert" and name != "current":
                marks[name] = text.index(name)
        return marks

    def set_marks(self, text, marks):
        for name, index in marks.items():
            text.mark_set(name, index)


class InsertCommand(Command):
    # Undoable insert command

    def __init__(self, index1, chars, tags=None):
        Command.__init__(self, index1, None, chars, tags)

    def do(self, text):
        self.marks_before = self.save_marks(text)
        self.index1 = text.index(self.index1)
        if text.compare(self.index1, ">", "end-1c"):
            # Insert before the final newline
            self.index1 = text.index("end-1c")
        text.insert(self.index1, self.chars, self.tags)
        self.index2 = text.index("%s+%dc" % (self.index1, len(self.chars)))
        self.marks_after = self.save_marks(text)
        ##sys.__stderr__.write("do: %s\n" % self)

    def redo(self, text):
        text.mark_set('insert', self.index1)
        text.insert(self.index1, self.chars, self.tags)
        self.set_marks(text, self.marks_after)
        text.see('insert')
        ##sys.__stderr__.write("redo: %s\n" % self)

    def undo(self, text):
        text.mark_set('insert', self.index1)
        text.delete(self.index1, self.index2)
        self.set_marks(text, self.marks_before)
        text.see('insert')
        ##sys.__stderr__.write("undo: %s\n" % self)

    def merge(self, cmd):
        if self.__class__ is not cmd.__class__:
            return False
        if self.index2 != cmd.index1:
            return False
        if self.tags != cmd.tags:
            return False
        if len(cmd.chars) != 1:
            return False
        if self.chars and \
           self.classify(self.chars[-1]) != self.classify(cmd.chars):
            return False
        self.index2 = cmd.index2
        self.chars = self.chars + cmd.chars
        return True

    alphanumeric = string.ascii_letters + string.digits + "_"

    def classify(self, c):
        if c in self.alphanumeric:
            return "alphanumeric"
        if c == "\n":
            return "newline"
        return "punctuation"


class DeleteCommand(Command):
    # Undoable delete command

    def __init__(self, index1, index2=None):
        Command.__init__(self, index1, index2, None, None)

    def do(self, text):
        self.marks_before = self.save_marks(text)
        self.index1 = text.index(self.index1)
        if self.index2:
            self.index2 = text.index(self.index2)
        else:
            self.index2 = text.index(self.index1 + " +1c")
        if text.compare(self.index2, ">", "end-1c"):
            # Don't delete the final newline
            self.index2 = text.index("end-1c")
        self.chars = text.get(self.index1, self.index2)
        text.delete(self.index1, self.index2)
        self.marks_after = self.save_marks(text)
        ##sys.__stderr__.write("do: %s\n" % self)

    def redo(self, text):
        text.mark_set('insert', self.index1)
        text.delete(self.index1, self.index2)
        self.set_marks(text, self.marks_after)
        text.see('insert')
        ##sys.__stderr__.write("redo: %s\n" % self)

    def undo(self, text):
        text.mark_set('insert', self.index1)
        text.insert(self.index1, self.chars)
        self.set_marks(text, self.marks_before)
        text.see('insert')
        ##sys.__stderr__.write("undo: %s\n" % self)


class CommandSequence(Command):
    # Wrapper for a sequence of undoable cmds to be undone/redone
    # as a unit

    def __init__(self):
        self.cmds = []
        self.depth = 0

    def __repr__(self):
        s = self.__class__.__name__
        strs = []
        for cmd in self.cmds:
            strs.append("    %r" % (cmd,))
        return s + "(\n" + ",\n".join(strs) + "\n)"

    def __len__(self):
        return len(self.cmds)

    def append(self, cmd):
        self.cmds.append(cmd)

    def getcmd(self, i):
        return self.cmds[i]

    def redo(self, text):
        for cmd in self.cmds:
            cmd.redo(text)

    def undo(self, text):
        cmds = self.cmds[:]
        cmds.reverse()
        for cmd in cmds:
            cmd.undo(text)

    def bump_depth(self, incr=1):
        self.depth = self.depth + incr
        return self.depth


def _undo_delegator(parent):  # htest #
    from tkinter import Toplevel, Text, Button
    #from idlelib.percolator import Percolator
    undowin = Toplevel(parent)
    undowin.title("Test UndoDelegator")
    x, y = map(int, parent.geometry().split('+')[1:])
    undowin.geometry("+%d+%d" % (x, y + 175))

    text = Text(undowin, height=10)
    text.pack()
    text.focus_set()
    p = Percolator(text)
    d = UndoDelegator()
    p.insertfilter(d)

    undo = Button(undowin, text="Undo", command=lambda:d.undo_event(None))
    undo.pack(side='left')
    redo = Button(undowin, text="Redo", command=lambda:d.redo_event(None))
    redo.pack(side='left')
    dump = Button(undowin, text="Dump", command=lambda:d.dump_event(None))
    dump.pack(side='left')

class WidgetRedirector:
    """Support for redirecting arbitrary widget subcommands.

    Some Tk operations don't normally pass through tkinter.  For example, if a
    character is inserted into a Text widget by pressing a key, a default Tk
    binding to the widget's 'insert' operation is activated, and the Tk library
    processes the insert without calling back into tkinter.

    Although a binding to <Key> could be made via tkinter, what we really want
    to do is to hook the Tk 'insert' operation itself.  For one thing, we want
    a text.insert call in idle code to have the same effect as a key press.

    When a widget is instantiated, a Tcl command is created whose name is the
    same as the pathname widget._w.  This command is used to invoke the various
    widget operations, e.g. insert (for a Text widget). We are going to hook
    this command and provide a facility ('register') to intercept the widget
    operation.  We will also intercept method calls on the tkinter class
    instance that represents the tk widget.

    In IDLE, WidgetRedirector is used in Percolator to intercept Text
    commands.  The function being registered provides access to the top
    of a Percolator chain.  At the bottom of the chain is a call to the
    original Tk widget operation.
    """
    def __init__(self, widget):
        '''Initialize attributes and setup redirection.

        _operations: dict mapping operation name to new function.
        widget: the widget whose tcl command is to be intercepted.
        tk: widget.tk, a convenience attribute, probably not needed.
        orig: new name of the original tcl command.

        Since renaming to orig fails with TclError when orig already
        exists, only one WidgetDirector can exist for a given widget.
        '''
        self._operations = {}
        self.widget = widget            # widget instance
        self.tk = tk = widget.tk        # widget's root
        w = widget._w                   # widget's (full) Tk pathname
        self.orig = w + "_orig"
        # Rename the Tcl command within Tcl:
        tk.call("rename", w, self.orig)
        # Create a new Tcl command whose name is the widget's pathname, and
        # whose action is to dispatch on the operation passed to the widget:
        tk.createcommand(w, self.dispatch)

    def __repr__(self):
        return "%s(%s<%s>)" % (self.__class__.__name__,
                               self.widget.__class__.__name__,
                               self.widget._w)

    def close(self):
        "Unregister operations and revert redirection created by .__init__."
        for operation in list(self._operations):
            self.unregister(operation)
        widget = self.widget
        tk = widget.tk
        w = widget._w
        # Restore the original widget Tcl command.
        tk.deletecommand(w)
        tk.call("rename", self.orig, w)
        del self.widget, self.tk  # Should not be needed
        # if instance is deleted after close, as in Percolator.

    def register(self, operation, function):
        '''Return OriginalCommand(operation) after registering function.

        Registration adds an operation: function pair to ._operations.
        It also adds a widget function attribute that masks the tkinter
        class instance method.  Method masking operates independently
        from command dispatch.

        If a second function is registered for the same operation, the
        first function is replaced in both places.
        '''
        self._operations[operation] = function
        setattr(self.widget, operation, function)
        return OriginalCommand(self, operation)

    def unregister(self, operation):
        '''Return the function for the operation, or None.

        Deleting the instance attribute unmasks the class attribute.
        '''
        if operation in self._operations:
            function = self._operations[operation]
            del self._operations[operation]
            try:
                delattr(self.widget, operation)
            except AttributeError:
                pass
            return function
        else:
            return None

    def dispatch(self, operation, *args):
        '''Callback from Tcl which runs when the widget is referenced.

        If an operation has been registered in self._operations, apply the
        associated function to the args passed into Tcl. Otherwise, pass the
        operation through to Tk via the original Tcl function.

        Note that if a registered function is called, the operation is not
        passed through to Tk.  Apply the function returned by self.register()
        to *args to accomplish that.  For an example, see colorizer.py.

        '''
        m = self._operations.get(operation)
        try:
            if m:
                return m(*args)
            else:
                return self.tk.call((self.orig, operation) + args)
        except TclError:
            return ""

class OriginalCommand:
    '''Callable for original tk command that has been redirected.

    Returned by .register; can be used in the function registered.
    redir = WidgetRedirector(text)
    def my_insert(*args):
        print("insert", args)
        original_insert(*args)
    original_insert = redir.register("insert", my_insert)
    '''

    def __init__(self, redir, operation):
        '''Create .tk_call and .orig_and_operation for .__call__ method.

        .redir and .operation store the input args for __repr__.
        .tk and .orig copy attributes of .redir (probably not needed).
        '''
        self.redir = redir
        self.operation = operation
        self.tk = redir.tk  # redundant with self.redir
        self.orig = redir.orig  # redundant with self.redir
        # These two could be deleted after checking recipient code.
        self.tk_call = redir.tk.call
        self.orig_and_operation = (redir.orig, operation)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__,
                               self.redir, self.operation)

    def __call__(self, *args):
        return self.tk_call(self.orig_and_operation + args)

def _widget_redirector(parent):  # htest #
    from tkinter import Toplevel, Text

    top = Toplevel(parent)
    top.title("Test WidgetRedirector")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("+%d+%d" % (x, y + 175))
    text = Text(top)
    text.pack()
    text.focus_set()
    redir = WidgetRedirector(text)
    def my_insert(*args):
        print("insert", args)
        original_insert(*args)
    original_insert = redir.register("insert", my_insert)

class Percolator:

    def __init__(self, text):
        # XXX would be nice to inherit from Delegator
        self.text = text
        self.redir = WidgetRedirector(text)
        self.top = self.bottom = Delegator(text)
        self.bottom.insert = self.redir.register("insert", self.insert)
        self.bottom.delete = self.redir.register("delete", self.delete)
        self.filters = []

    def close(self):
        while self.top is not self.bottom:
            self.removefilter(self.top)
        self.top = None
        self.bottom.setdelegate(None)
        self.bottom = None
        self.redir.close()
        self.redir = None
        self.text = None

    def insert(self, index, chars, tags=None):
        # Could go away if inheriting from Delegator
        self.top.insert(index, chars, tags)

    def delete(self, index1, index2=None):
        # Could go away if inheriting from Delegator
        self.top.delete(index1, index2)

    def insertfilter(self, filter):
        # Perhaps rename to pushfilter()?
        assert isinstance(filter, Delegator)
        assert filter.delegate is None
        filter.setdelegate(self.top)
        self.top = filter

    def removefilter(self, filter):
        # XXX Perhaps should only support popfilter()?
        assert isinstance(filter, Delegator)
        assert filter.delegate is not None
        f = self.top
        if f is filter:
            self.top = filter.delegate
            filter.setdelegate(None)
        else:
            while f.delegate is not filter:
                assert f is not self.bottom
                f.resetcache()
                f = f.delegate
            f.setdelegate(filter.delegate)
            filter.setdelegate(None)

def _percolator(parent):  # htest #
    import tkinter as tk

    class Tracer(Delegator):
        def __init__(self, name):
            self.name = name
            Delegator.__init__(self, None)

        def insert(self, *args):
            print(self.name, ": insert", args)
            self.delegate.insert(*args)

        def delete(self, *args):
            print(self.name, ": delete", args)
            self.delegate.delete(*args)

    box = tk.Toplevel(parent)
    box.title("Test Percolator")
    x, y = map(int, parent.geometry().split('+')[1:])
    box.geometry("+%d+%d" % (x, y + 175))
    text = tk.Text(box)
    p = Percolator(text)
    pin = p.insertfilter
    pout = p.removefilter
    t1 = Tracer("t1")
    t2 = Tracer("t2")

    def toggle1():
        (pin if var1.get() else pout)(t1)
    def toggle2():
        (pin if var2.get() else pout)(t2)

    text.pack()
    var1 = tk.IntVar(parent)
    cb1 = tk.Checkbutton(box, text="Tracer1", command=toggle1, variable=var1)
    cb1.pack()
    var2 = tk.IntVar(parent)
    cb2 = tk.Checkbutton(box, text="Tracer2", command=toggle2, variable=var2)
    cb2.pack()

def any(name, alternates):
    "Return a named group pattern matching list of alternates."
    return "(?P<%s>" % name + "|".join(alternates) + ")"

def make_pat():
    kw = r"\b" + any("KEYWORD", keyword.kwlist) + r"\b"
    builtinlist = [str(name) for name in dir(builtins)
                   if not name.startswith('_') and
                   name not in keyword.kwlist]
    builtin = r"([^.'\"\\#]\b|^)" + any("BUILTIN", builtinlist) + r"\b"
    comment = any("COMMENT", [r"#[^\n]*"])
    stringprefix = r"(?i:r|u|f|fr|rf|b|br|rb)?"
    sqstring = stringprefix + r"'[^'\\\n]*(\\.[^'\\\n]*)*'?"
    dqstring = stringprefix + r'"[^"\\\n]*(\\.[^"\\\n]*)*"?'
    sq3string = stringprefix + r"'''[^'\\]*((\\.|'(?!''))[^'\\]*)*(''')?"
    dq3string = stringprefix + r'"""[^"\\]*((\\.|"(?!""))[^"\\]*)*(""")?'
    string = any("STRING", [sq3string, dq3string, sqstring, dqstring])
    return (kw + "|" + builtin + "|" + comment + "|" + string +
            "|" + any("SYNC", [r"\n"]))

prog = re.compile(make_pat(), re.S)
idprog = re.compile(r"\s+(\w+)", re.S)

DEBUG = False

def color_config(text):
    text.config(
        foreground='#000',
        background='#FFF',
        insertbackground='#000',
        selectforeground='#000',
        selectbackground='#777',
        inactiveselectbackground='#777'
        )

class ColorDelegator(Delegator):
    """Delegator for syntax highlighting (text coloring).

    Instance variables:
        delegate: Delegator below this one in the stack, meaning the
                one this one delegates to.

        Used to track state:
        after_id: Identifier for scheduled after event, which is a
                timer for colorizing the text.
        allow_colorizing: Boolean toggle for applying colorizing.
        colorizing: Boolean flag when colorizing is in process.
        stop_colorizing: Boolean flag to end an active colorizing
                process.
    """

    def __init__(self):
        Delegator.__init__(self)
        self.init_state()
        self.prog = prog
        self.idprog = idprog
        self.LoadTagDefs()

    def init_state(self):
        "Initialize variables that track colorizing state."
        self.after_id = None
        self.allow_colorizing = True
        self.stop_colorizing = False
        self.colorizing = False

    def setdelegate(self, delegate):
        """Set the delegate for this instance.

        A delegate is an instance of a Delegator class and each
        delegate points to the next delegator in the stack.  This
        allows multiple delegators to be chained together for a
        widget.  The bottom delegate for a colorizer is a Text
        widget.

        If there is a delegate, also start the colorizing process.
        """
        if self.delegate is not None:
            self.unbind("<<toggle-auto-coloring>>")
        Delegator.setdelegate(self, delegate)
        if delegate is not None:
            self.config_colors()
            self.bind("<<toggle-auto-coloring>>", self.toggle_colorize_event)
            self.notify_range("1.0", "end")
        else:
            # No delegate - stop any colorizing.
            self.stop_colorizing = True
            self.allow_colorizing = False

    def config_colors(self):
        "Configure text widget tags with colors from tagdefs."
        for tag, cnf in self.tagdefs.items():
            self.tag_configure(tag, **cnf)
        self.tag_raise('sel')

    def LoadTagDefs(self):
        "Create dictionary of tag names to text colors."
        self.tagdefs = {
            "COMMENT":{'foreground': '#dd0000', 'background': '#ffffff'},
            "KEYWORD":{'foreground': '#ff7700', 'background': '#ffffff'},
            "BUILTIN":{'foreground': '#900090', 'background': '#ffffff'},
            "STRING": {'foreground': '#00aa00', 'background': '#ffffff'},
            "DEFINITION":{'foreground': '#0000ff', 'background': '#ffffff'},
            "SYNC": {'background': None, 'foreground': None},
            "TODO": {'background': None, 'foreground': None},
            "ERROR":{'foreground': '#000000', 'background': '#ff7777'},
            # "hit" is used by ReplaceDialog to mark matches. It shouldn't be changed by Colorizer, but
            # that currently isn't technically possible. This should be moved elsewhere in the future
            # when fixing the "hit" tag's visibility, or when the replace dialog is replaced with a
            # non-modal alternative.
            "hit": {'foreground': '#ffffff', 'background': '#000000'}
        }

    def insert(self, index, chars, tags=None):
        "Insert chars into widget at index and mark for colorizing."
        index = self.index(index)
        self.delegate.insert(index, chars, tags)
        self.notify_range(index, index + "+%dc" % len(chars))

    def delete(self, index1, index2=None):
        "Delete chars between indexes and mark for colorizing."
        index1 = self.index(index1)
        self.delegate.delete(index1, index2)
        self.notify_range(index1)

    def notify_range(self, index1, index2=None):
        "Mark text changes for processing and restart colorizing, if active."
        self.tag_add("TODO", index1, index2)
        if self.after_id:
            if DEBUG: print_("colorizing already scheduled")
            return
        if self.colorizing:
            self.stop_colorizing = True
            if DEBUG: print_("stop colorizing")
        if self.allow_colorizing:
            if DEBUG: print_("schedule colorizing")
            self.after_id = self.after(1, self.recolorize)
        return

    def close(self):
        if self.after_id:
            after_id = self.after_id
            self.after_id = None
            if DEBUG: print_("cancel scheduled recolorizer")
            self.after_cancel(after_id)
        self.allow_colorizing = False
        self.stop_colorizing = True

    def toggle_colorize_event(self, event=None):
        """Toggle colorizing on and off.

        When toggling off, if colorizing is scheduled or is in
        process, it will be cancelled and/or stopped.

        When toggling on, colorizing will be scheduled.
        """
        if self.after_id:
            after_id = self.after_id
            self.after_id = None
            if DEBUG: print_("cancel scheduled recolorizer")
            self.after_cancel(after_id)
        if self.allow_colorizing and self.colorizing:
            if DEBUG: print_("stop colorizing")
            self.stop_colorizing = True
        self.allow_colorizing = not self.allow_colorizing
        if self.allow_colorizing and not self.colorizing:
            self.after_id = self.after(1, self.recolorize)
        if DEBUG:
            print("auto colorizing turned",
                  "on" if self.allow_colorizing else "off")
        return "break"

    def recolorize(self):
        """Timer event (every 1ms) to colorize text.

        Colorizing is only attempted when the text widget exists,
        when colorizing is toggled on, and when the colorizing
        process is not already running.

        After colorizing is complete, some cleanup is done to
        make sure that all the text has been colorized.
        """
        self.after_id = None
        if not self.delegate:
            if DEBUG: print_("no delegate")
            return
        if not self.allow_colorizing:
            if DEBUG: print_("auto colorizing is off")
            return
        if self.colorizing:
            if DEBUG: print_("already colorizing")
            return
        try:
            self.stop_colorizing = False
            self.colorizing = True
            if DEBUG: print_("colorizing...")
            t0 = time.perf_counter()
            self.recolorize_main()
            t1 = time.perf_counter()
            if DEBUG: print_("%.3f seconds" % (t1-t0))
        finally:
            self.colorizing = False
        if self.allow_colorizing and self.tag_nextrange("TODO", "1.0"):
            if DEBUG: print_("reschedule colorizing")
            self.after_id = self.after(1, self.recolorize)

    def recolorize_main(self):
        "Evaluate text and apply colorizing tags."
        next = "1.0"
        while True:
            item = self.tag_nextrange("TODO", next)
            if not item:
                break
            head, tail = item
            self.tag_remove("SYNC", head, tail)
            item = self.tag_prevrange("SYNC", head)
            head = item[1] if item else "1.0"

            chars = ""
            next = head
            lines_to_get = 1
            ok = False
            while not ok:
                mark = next
                next = self.index(mark + "+%d lines linestart" %
                                         lines_to_get)
                lines_to_get = min(lines_to_get * 2, 100)
                ok = "SYNC" in self.tag_names(next + "-1c")
                line = self.get(mark, next)
                ##print head, "get", mark, next, "->", repr(line)
                if not line:
                    return
                for tag in self.tagdefs:
                    self.tag_remove(tag, mark, next)
                chars = chars + line
                m = self.prog.search(chars)
                while m:
                    for key, value in m.groupdict().items():
                        if value:
                            a, b = m.span(key)
                            self.tag_add(key,
                                         head + "+%dc" % a,
                                         head + "+%dc" % b)
                            if value in ("def", "class"):
                                m1 = self.idprog.match(chars, b)
                                if m1:
                                    a, b = m1.span(1)
                                    self.tag_add("DEFINITION",
                                                 head + "+%dc" % a,
                                                 head + "+%dc" % b)
                    m = self.prog.search(chars, m.end())
                if "SYNC" in self.tag_names(next + "-1c"):
                    head = next
                    chars = ""
                else:
                    ok = False
                if not ok:
                    # We're in an inconsistent state, and the call to
                    # update may tell us to stop.  It may also change
                    # the correct value for "next" (since this is a
                    # line.col string, not a true mark).  So leave a
                    # crumb telling the next invocation to resume here
                    # in case update tells us to leave.
                    self.tag_add("TODO", next)
                self.update()
                if self.stop_colorizing:
                    if DEBUG: print_("colorizing stopped")
                    return

    def removecolors(self):
        "Remove all colorizing tags."
        for tag in self.tagdefs:
            self.tag_remove(tag, "1.0", "end")

def _color_delegator(parent):  # htest #
    from tkinter import Toplevel, Text
    #from idlelib.percolator import Percolator

    top = Toplevel(parent)
    top.title("Test ColorDelegator")
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry("700x250+%d+%d" % (x + 20, y + 175))
    source = (
        "if True: int ('1') # keyword, builtin, string, comment\n"
        "elif False: print_(0)\n"
        "else: float(None)\n"
        "if iF + If + IF: 'keyword matching must respect case'\n"
        "if'': x or''  # valid keyword-string no-space combinations\n"
        "async def f(): await g()\n"
        "# All valid prefixes for unicode and byte strings should be colored.\n"
        "'x', '''x''', \"x\", \"\"\"x\"\"\"\n"
        "r'x', u'x', R'x', U'x', f'x', F'x'\n"
        "fr'x', Fr'x', fR'x', FR'x', rf'x', rF'x', Rf'x', RF'x'\n"
        "b'x',B'x', br'x',Br'x',bR'x',BR'x', rb'x', rB'x',Rb'x',RB'x'\n"
        "# Invalid combinations of legal characters should be half colored.\n"
        "ur'x', ru'x', uf'x', fu'x', UR'x', ufr'x', rfu'x', xf'x', fx'x'\n"
        )
    text = Text(top, background="white")
    text.pack(expand=1, fill="both")
    text.insert("insert", source)
    text.focus_set()

    color_config(text)
    p = Percolator(text)
    d = ColorDelegator()
    p.insertfilter(d)

def main():
    '''
    theme = idleConf.CurrentTheme()
    normal_colors = idleConf.GetHighlight(theme, 'normal')
    cursor_color = idleConf.GetHighlight(theme, 'cursor')['foreground']
    select_colors = idleConf.GetHighlight(theme, 'hilite')

    print(f"""{{
  'foreground':"{normal_colors['foreground']}",
  'background':"{normal_colors['background']}",
  'insertbackground':"{cursor_color}",
  'selectforeground':"{select_colors['foreground']}",
  'selectbackground':"{select_colors['background']}",
  'inactiveselectbackground':"{select_colors['background']}"
    }}""")

    print(f"""
     self.tagdefs = {{
            "COMMENT":"{idleConf.GetHighlight(theme, "comment")}",
            "KEYWORD":"{idleConf.GetHighlight(theme, "keyword")}",
            "BUILTIN":"{idleConf.GetHighlight(theme, "builtin")}",
            "STRING": "{idleConf.GetHighlight(theme, "string")}",
            "DEFINITION":"{ idleConf.GetHighlight(theme, "definition")}",
            "SYNC": {{'background': None, 'foreground': None}},
            "TODO": {{'background': None, 'foreground': None}},
            "ERROR":"{idleConf.GetHighlight(theme, "error")}",
            # "hit" is used by ReplaceDialog to mark matches. It shouldn't be changed by Colorizer, but
            # that currently isn't technically possible. This should be moved elsewhere in the future
            # when fixing the "hit" tag's visibility, or when the replace dialog is replaced with a
            # non-modal alternative.
            "hit": "{idleConf.GetHighlight(theme, "hit")}"
    }}""")
    '''
    pass

if __name__=='__main__':
    main()