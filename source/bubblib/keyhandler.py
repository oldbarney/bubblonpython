"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import sys
from .bubblevent import KeyEvent
from .gutils import ctrl, shift

key_bindings=['<Key>','<Pause>','<Escape>','<Prior>','<Next>',
              '<End>','<Home>','<Left>','<Up>','<Right>','<Down>',
              '<Print>','<Insert>','<Delete>','<F1>','<F2>','<F3>',
              '<F4>','<F5>','<F6>','<F7>','<F8>','<F9>','<F10>',
              '<F11>','<F12>','<Return>','<BackSpace>','<Tab>']
if sys.version_info[1]>=12:
    key_bindings.append('<ISO_Left_Tab>')

class BaseKeyHandler:
    def __init__(self,canvas,key_func_map):
        self.error=None
        for bind in key_bindings:
            if bind in key_func_map:
                canvas.bind(bind,key_func_map[bind])
            else:
                canvas.bind(bind,lambda event:self.unbound(bind))

    def unbound(self,binding):
        self.error=('unbound key event',binding)

keypad_map={'KP_Left':'Left',
            'KP_Right':'Right',
            'KP_Up':'Up',
            'KP_Down':'Down',
            'KP_Home':'Home',
            'KP_End':'End',
            'KP_Prior':'PgUp',
            'KP_Next':'PgDn',
            'KP_Insert':'Ins',
            'KP_Delete':'Del'}

class PageKeyHandler(BaseKeyHandler):
    def __init__(self,page):
        self.page=page
        key_map={
            '<Key>':self.key,
            '<Escape>':lambda event:self.ed_key('Esc',event),
            '<End>':lambda event:self.ed_key('End',event),
            '<Home>':lambda event:self.ed_key('Home',event),
            '<Left>':lambda event:self.ed_key('Left',event),
            '<Up>':lambda event:self.ed_key('Up',event),
            '<Right>':lambda event:self.ed_key('Right',event),
            '<Down>':lambda event:self.ed_key('Dn',event),
            '<Print>':lambda event:self.ed_key('Print',event),
            '<Insert>':lambda event:self.ed_key('Ins',event),
            '<Delete>':lambda event:self.ed_key('Del',event),
            '<Prior>':lambda event:self.ed_key('PgUp',event),
            '<Next>':lambda event:self.ed_key('PgDn',event),
            '<F1>':lambda event:self.ed_key('F1',event),
            '<F2>':lambda event:self.ed_key('F2',event),
            '<F3>':lambda event:self.ed_key('F3',event),
            '<F4>':lambda event:self.ed_key('F4',event),
            '<F5>':lambda event:self.ed_key('F5',event),
            '<F6>':lambda event:self.ed_key('F6',event),
            '<F7>':lambda event:self.ed_key('F7',event),
            '<F8>':lambda event:self.ed_key('F8',event),
            '<F9>':lambda event:self.ed_key('F9',event),
            '<F10>':lambda event:self.ed_key('F10',event),
            '<F11>':lambda event:self.ed_key('F11',event),
            '<F12>':lambda event:self.ed_key('F12',event),
            '<Return>':lambda event:self.ed_key('Enter',event),
            '<BackSpace>':lambda event:self.ed_key('Back',event),
            '<Tab>':lambda event:self.ed_key('Tab',event),
            }
        if sys.version_info[1] >= 12:
            key_map['<ISO_Left_Tab>']= lambda event: self.ed_key('BackTab')
        BaseKeyHandler.__init__(self,page.window,key_map)

    def key(self,event):
        sym=event.keysym
        #print('KEY TYPED on page',event)
        if sym in keypad_map:
            self.error=('Keypad key',sym)
            self.ed_key(keypad_map[sym])
            return 'break'
        c=event.char
        if c=='':
            return 'break'
        self.page._mach.queue_event(KeyEvent('Key',sym,self.page,event))
        return 'break'

    def ed_key(self,key,event):
        #print('ed_key generating KeyEvent as ',key)
        self.page._mach.queue_event(KeyEvent(key,'',self.page,event))

