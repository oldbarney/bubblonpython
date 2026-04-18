"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"

from .textcontainer import BlockOfText
from .uiserver import ui
from .utils import log


class BaseTextItem(BlockOfText):
    #<Enter> creates a new line
    #Esc exits - to update block
    #<Ctrl>b,i,uparrow,downarrow for bold,italic,superscript,subscript
    #<Ctrl>u or z undo, <ctrl>v,c,x for insert, copy, cut to cliboard
    # arrow-keys, home end PgUp etc, as expected
    #html tags for <b> <i> <super> <sub> and <br />
    #'reveal codes' mode of wordwise ??
    #provides set of MIME types for cut/paste operations via system clipboard

    def __init__(self,text, font="Courier,10", colour='#000',tabsize=4,autoindent=True):

        BlockOfText.__init__(self,text, font=font, colour=colour)
        #self.colour=QColor(self.node.params[1])
        self.undos=[]
        self.state='off' #selecting, live,
        self.current_attrib=0
        #self.flasher.signal.connect(self.prepareGeometryChange)
        self.cursor_pos=None
        self.insert_mode=True
        self.tabsize=tabsize
        self.autoindent=autoindent
        self.marking=False

    def command(self,cmd,*args,cont=False):
        """
        :param cmd:
            reset
            curs number
            curs_and_mark number
            mark number
            replace the d2 characters starting from d1 with d3  (d1=index d2=length d3=new text)
            undo
            copy characters between mark and cursor to clipboard  here todo much more
            paste replace characters between mark and  cursor with clipboard
            cut characters between mark and cursor to clipboard

        :param d1:
        :param d2:
        :param d3:
        :return:
        """
        if cmd=='reset':
            self.undos=[]
        elif cmd=='curs':
            self.undos.append((cont,self._curs,self._mark,0,0,'',''))
            log(f'assigning cursor with [{args[0]}] before c={self._curs}, m={self._mark}',level=1)
            self.curs=args[0]
            log(f'assigned after c={self._curs}, m={self._mark}',level=1)
        elif cmd=='mark':
            self.mark=args[0]
        elif cmd=="replace":
            pass
        elif cmd=='undo':
            while self.undos:
                (cont,cur,mar,index,length,text,attributes)=self.undos.pop(-1)
                self.replace_ta(index,length,text,attributes,undoable=False)
                self.curs=(cur,mar)
                self.check_marked()
                if not cont:
                    break
            else:
                log('Nothing to undo',level=2)
        else:
            log(f'BaseTextItem unrecognised command: {cmd}',level=2)

    def marked_text(self):
        return self.plain_text[min(self._curs,self._mark):max(self._curs,self._mark)]

    def replace_ta(self,index,length,text,attributes=None,undoable=True):
        if undoable:
            oldcurs=self._curs
            oldmark=self._mark
            nt,na=super().replace_ta(index,length,text,attributes)
            self.undos.append((False,oldcurs,oldmark,index,len(text),nt,na))
        else:
            super().replace_ta(index,length,text,attributes)

    def copy_to_clipboard(self):
        ui.root.clipboard_append(self.marked_text())

    def insert_from_clipboard(self):
        newtext=ui.root.clipboard_get()
        pos=min(self._curs,self._mark)
        newcurs=pos+len(newtext)
        self.replace_ta(pos,abs(self._curs-self._mark),newtext)
        self.curs=newcurs

    def cut_to_clipboard(self):
        ui.root.clipboard_append(self.marked_text())
        newtext=''
        pos=min(self._curs,self._mark)
        newcurs=pos+len(newtext)
        self.replace_ta(pos,abs(self._curs-self._mark),newtext)
        self.curs=newcurs

    def ed_char(self,s,a):
        if self._curs!=self._mark:
            self.replace_ta(min(self._mark,self._curs),abs(self._curs-self._mark),s,a)
            self.command("curs",min(self._curs,self._mark)+len(s),cont=True)
        elif self.insert_mode or self._curs==len(self.editable[0]):
            self.replace_ta(self._curs,0,s,a)
            self.command("curs",self._curs+1,cont=True)
        else:
            self.replace_ta(self._curs,1,s,a)
            self.command("curs",self._curs+1,cont=True)
        self.check_marked()

    def ed_return(self):
        r,c=self.ind_to_rc(self._curs)
        row=self.lines[r]
        lead=0
        if self.autoindent:
            while lead<len(row) and lead<c and row[lead]==' ':
                lead+=1
        self.replace_ta(self._curs,0,'\r'+' '*lead,'\r'+hex(self.current_attrib)[-1]*lead)
        self.command("curs",self._curs+lead+1,cont=True)

    def ed_c_end(self,shift):
        if self._curs==self.max_cursor():
            return
        r,c=self.ind_to_rc(self._curs)
        if c<len(self.lines[r]):
            c=len(self.lines[r])
            if shift:
                self.command("curs",(self.rc_to_ind(r,c),self._mark))
            else:
                self.command("curs",self.rc_to_ind(r,c))
        else:
            self.command("curs",self.max_cursor())

    def ed_c_home(self,shift):
        if self._curs==0:
            return
        r,c=self.ind_to_rc(self._curs)
        if c>0:
            if shift:
                self.command("curs",(self.rc_to_ind(r,0),self._mark))
            else:
                self.command("curs",self.rc_to_ind(r,0))
        else:
            if shift:
                self.command("curs",(0,self._mark))
            else:
                self.command("curs",0)

    def ed_c_down(self,shift):
        if self._curs==self.max_cursor():
            return
        r,c=self.ind_to_rc(self._curs)
        r+=1
        if r==len(self.lines):  #todo here this is wrong
            self.replace_ta(self.max_cursor(),0,'\r','\r')
            self.command("curs",self.max_cursor(),cont=True)
        else:
            if c>len(self.lines[r]):
                c=len(self.lines[r])
            if shift:
                self.command("curs",(self.rc_to_ind(r,c),self._mark))
            else:
                self.command("curs",self.rc_to_ind(r,c))

    def ed_c_up(self,shift):
        r,c=self.ind_to_rc(self._curs)
        if r>0:
            r-=1
            if c>len(self.lines[r]):
                c=len(self.lines[r])
            if shift:
                self.command("curs",(self.rc_to_ind(r,c),self._mark))
            else:
                self.command("curs",self.rc_to_ind(r,c))

    def ed_c_left(self, ctrl,shift):
        if self._curs==0:
            return
        if ctrl:
            log('control_left',level=1)
        if shift:
            self.command("curs",(self._curs-1,self._mark))
        else:
            self.command("curs",self._curs-1)

    def ed_c_right(self, ctrl,shift):
        if self._curs<self.max_cursor():
            if ctrl:
                log('control_right',level=1)
            if shift:
                self.command("curs",(self._curs+1,self._mark))
            else:
                self.marking=False
                self.command("curs",self._curs+1)

    def ed_backspace(self):
        if self._curs!=self._mark:
            self.replace_ta(min(self._mark,self._curs),abs(self._curs-self._mark),'','')
            log('backspacing surely should not be marked now',level=2)
            self.command("curs",min(self._curs,self._mark),cont=True)
        else:
            if self._curs==0:
                return
            r,c=self.ind_to_rc(self._curs)
            if c==0 or not self.autoindent:
                self.replace_ta(self._curs-1,1,'','')
                self.command("curs",self._curs-1,cont=True)
            else:
                self.ed_c_backtab()

    def ed_c_del(self):
        if self._curs!=self._mark:
            self.replace_ta(min(self._mark,self._curs),abs(self._curs-self._mark),'','')
            self.command("curs",min(self._curs,self._mark),cont=True)
        else:
            if self._curs==self.max_cursor():
                return
            self.replace_ta(self._curs,1,'','')

    def ed_c_tab(self):
        def get_tab_dist():
            r,c=self.ind_to_rc(self._curs)
            return (c//self.tabsize+1)*self.tabsize-c
        diff=get_tab_dist()
        self.replace_ta(self.curs,0,' '*diff,hex(self.current_attrib)[-1]*diff)
        self.command("curs",self._curs+diff,cont=True)

    def ed_c_backtab(self):
        r,c=self.ind_to_rc(self._curs)
        if c==0:
            return
        row=self.lines[r]
        newc=((c-1)//self.tabsize)*self.tabsize
        log(f'backtab({row[:c]}),({" "*c})',level=1)
        if row[:c]!=' '*c:
            self.replace_ta(self._curs-1,1,'','')
            self.command("curs",self._curs-1,cont=True)
        else:
            diff=c-newc
            self.replace_ta(self._curs-diff,diff,'','')
            self.command("curs",self._curs-diff,cont=True)

    def position_cursor(self,x,y,marking):
        log('position cursor',x,y,level=1)
        r,c=self.xy_to_rc(x,y)
        if r>=len(self.lines):
            r=len(self.lines)-1
        elif r<0:
            r=0
        if c>len(self.lines[r]):
            c=len(self.lines[r])
        elif c<0:
            c=0
        log('position cursor r,c',r,c,level=1)

        newcursor=self.rc_to_ind(r,c)
        log(f'cursor ind=',self.curs,level=1)
        if newcursor==0:
            self.current_attrib=0
        else:
            try:
                self.current_attrib=int(self.editable[1][newcursor-1],16)
            except:
                self.current_attrib=0
        if marking:
            self.command("curs",(newcursor,self._mark))
        else:
            self.command("curs",newcursor)

    def toggle(self,attrib):
        self.current_attrib ^= attrib
