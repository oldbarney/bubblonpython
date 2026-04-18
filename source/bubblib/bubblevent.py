"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import time
from types import SimpleNamespace

from bubblib.gutils import ctrl, shift, alt_gr, alt
from bubblib.uiserver import ui


class BubblEvent:
    """Bubbl Events
Bubbl Events are normally sent to the currently running BUBBL machine
and queued until acted on or discarded by a 'Wait' instruction.
Each event object has the field 'event_type' and, depending on the
type of event, other fields with related information.

Event type & fields     Events
WindowEvent             MouseEvents, KeyEvents,DropEvent, MenuEvent,
                        UserEvent,WinDrop,WinSize,WinClose
    page                BubblPage on which event occurred
MouseEvent              MouseDn,MouseUp,MouseMv,MouseWheel,MouseDbl,
    x   x-coord
    y   y-coord
    left    mouse button
    right   mouse button
    middle  mouse button
    over    Page item(s) mouse is over
    ctrl    ctrl-key was pressed
    shift   shift-key was pressed
    alt     alt-key was pressed
    alt_gr  alt_gr key was pressed

KeyEvent                Key, Enter, Esc, Up, Dn, Left, Right, Tab, BackTab,
    key                 PgUp, PgDn, Ins, Del, Home, End, Back, F1,F2.. etc
    ctrl    ctrl-key was pressed
    shift   shift-key was pressed
    alt     alt-key was pressed
    alt_gr  alt_gr key was pressed

TimerEvent              Timer
    Id
OutputStreamEvent       StdOut,StdErr,ProcExit
    id_no
    line

AsyncEvent              Async
    prog_name
    diag_name
    link_name

RxEvent                 Rx
    prtcl   TCP or UDP
    address IPV4 address
    port    port number
    host    IPV4 host
    text    message

RqEvent                 Rq
    conn  Connection
DropEvent               Drop
    mime  mime-types
    data  string or list
    x     x-coord
    y     y-coord
UserEvent               Button,Input,Choice,Radio,Scroll,Check,Text
    page
    source
    value
    tags
MessageEvent            Msg
    sender machine name
    value  message
    """
    def __init__(self,event_type):
        self.event_type=event_type
    def __str__(self):
        return f'{self.event_type}-Event'

class AsyncEvent(BubblEvent):
    def __init__(self,prog,diag):
        super().__init__('Async')
        self.prog_name=prog.name
        self.diag_name=diag
        try:
            self.link_name=prog.sig["linknames"][prog.link]
        except:
            self.link_name=''
    def __str__(self):
        return super().__str__()+f' prog={self.prog_name} diag={self.diag_name}'

class RxEvent(BubblEvent):
    def __init__(self,tcp,host,address,port,message):
        super().__init__('Rx')
        self.prtcl='TCP' if tcp else 'UDP'
        print('RxEvent',self.prtcl,message)
        self.address=address
        self.port=port
        self.host=host
        self.text=message

    def __str__(self):
        return super().__str__()+' address={self.address} port={self.port}'+\
            f' host={self.host} prtcl={self.prtcl} ext={self.text}'

class RqEvent(BubblEvent):
    def __init__(self,conn):
        super().__init__('Rq')
        print('RqEvent',conn)
        self.conn=conn

    def __str__(self):
        return super().__str__()+f' conn={self.conn}'

class TimerEvent(BubblEvent):
    def __init__(self,event_id):
        super().__init__('Timer')
        self.Id=event_id

    def __str__(self):
        return super().__str__()+f' Id={self.Id}'

    def benign_clone(self):
        return SimpleNamespace(event_type=self.event_type,
                               value=self.Id,
                               tags=[]
                               )



class OutputStreamEvent(BubblEvent):
    def __init__(self,event_type,id_no,line=None):
        super().__init__(event_type)
        self._id=id_no
        self._line=line
    @property
    def id_no(self):
        return self._id
    @property
    def line(self):
        return self._line
    def __str__(self):
        return (super().__str__()+f' id={self._id_no} '+
                (f'exit_code={self.line}'
                    if self.event_type=='ProcExit'
                    else f'mess={self.line}'))

class WindowEvent(BubblEvent):
    def __init__(self,event_type,page):
        BubblEvent.__init__(self,event_type)
        self._page=page
    @property
    def page(self):
        return self._page
    def __str__(self):
        return super().__str__()+f' page={self.page.name}'

