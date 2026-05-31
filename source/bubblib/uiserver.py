"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import tkinter as tk

from .utils import log
try:
    from tkinterdnd2 import TkinterDnD
except:
    TkinterDnD=None

class UIFlasher:
    def __init__(self,parent,on_proc,off_proc):
        self.parent=parent
        self.on_proc=on_proc
        self.off_proc=off_proc
        self.state='stopped'

    def start(self,on=500,off=300):
        self.on_time=on
        self.off_time=off
        if self.state=='stopped':
            self.state='off'
            self.repeat()
        elif self.state=='stopping':
            self.state='off'

    def repeat(self):
        #print('FLASH_TIMER REPEAT state',self.state)
        if self.state =='off':
            self.on_proc()
            self.state='on'
            self.parent.after(self.on_time,self.repeat)
        elif self.state=='on':
            self.off_proc()
            self.state='off'
            self.parent.after(self.off_time,self.repeat)
        elif self.state=='stopping':
            self.state='stopped'

    def stop(self):
        #print('FLASH TIMER STopping state=',self.state)
        if self.state=='on':
            self.off_proc()
            self.state='stopping'
        elif self.state=='off':
            self.state='stopping'
        #print('FLASH timer Stopped')
class UITimer:
    timer_no=1
    def __init__(self,parent,client_handler,interval=1000):
        self._active_number=1
        self.event_id=f'<<UITimer{self.timer_no}>>'
        self.timer_no+=1
        self.parent=parent
        self.client_handler=client_handler
        self.interval=interval
        self._repeat=False

    def restart(self):
        self.parent.event_generate(self.event_id)
        if self._repeat:
            self.parent.after(self.interval,self.restart)

    def handle_event(self,number):
        if number==self._active_number:
            self.client_handler()

    def start(self,ms=None,repeat=True):
        if ms is not None:
            self.interval=ms
        self._repeat=repeat
        self._active_number+=1
        self.parent.bind(self.event_id,lambda event,number=self._active_number:self.handle_event(number))
        self.parent.after(self.interval,self.restart)

    def isActive(self):
        return self._active

    def stop(self):
        self._active_number+=1 #this prevents last event
        self.parent.unbind(self.event_id)

class UI():
    def __init__(self):
        self.tk=tk
        if TkinterDnD is not None:
            self.root=TkinterDnD.Tk()
            self.has_dnd=True
        else:
            self.root=tk.Tk()
            self.has_dnd=False
        self.root.option_add('*tearOff', False)
        self.root.option_add('*tearOff', False)
        self.root.withdraw()
        self._base_ppp=self.root.call('tk','scaling')

    @property
    def ppp(self):
        return float(self.root.call('tk','scaling'))

    def ok_set_ppp(self,value):
        try:
            self.root.call('tk','scaling','-displayof','.',float(value))
            return True
        except Exception as e:
            return False

    def scaled_font_size(self,size):
        return round(size*self.ppp/self._base_ppp)


    def copy_to_clipboard(self,text,files=False):
        try:
            self.root.clipboard_clear()
        except Exception as e:
            log('benign clipboard_clear() error:',e,level=2)
        if files:
            try:
                self.root.clipboard_append(text,type='FILELIST')
            except Exception as e:
                log('ui copy to cliboard error:',e,level=2)
        else:
            try:
                self.root.clipboard_append(text,type='STRING')
            except Exception as e:
                log('ui copy to cliboard error:',e,level=2)


    def get_clipboard_file_list(self):
        try:
            return self.root.splitlist(ui.root.clipboard_get(type='FILELIST'))
        except Exception as e:
            log('no file list available from clipboard',e,level=2)
            return None

    def get_clipboard_string(self):
        try:
            return self.root.clipboard_get()
        except Exception as e:
            log('no string available from clipboard',e,level=2)
            pass
        try:
            return '\n'.join(self.get_clipboard_file_list())
        except:
            return None

    def run(self):
        self.root.mainloop()

    def close(self,*args):
        self.root.destroy()

    def timer(self,handler):
        return UITimer(self.root,handler)

    def flasher(self,on_proc,off_proc):
        return UIFlasher(self.root,on_proc,off_proc)

    def is_safe_colour(self,c):
        try:
            _=self.root.winfo_rgb(c)
            return True
        except Exception as e:
            #print(f'invalid colour({c})',e)
            return False

    def valid_colour(self,colour,default='#000'):
        if colour is None:
            return default
        try:
            self.root.winfo_rgb(colour)
            return colour
        except:
            return default

    def mx(self):
        return self.root.winfo_pointerx()

    def my(self):
        return self.root.winfo_pointery()


    #def request_close_client(self,client):
    #    self.clients_to_close.append(client)
    #    self.root.event_generate("<<close_client>>", when="tail")

    #def close_client(self,event):
    #    self.clients_to_close.popleft().thr.join()

    #def close_ui(self):
    #    self.root.event_generate("<<close_ui>>")

log('UISERVER RUNNING')

ui=UI()
