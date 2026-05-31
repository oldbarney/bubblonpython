"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from bubblib.utils import log
from .baseelements import BaseBlockPresenter
from bubblib.globaldefs import render_defaults, dispmarkups
from bubblib.gutils import BubblFont
from bubblib.basetexteditor import BaseTextItem
from .blockeditor import BlockEditor
from bubblib.textcontainer import EMPTY_TEXT_BLOCK_TEXT
from bubblib.uiserver import ui


#from popup import popup_menu

class TextPresenter(BaseBlockPresenter, BaseTextItem):  #Its a QGraphicsObject
    #<Enter> creates a new line
    #Esc exits - to update block
    #<Ctrl>I,b,uparrow,downarrow for bold,italic,superscript,subscript
    #<Ctrl>u or z undo, <ctrl>v,c,x for insert clipboard,copy to cliboard,cut to cliboard
    # arrow-keys, home end PgUp etc, as expected
    #html tags for <b> <i> <super> <sub> and <br />
    #'reveal codes' mode of wordwise ??
    #clipboard is instance of TextItem, so contains appropriate html handling
    #provides set of MIME types for cut/paste operations via system clipboard
    undo_map={}

    def __init__(self, diag_editor, node=None):
        BaseBlockPresenter.__init__(self, diag_editor, node)
        if len(self.params)<3:
            self.params[1:]=(render_defaults.font,'#000')
            #text=self.params[0]
            #self.params.clear()
            #self.params.append(text)
            #self.params.append('TKDefaultFont')
            #self.params.append('#000')
        #print('Font to pass to BaseTextItem from TextPresenter is ',self.params[1])
        BaseTextItem.__init__(self, self.params[0], font=self.params[1], colour=self.params[2])
        undo_map_key=f'{diag_editor.diag.name},{node.no}'
        try:
            self.undos=self.undo_map[undo_map_key]
        except KeyError:
            self.undos=[]
            self.undo_map[undo_map_key]=self.undos

        self.undos=[]
        self.current_attrib=0
        #self.flasher.signal.connect(self.prepareGeometryChange)
        self.cursor_coords=0,0,0,0
        self.insert_mode=True
        self.active=False
        self.cursor_phase=0

    def reload(self):
        self.fonts={}
        self.html=self.params[0]
        self.font = BubblFont(self.params[1])
        self.colour= self.params[2]

    def refresh(self):
        #return true if cursor changed
        #print('Text Presenter Refreshing')
        last=self.cursor_coords
        self.cursor_coords=self.draw(self.xpos(),self.ypos(),self.canvas,self.uid)
        if last[0]!=self.cursor_coords[0] or last[1]!=self.cursor_coords[1]:
            if self.active:
                self.text_cursor_on()

    def text_cursor_on(self):
        #print('switching cursor on')
        self.canvas.delete('textcursor')
        self.cursor_phase=0
        self.canvas.create_line(*self.cursor_coords,fill='#000',width=2,tag='textcursor')
        if not self.active:
            self.active=True
            ui.root.after(100,self.update_cursor)

    def text_cursor_off(self):
        self.canvas.delete('textcursor')
        self.active=False

    def update_cursor(self):
        #print('updating cursor',self.cursor_phase)
        if not self.active:
            self.canvas.delete('textcursor')
            return
        self.cursor_phase+=1
        if self.cursor_phase>=7:
            self.canvas.create_line(*self.cursor_coords,fill='#000',width=2,tag='textcursor')
            self.cursor_phase=0
        elif self.cursor_phase==4:
            self.canvas.delete('textcursor')
        ui.root.after(100,self.update_cursor)

    def undo(self):
        if self.undos:
            self.html,self.fontname,self.fontsize,self.colour=self.undos.pop()
            self.update_params(False)

    def update_params(self,undoable=True):
        if undoable:
            self.undos.append(self.params)
        self.params[0]=self.html
        self.params[1]=self.font.__str__()
        self.params[2]=self.colour
        log(f'LIVETEXTEDIT UPDATED PARAMS >{self.font}<',self.html)

    def mouse_down(self,*args):
        log('livetextedit mouse down')
        if len(args)==2:
            (x,y)=args
        else:
            x,y=self.xy(args[0])
        x-=self.xpos()
        y-=self.ypos()
        self.position_cursor(x,y,False)
        self.refresh()
        self.text_cursor_on()

    def mouse_move(self,event):
        log(f'livetextedit mouseMoveEvent')
        x,y=self.xy(event)
        self.position_cursor(x-self.xpos(),y-self.ypos(),True)
        self.refresh()

    def mouse_up(self,event):
        log('livetextedit mouse release nothing to do')

    def highlight(self,highlight):
        if self.highlighted:
            if not highlight:
                self.highlighted=False
                self.refresh()
        else:
            if highlight:
                self.highlighted=True
                self.refresh()

    def edit(self,x,y,on_top=False,line_no=None):
        log('TextPresenter.edit calling editor')
        log('presentation edlines',self.node.presentation['edlines'])
        self.update_params()
        self.beditor = BlockEditor(self.diag_editor,self.node,x,y)

    def end_edit(self,changed):
        log('END_EDIT c',changed)
        if changed:
            self.reload()
            self.refresh()
        self.beditor=None

    def toggle(self,attrib):
        self.current_attrib ^= attrib

    def scaled_width(self):
        if self.is_empty():
            return(self.font.font.measure(EMPTY_TEXT_BLOCK_TEXT))
        return max(self.font.font.measure(line) for line in self.lines)

    def scaled_height(self):
        if self.is_empty():
            return(self.line_space)
        return self.line_space*len(self.lines)

    def get_json_for_disp_thing(self,node_no,link,gx,gy,x_org,y_org):
        """Return json for block connecting to node_no_1
        """

        text=self.params[0].replace('<br />',r'\\n')
        x_off=self.node.init['pos'][0]*render_defaults.grid-x_org
        y_off=self.node.init['pos'][1]*render_defaults.grid-y_org
        def mups():
            #'write',line,'rect','ellipse','polygon','arc'
            result=f'''
    ["colour","{self.params[2]}"],
    ["font","{self.params[1]}"],
    ["x","round(_xorg+{x_off:.2f})"],
    ["y","round(_yorg+{y_off:.2f})"]'''
            return result

        def pars():
            return f'''["'{text}'",{mups()}]'''

        def height():
            return 5

        result=f""""{node_no}":{{"params":{pars()},
"type":"WRITE",
"size":[7,{height()}],
"pos":[{gx},{gy}],
"links":[{link}]}}""",gy+height()+1
        log('TEXTJASON',result[0])
        return result