class PythonEditorKeyHandler:
    def __init__(self,editor,canvas):
        self.editor=editor
        self.text_item=editor.text_holder
        self.canvas=canvas #=editor.window
        canvas.bind('<Key>',self.key)
        canvas.bind('<Pause>',lambda event:None)
        canvas.bind('<Escape>',self.esc)
        canvas.bind('<Prior>',self.pg_up),
        canvas.bind('<Next>',self.pg_dn),
        canvas.bind('<End>',self.end),
        canvas.bind('<Home>',self.home)
        canvas.bind('<Left>',self.left)
        canvas.bind('<Up>',self.up)
        canvas.bind('<Right>',self.right)
        canvas.bind('<Down>',self.down)
        canvas.bind('<Print>',self.print)
        canvas.bind('<Insert>',self.ins)
        canvas.bind('<Delete>',self.delete)
        canvas.bind('<Return>',self.enter)
        canvas.bind('<BackSpace>',self.backspace)
        canvas.bind('<Tab>',self.tab)
        if sys.version_info[1]>=12:
            canvas.bind('<ISO_Left_Tab>',self.back_tab)

    def enter(self,event):
        #print('Python editor enter pressed')
        self.text_item.ed_return()
        self.editor.refresh()
        return 'break'

    def key(self,event):
        #print('KEY TYPED on','python editor',event)
        c=event.char
        if c=='':
            return 'break'
        if ctrl(event):
            c=event.keysym
            #print('CTRL',c)
            if c in ('u','z'):
                #print('UNDO')
                self.text_item.command('undo')
            elif c=='c':
                self.text_item.copy_to_clipboard()
            elif c=='v':
                self.text_item.insert_from_clipboard()
            elif c=='x':
                self.text_item.cut_to_clipboard()
        else:
            self.text_item.ed_char(event.char,hex(self.text_item.current_attrib)[-1])
        self.editor.refresh()
        return 'break'

    def left(self,event):
        self.text_item.ed_c_left(ctrl(event),shift(event))
        self.editor.refresh()
        return 'break'

    def right(self,event):
        self.text_item.ed_c_right(ctrl(event),shift(event))
        self.editor.refresh()
        return 'break'

    def up(self,event):
        self.text_item.ed_c_up(shift(event))
        self.editor.refresh()
        return 'break'

    def down(self,event):
        self.text_item.ed_c_down(shift(event))
        self.editor.refresh()
        return 'break'

    def home(self,event):
        self.text_item.ed_c_home(shift(event))
        self.editor.refresh()
        return 'break'

    def end(self,event):
        self.text_item.ed_c_end(shift(event))
        self.editor.refresh()
        return 'break'

    def backspace(self,event):
        self.text_item.ed_backspace()
        self.editor.refresh()
        return 'break'

    def esc(self,event):
        self.editor.button_press('Cancel')
        return 'break'


    def delete(self,event):
        if shift(event):
            self.text_item.cut_to_clipboard()
        else:
            self.text_item.ed_c_del()
        self.editor.refresh()
        return 'break'

    def tab(self,event):
        self.text_item.ed_c_tab()
        self.editor.refresh()
        return 'break'

    def back_tab(self,event):
        self.text_item.ed_c_backtab()
        self.editor.refresh()
        return 'break'

    def undo(self,event):
        self.text_item.command('undo')
        self.editor.refresh()
        return 'break'

    def ins(self,event):
        if shift(event):
            self.text_item.copy_to_clipboard()
            self.editor.refresh()
        return 'break'

    def pg_up(self,event):
        #print('page up')
        return 'break'

    def pg_dn(self,event):
        #print('page dn')
        return 'break'

    def print(self,event):
        #print('print')
        return 'break'



