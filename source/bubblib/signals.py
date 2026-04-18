"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
class Signal:
    def __init__(self,*args):
        self.args=args
        self.connections=[]

    def connect(self,slot):
        #print(self.args)
        #print(slot)
        if slot in self.connections:
            return
        self.connections.append(slot)

    def bind_event(self,widget,event):
        widget.bind(event,self.emit)

    def disconnect(self,slot):
        try:
            self.connections.remove(slot)
        except:
            pass

    def emit(self,*args):
        for slot in self.connections:
            if isinstance(slot,Signal):
                slot.emit(*args)
            else:
                slot(*args)

def Slot(func,*arg_types):
    def wrapped(*args,**kwargs):
        #if all (isinstance(a,t) for (t,a) in zip(arg_types,args)):
        func(*args,**kwargs)
        #else:
        #    raise Exception(f'Wrong arg types:Expected{args}')
    return wrapped
