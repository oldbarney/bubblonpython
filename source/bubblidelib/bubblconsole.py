"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from  tkinter import ttk
import tkinter as tk
from bubblib.globaldefs import ExState
from bubblib.signals import Signal, Slot
from bubblib.utils import log

buttons={
    ExState.stopped_on_node:
        [('Run','undoablerun'),
         ('Step','step'),
         ('Back','back'),
         ('Edit','edit')],
    ExState.stopped_on_link:
        [('Back','back'),
         ('Edit','edit')],
    ExState.active:
        [('Stop','stop')],
    ExState.quiescent:
        [('Activate','activate_flasher')],
    ExState.exited:
        [('Back','back')]
}

class Console(ttk.Frame):
    tell_machine=Signal(str)
    def __init__(self,parent):
        self.editors=''
        ttk.Frame.__init__(self,parent,borderwidth=6,relief='ridge')
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=0)
        #self.stack_frame=tk.Frame(self,borderwidth=1,relief='solid',background='#FEE')
        #self.stack_frame.grid(row=0,column=1,sticky='nsew')
        self.stack_frame=None
        self.label_frame=None

        self.button_frame=tk.Frame(self,borderwidth=1,relief='solid')
        self.rowconfigure(0,weight=1)
        self.rowconfigure(1,weight=0)
        self.update_buttons(ExState.quiescent)

    def cache_editor_list(self,editors):
        self.editors=editors

    def reset(self):
        self.tell_machine.emit('reset')

    def do_tell_machine(self,command,call_stack=None,clear_breakpoint=True):
        if command in ('step','run','undoablerun'):
            self.update_buttons(ExState.active, call_stack)
            if clear_breakpoint:
                self.tell_machine.emit('clear_breakpoint')
        self.tell_machine.emit('steppable','main',*self.editors)
        #print('do_tell_machine emitting',command)
        self.tell_machine.emit(command)

    #@Slot(str,int)
    def select_node(self,diag_name,node_no):
        self.tell_machine.emit('goto',diag_name,node_no)

    def set_break_point(self,diag_name,node_no):
        self.tell_machine.emit('set_breakpoint',diag_name,node_no)

    #@Slot(ExecutionState)
    def update_buttons(self,state,call_stack=None):
        #for l in self.stack_frame.winfo_children():
        #    l.destroy()
        #for l in self.label_frame.winfo_children():
        #    l.destroy()

        if call_stack is not None and len(call_stack)>0:
            if self.stack_frame is None:
                self.label_frame=tk.Frame(self,background='#FEE')
                self.label_frame.rowconfigure(0,weight=0)
                self.label_frame.rowconfigure(1,weight=1)
                self.label_frame.columnconfigure(0,weight=1)
                self.stack_frame=tk.Frame(self,background='#FFF',
                                          )
            self.label_frame.grid(row=0,column=0,sticky='nsew')
            self.stack_frame.grid(row=0,column=1,sticky='nse')
            self.button_frame.grid(row=1,column=0,columnspan=2)

            tk.Label(self.label_frame,
                     text='Call-Stack:',
                     background='#FEE').grid(
                row=0,
                column=0,
                sticky='ne',
                padx=5
            )
            tk.Button(self.label_frame,
                      text='Reset',
                      command=self.reset,
                      background='#FAA').grid(
                row=1,
                column=0,
                sticky='e',
                padx=5
            )
            for i,(block,colour) in enumerate(call_stack):
                self.stack_frame.rowconfigure(i,weight=1)
                tk.Label(self.stack_frame,
                         borderwidth=1,
                         relief='solid',
                         text=block,
                         background=colour,foreground='#000').grid(column=0,row=i,sticky='s',padx=10)
        else:
            if self.stack_frame is not None:
                self.stack_frame.destroy()
                self.label_frame.destroy()
                self.label_frame=None
                self.stack_frame=None
            self.button_frame.grid(row=0,column=0,columnspan=2)

        for b in self.button_frame.winfo_children():
            b.destroy()
        if state==ExState.dying:
            log('console knows maching is dying')
            return
        buts=buttons[state]
        for i,(text,command) in enumerate(buts):
            ttk.Button(self.button_frame,text=text,command=lambda command=command:self.do_tell_machine(command)).grid(row=0,column=i)