class BubblDiagKeyHandler:
    def __init__(self,diag_editor):
        self.editor=diag_editor
        if diag_editor.name=='main':
            canvas=diag_editor.window
        else:
            canvas=diag_editor.window.frame
        canvas.bind('<Key>',self.key)
        canvas.bind('<Pause>',lambda event:None) #print('pause'))
        canvas.bind('<Escape>',self.esc)
        canvas.bind('<Prior>',self.pg_up),
        canvas.bind('<Next>',self.pg_dn),
        canvas.bind('<End>',self.end),
        canvas.bind('<Home>',self.home)
        canvas.bind('<Left>',self.left)
        canvas.bind('<Up>',self.up)
        canvas.bind('<Right>',self.right)
        canvas.bind('<Down>',self.down)
        canvas.bind('<Print>',self.print)
        canvas.bind('<Insert>',self.ins)
        canvas.bind('<Delete>',self.delete)
        canvas.bind('<F1>',lambda event:self.f_key(event,1))
        canvas.bind('<F2>',lambda event:self.f_key(event,2))
        canvas.bind('<F3>',lambda event:self.f_key(event,3))
        canvas.bind('<F4>',lambda event:self.f_key(event,4))
        canvas.bind('<F5>',lambda event:self.f_key(event,5))
        canvas.bind('<F6>',lambda event:self.f_key(event,6))
        canvas.bind('<F7>',lambda event:self.f_key(event,7))
        canvas.bind('<F8>',lambda event:self.f_key(event,8))
        canvas.bind('<F9>',lambda event:self.f_key(event,9))
        canvas.bind('<F10>',lambda event:self.f_key(event,10))
        canvas.bind('<F11>',lambda event:self.f_key(event,11))
        canvas.bind('<F12>',lambda event:self.f_key(event,12))
        canvas.bind('<Return>',self.enter)
        canvas.bind('<BackSpace>',self.backspace)
        canvas.bind('<Tab>',self.tab)
        if sys.version_info[1]>=12:
            canvas.bind('<ISO_Left_Tab>',self.back_tab)

    def refresh(self):
        if self.editor.active_text_editor is not None:
            self.editor.active_text_editor.refresh()

    def enter(self,event):
        if self.editor.active_text_editor is not None:
            #print('enter pressed')
            self.editor.active_text_editor.ed_return()
            self.refresh()
        else:
            self.editor.entert_key(event)

        return 'break'

    def key(self,event):
        #print('KEY TYPED on',self.editor.name,event)
        c=event.char
        if c=='':
            return 'break'
        if self.editor.active_text_editor is not None:
            if ctrl(event):
                c=event.keysym

                #print('CTRL',c)
                if c in ('u','z'):
                    #print('UNDO')
                    self.editor.active_text_editor.command('undo')
                elif c=='c':
                    self.editor.active_text_editor.copy_to_clipboard()
                elif c=='v':
                    self.editor.active_text_editor.insert_from_clipboard()
                elif c=='x':
                    self.editor.active_text_editor.cut_to_clipboard()
            else:
                self.editor.active_text_editor.ed_char(event.char,hex(self.editor.active_text_editor.current_attrib)[-1])
            self.refresh()
        else:
            self.editor.handle_key(event)
        return 'break'

    def f_key(self,event,number):
        #print(f'F{number} pressed')
        self.editor.f_key(event,number)
        return 'break'

    def left(self,event):
        if self.editor.active_text_editor is not None:
            self.editor.active_text_editor.ed_c_left(ctrl(event),shift(event))
            self.refresh()
        else:
            self.editor.left_key(event)

        return 'break'


    def right(self,event):
        if self.editor.active_text_editor is not None:
            self.editor.active_text_editor.ed_c_right(ctrl(event),shift(event))
            self.refresh()
        else:
            self.editor.right_key(event)
        return 'break'

    def up(self,event):
        if self.editor.active_text_editor is not None:
            self.editor.active_text_editor.ed_c_up(shift(event))
            self.refresh()
        else:
            self.editor.up_key(event)
        return 'break'

    def down(self,event):
        if self.editor.active_text_editor is not None:
            self.editor.active_text_editor.ed_c_down(shift(event))
            self.refresh()
        else:
            self.editor.down_key(event)
        return 'break'

    def home(self,event):
        if self.editor.active_text_editor is not None:
            self.editor.active_text_editor.ed_c_home(shift(event))
            self.refresh()
        else:
            self.editor.home_key(event)
        return 'break'

    def end(self,event):
        if self.editor.active_text_editor is not None:
            self.editor.active_text_editor.ed_c_end(shift(event))
            self.refresh()
        else:
            self.editor.end_key(event)
        return 'break'

    def backspace(self,event):
        if self.editor.active_text_editor is not None:
            self.editor.active_text_editor.ed_backspace()
            self.refresh()
            #self.refresh()
        return 'break'

    def esc(self,event):
        self.editor.esc_pressed()
        self.refresh()
        return 'break'


    def delete(self,event):
        if self.editor.active_text_editor is not None:
            if shift(event):
                self.editor.active_text_editor.cut_to_clipboard()
            else:
                self.editor.active_text_editor.ed_c_del()
        else:
            if shift(event):
                self.editor.cut()
            else:
                self.editor.delete()
        self.refresh()
        return 'break'

    def tab(self,event):
        if self.editor.active_text_editor is not None:
            self.editor.active_text_editor.ed_c_tab()
            self.refresh()
        else:
            self.editor.tab_key(event)
        return 'break'

    def back_tab(self,event):
        if self.editor.active_text_editor is not None:
            self.editor.active_text_editor.ed_c_backtab()
            self.refresh()
        else:
            self.editor.back_tab_key(event)
        return 'break'

    def undo(self,event):
        if self.editor.active_text_editor is not None:
            self.editor.active_text_editor.command('undo')
            self.refresh()
        else:
            self.editor.undo()
        return 'break'

    def ins(self,event):
        if self.editor.active_text_editor is not None:
            if shift(event):
                self.editor.active_text_editor.copy_to_clipboard()
                self.refresh()
        else:
            if shift(event):
                self.editor.ins()
        return 'break'

    def pg_up(self,event):
        #print('page up')
        self.editor.pg_up_key(event)
        return 'break'

    def pg_dn(self,event):
        #print('page dn')
        self.editor.pg_dn_key(event)
        return 'break'

    def print(self,event):
        #print('print')
        return 'break'