class MouseEvent(WindowEvent):
    def __init__(self,event_type,x,y,page,button,offset=0,
                 ctrl=False,
                 shift=False,
                 alt=False,
                 alt_gr=False):
        WindowEvent.__init__(self,event_type,page)
        self.x=x
        self.y=y
        self.button=button
        self.offset=offset
        self.ctrl=ctrl
        self.shift=shift
        self.alt_gr=alt_gr
        self.alt=alt

    def __str__(self):
        result=super().__str__()
        result+=f' x={self.x} y={self.y} btn={self.button}'
        if self.ctrl:
            result+=' ctrl'
        if self.shift:
            result+=' shift'
        if self.alt:
            result+=' alt'
        if self.alt_gr:
            result+=' alt_gr'
        return result

    @property
    def left(self):
        return self.button=='left'
    @property
    def right(self):
        return self.button=='right'
    @property
    def middle(self):
        return self.button=='middle'
    @property
    def over(self):
        #to=time.process_time()
        result=self._page.mouse_over
        #print('OVER TOOK',time.process_time()-to)
        return result

class MenuEvent(WindowEvent):
    def __init__(self,page,item):
        WindowEvent.__init__(self,'Menu',page)
        self.value=item
    def __str__(self):
        return super().__str__()+f' value={self.value}'
class DropEvent(WindowEvent):
    def __init__(self,page,drop_event):
        WindowEvent.__init__(self,'WinDrop',page)
        self.mime=ui.root.splitlist(drop_event.type)
        self.data=ui.root.splitlist(drop_event.data)
        self.x = drop_event.x_root - page.window.winfo_x()
        self.y = drop_event.y_root - page.window.winfo_y()

    def __str__(self):
        return (
            super().__str__()+
            f' x={self.x} y={self.y} mime={self.mime} data={self.data}')

class KeyEvent(WindowEvent):
    def __init__(self,event_type,key,page,event):
        WindowEvent.__init__(self,event_type,page)
        self._key=key
        self.ctrl=ctrl(event)
        self.shift=shift(event)
        self.alt_gr=alt_gr(event)
        self.alt=alt(event)

    def __str__(self):
        result=super().__str__()+f' key={self.key}'
        if self.ctrl:
            result+=' ctrl'
        if self.shift:
            result+=' shift'
        if self.alt:
            result+=' alt'
        if self.alt_gr:
            result+=' alt_gr'
        return result

    @property
    def key(self):
        return self._key

class UserEvent(WindowEvent):
    def __init__(self,type_name,page,source,value,tags):
        WindowEvent.__init__(self,type_name,page)
        self.source=source
        self.value=value
        self.tags=tags
    def __str__(self):
        return (super().__str__()+
                f' source={self.source.thing}'+
                f' value={self.value} tags={self.tags}')

    def benign_clone(self):
        return SimpleNamespace(event_type=self.event_type,
                               value=self.value,
                               tags=self.tags
                               )


class ButtonEvent(UserEvent):
    def __init__(self,page,source,text,tags):
        UserEvent.__init__(self,'Button',page,source,text,tags)

class ScrollerEvent(UserEvent):
    def __init__(self,page,source,value,tags):
        UserEvent.__init__(self,'Scroll',page,source,value,tags)

class InputEvent(UserEvent):
    def __init__(self,page,source,value,tags):
        UserEvent.__init__(self,'Input',page,source,value,tags)

class TextEdEvent(UserEvent):
    def __init__(self,page,source,value,tags):
        UserEvent.__init__(self,'Text',page,source,value,tags)

class ChoiceEvent(UserEvent):
    def __init__(self,page,index,value,tags):
        UserEvent.__init__(self,'Choice',page,index,value,tags)

class CheckboxEvent(UserEvent):
    def __init__(self,page,source,value,tags):
        UserEvent.__init__(self,'Check',page,source,value,tags)

class RadioEvent(UserEvent):
    def __init__(self,page,source,value,tags):
        UserEvent.__init__(self,'Radio',page,source,value,tags)

class MessageEvent(BubblEvent):
    def __init__(self,sender,message):
        BubblEvent.__init__(self,'Msg')
        self.sender=sender
        self.value=message
    def __str__(self):
        return super().__str__()+f' sender={self.sender} value={self.value}'
