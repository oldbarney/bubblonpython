"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import copy
from tkinter import StringVar

from bubblib.inputbox import InputBox
from bubblib.editorframe import EditorWindow
from bubblib.globaldefs import markup_type_map, dispmarkups, event_types
from bubblib.logger import Logger
from bubblib.mywidgets import PopupMenu, PopupInfo
from bubblib.popupchoice import PopupChoice
from bubblib.uiserver import ui
from bubblib.utils import log


class ParamEdVM:
    def __init__(self, params,link_names,links, undoStack):
        self.params = params
        self.link_names=link_names
        self.undos = undoStack
        self.links=links

    def reset(self):
        self.undos = []

    def delta(self, command, undoable=True):
        '''
            command=["group"]
                    ["endgroup"]
                    ["ins",ind,str or array[str]]
                    ["del",ind]
                    ["upd",(ind,subind|None),data:str]
                    ["swap",ind]
                    ["inslink",ind,val]
                    ["dellink",ind]
                    ["swaplink",ind]
                    ["updlink",ind]
         '''
        cmd = command[0]
        log("block ParamEdVm.delta:",command)
        if cmd == "group":
            if undoable:
                self.undos.append(command)
            return
        elif cmd == "cleargroup":
            i = len(self.undos) - 1
            while i >= 0 and self.undos[i] != "group":
                i -= 1
                if i >= 0:
                    self.undos.pop(i)
            return
        elif cmd == "endgroup":
            if undoable:
                self.undos.append(command)
            return
        p1 = command[1] if len(command) > 1 else None
        p2 = command[2] if len(command) > 2 else None
        p3 = command[3] if len(command) > 3 else None
        p4 = command[4] if len(command) > 4 else None

        if cmd == "ins":
            if undoable:
                if p3 is not None:
                    self.undos.append(["del", p1,p3])
                else:
                    self.undos.append(["del", p1])
            if isinstance(p2,list):
                self.params.insert(p1,[StringVar(None,p2[0]),StringVar(None,p2[1])])
            else:
                self.params.insert(p1,StringVar(None,p2))
                if p3 is not None:
                    self.links.insert(p3,p4)
        elif cmd == "inslink":
            if undoable:
                self.undos.append(["dellink", p1])
            self.link_names.insert(p1,StringVar(None,p2))
        elif cmd == "del":
            if undoable:
                ins_val=self.params[p1]
                if isinstance(ins_val,list):
                    ins_val=[ins_val[0].get(),ins_val[1].get()]
                    self.undos.append(["ins", p1, ins_val])
                else:
                    ins_val=ins_val.get()
                    if p2 is not None:
                        #print('p2',p2,'links',self.links)
                        self.undos.append(['ins',p1,ins_val,p2,self.links[p2]])
                    else:
                        self.undos.append(["ins", p1, ins_val])
            self.params.pop(p1)
            if p2 is not None:
                self.links.pop(p2)
        elif cmd == "dellink":
            if undoable:
                self.undos.append(["inslink", p1, self.link_names[p1].get()])
            self.link_names.pop(p1)
        elif cmd == 'toggleIO':
            if undoable:
                self.undos.append(['togglIO',p1])
            v=self.params[p1]
            if v.get()[:1]=='@':
                v.set(v.get()[1:])
            else:
                v.set('@'+v.get())

        elif cmd == "swap":
            if undoable:
                self.undos.append(command)
            self.params.insert(p1-1, self.params.pop(p1))
            if p2 is not None:
                self.links.insert(p2-1,self.links.pop(p2))
        elif cmd == "swaplink":
            if undoable:
                self.undos.append(command)
            self.link_names.insert(p1, self.link_names.pop(p1 + 1))
        elif cmd == "updlink":
            if undoable:
                self.undos.append(["updlink", p1, self.link_names[p1].get()])
            self.link_names[p1].set(p2)

    def undo(self) -> bool:  # does this handle nested groups properly? I think so
        if self.undos == []:
            return False
        c = self.undos.pop()
        if c[0] == "endgroup":
            while self.undo():
                pass
        elif c[0] == "group":
            return False
        else:
            self.delta(c, False)
            return True



class BlockEditor:
    instances=set()
    undo_map={}

    @classmethod
    def edit_block_params(cls,block,command):
        key=f'{block.diag.name},{block.no}'
        try:
            undos=cls.undo_map[key]
        except KeyError:
            undos=[]
            cls.undo_map[key]=undos
        vm=ParamEdVM(block.params,[],[],undos)
        vm.delta([command],True)


    @classmethod
    def close_all(cls):
        for ed in cls.instances:
            log('closing ed',ed)
            ed.close(remove_tracker=False)
        cls.instances.clear()

    def __init__(self, diag_editor, node, x,y):
        self.diag_editor = diag_editor
        self.block = node
        undo_map_key=f'{diag_editor.diag.name},{node.no}'
        try:
            undos=self.undo_map[undo_map_key]
        except KeyError:
            undos=[]
            self.undo_map[undo_map_key]=undos
        self.is_interface='interface' in node.presentation
        if self.is_interface:
            params,link_names=node.get_params()
            self.params=[]
            for p in params:
                self.params.append(StringVar(None,p))
            self.link_names=[StringVar(None,ln) for ln in link_names]
        else:
            self.params=[]
            for p in self.block.params:
                if isinstance(p,list):
                    self.params.append([StringVar(None,p[0]),StringVar(None,p[1])])
                else:
                    self.params.append(StringVar(None,p))
            self.link_names=None
        if self.block.type_name in ('WAIT','SWITCH','MENU'):
            self.links=list(self.block.links)
            self.link_off={'WAIT':-1,'SWITCH':0,'MENU':1}[self.block.type_name]
        else:
            self.links=None
        self.vm=ParamEdVM(self.params,self.link_names,self.links,undos)
        #self.vm.delta(['group'])

        self.x=x
        self.y=y

        self.defn=self.get_defn()
        #log('defn is',self.defn)
        if isinstance(diag_editor.window,EditorWindow):
            parent=diag_editor.window.frame
        else:
            parent=diag_editor.window

        self.input_box= InputBox(
            parent,x,y,
            self.defn,
            self.button_press,
            tkinter_file_dialog=self.diag_editor.ide.config[
                'tkinterfiledialog'],
            history=self.diag_editor.ide.history,
            resources=self.diag_editor.get_resources(),
            info_key=self.block.type_name
            )
        self.instances.add(self)
        #ui.register_event_receiver(self,'<<inputboxbutton>>',self.button_press,self)
        '''
InputBox defn is {'title':'title',
             'modal':True,
             'rows':[row,..],
             'style':"",
             'changed':func,
             }
    row=[item,....]
    item is {'type':'input','var':key,'weight':<0,1 or 2>,contexts':[]}
            {'type':'choice','var':key,'choices':[choice,..]}
            {'type':'check','var':key}
            {'type':'label','text':text}
            {'type':'button','text':str,'icon':str,'index':int,'prefix':str,'disabled':bool}
            {'type':'radio','var':key}
            {'type':'radio_row','var':key,'choices':[choice,...]}

presentation['edlines']=
['single',prompt,'button' (,icon) ]
                 'input',[context,...]]
                 'check',
                 'choice',[choice,...]]

['multi',prompt,prefix,add_text (,[choice,...]) ]
        ,key,'markup']
         [prompt1,prompt2],add_text]
['call',target]
'''

    def close(self,remove_tracker=True):
        self.input_box.close_window()
        if remove_tracker:
            self.instances.remove(self)

    def get_defn(self):
    #return defn,variable_map
        log(self.block.type_name)
        pres= self.block.presentation
        title=pres['title']
        index=0
        rows=[]
        for spec in pres['edlines']:
            #log('spec',spec)
            if spec[0]=='single':  #['fixed',[items]]
                cols=[]
                prompt=spec[1]
                input_type=spec[2]

                if input_type=='button':
                    icon=spec[3] if len(spec)==4 else None
                    cols.append({'type':'button','text':prompt,'index':0,'icon':icon,'prefix':'','disabled':False})
                else:
                    cols.append({'type':'label','text':prompt})
                    if input_type=='input':
                        cols.append({'type':'input','var':self.params[index],'weight':2,'contexts':spec[3]})
                    elif input_type=='check':
                        cols.append({'type':'check','var':self.params[index]})
                    elif input_type=='choice':
                        cols.append({'type':'choice','var':self.params[index],'choices':spec[3]})
                    index+=1
                rows.append(cols)
            elif spec[0]=='multi':
                first=index
                last=len(self.params)-1
                if isinstance(spec[1],list):
                    prompt1=spec[1][0].split(',')[0]
                    cont1=spec[1][0].split(',')[1:]
                    prompt2 = spec[1][1].split(',')[0]
                    cont2 = spec[1][1].split(',')[1:]
                    while index<len(self.params):
                        cols=[]
                        cols.append({'type':'label','text':prompt1})
                        cols.append({'type':'input','var':self.params[index][0],'weight':1,'contexts':cont1})
                        cols.append({'type':'label','text':prompt2})
                        cols.append({'type':'input','var':self.params[index][1],'weight':2,'contexts':cont2})

                        cols.append({'type':'button','text':'','index':index,'icon':'up','command':'assign:up','disabled':index==first})
                        cols.append({'type':'button','text':'','index':index,'icon':'down','command':'assign:down','disabled':index==last})
                        cols.append({'type':'button','text':'','index':index,'icon':'ins','command':'assign:ins','disabled':False})
                        cols.append({'type':'button','text':'','index':index,'icon':'del','command':'assign:del','disabled':False})
                        index+=1
                        rows.append(cols)
                    rows.append([{'type':'button','text':spec[2],'index':index,'command':'assign:ins','disabled':False}])
                else:
                    prompt=spec[1].split(',')[0]
                    cont=spec[1].split(',')[1:]
                    prefix=spec[2]
                    if prefix=='markup':
                        self.markup_key=prompt
                        add_text='Add markup'
                        choices=None
                    else:
                        add_text=spec[3]
                        if len(spec)==5:
                            choices=spec[4]
                        else:
                            choices=None
                    if prefix=='linkname':
                        bot=0
                        top=len(self.link_names)
                    else:
                        bot=index
                        top=len(self.params)
                        if prefix!='markup':
                            while top>index and isinstance(self.params[top-1],list):
                                top-=1
                    for ind in range(bot,top):
                        cols=[]
                        if choices is not None:
                            cols.append({'type':'label','text':prompt})
                            cols.append({'type':'choice','var':self.params[ind],'choices':choices})
                        elif prefix=='markup':
                            markup=self.params[ind][0].get()
                            if markup=='':
                                cols.append({'type':'label','text':'Markup'})
                                choices=dispmarkups[self.markup_key]
                                mu_var=self.params[ind][0]
                                mu_var.trace_add('write',self.markup_callback)
                                cols.append({'type':'choice','var':self.params[ind][0],'choices':choices})
                            else:
                                cols.append({'type':'label','text':self.params[ind][0].get()})
                                try:
                                    markup_type=markup_type_map[markup]
                                except:
                                    markup_type=''
                                if markup_type=='expr':
                                    cols.append({'type':'input','var':self.params[ind][1],'weight':2,'contexts':[]})
                                elif markup_type in ('colour','font','image_file','file','default','table','fieldname'):
                                    cols.append({'type':'input','var':self.params[ind][1],'weight':2,'contexts':[markup_type]})
                                elif markup_type=='check':
                                    cols.append({'type':'input','var':self.params[ind][1],'weight':2,'contexts':['truefalse']})
                                    #if isinstance(self.params[ind][1],StringVar):
                                    #    self.params[ind][1]=BooleanVar(None,self.params[ind][1].get()=='1')
                                    #cols.append({'type':'choice','var':self.params[ind][1],'choices':['False','True']})
                                    #cols.append({'type':'check','var':self.params[ind][1]})
                                    #log('ADDING CHECK TRACE')
                                    #self.params[ind][1].trace_add('write',self.check_value_callback)
                                elif markup_type.startswith('choice:'):
                                    cols.append({'type':'choice','var':self.params[ind][1],'choices':markup_type[7:].split(',')})
                                else:
                                    log('unrecognised markup type '+markup_type,level=Logger.INFO)
                        else:
                            cols.append({'type':'label','text':prompt})
                            if prefix=='linkname':
                                cols.append({'type':'input','var':self.link_names[ind],'weight':1,'contexts':[]})
                            else:
                                cols.append({'type':'input','var':self.params[ind],'weight':2,'contexts':cont})
                        if add_text=='Add parameter':
                            cols.append({'type':'button','text':'','index':ind,'icon':'io','disabled':False})
                        cols.append({'type':'button','text':'','index':ind,'icon':'up','disabled':ind==bot,'prefix':prefix})
                        cols.append({'type':'button','text':'','index':ind,'icon':'down','disabled':ind==top-1,'prefix':prefix})
                        cols.append({'type':'button','text':'','index':ind,'icon':'ins','disabled':False,'prefix':prefix})
                        cols.append({'type':'button','text':'','index':ind,'icon':'del','disabled':False,'prefix':prefix})
                        rows.append(cols)
                        if prefix!='linkname':
                            index+=1
                    rows.append([{'type':'button','text':add_text,'command':prefix+'ins','index':top,'disabled':False}])
            elif spec[0]=='call':
                title=self.params[0].get()
                try:
                    target=self.diag_editor.bbsm.diags[title]
                    par_names=target.params[1:]
                    while len(self.params)<len(par_names)+1:
                        self.params.append(StringVar(None,''))
                    for index,par in enumerate(par_names):
                        rows.append([{'type':'label','text':par},{'type':'input','var':self.params[index+1],'weight':2,'contexts':[]}])
                except:
                    rows.append([{'type':'label','text':'Non-existant block'}])

        return {'title':title,'modal':False,'style':'','rows':rows}

    def check_value_callback(self,p1,p2,p3):
        log('CHECK',p1,p2,p3)


    def redefine(self):
        self.input_box.reload(self.get_defn(),resources=self.diag_editor.get_resources())

    def markup_callback(self,*args):
        log('markup args is ',*args)
        self.redefine()

    def show_help(self):
        PopupInfo(self.input_box,self.block)

    def button_press(self,command,index):
        #log('BPevent',command,index)
        if command in ('ok','esc'):
            #self.input_box.unbind("<<inputboxbutton>>",self.button_press)
            if self.block.no not in self.diag_editor.presenters:
                log('Block not longer exists when closing editor',level=2)
            else:
                if command=='ok':
                    self.update_block()
                    self.diag_editor.presenters[self.block.no].end_edit(True)
                else:
                    self.diag_editor.presenters[self.block.no].end_edit(False)
            self.close()
            return
        if command=='Undo':
            self.vm.undo()
            self.redefine()
        elif command=='help':
            self.show_help()
            return
        elif command.startswith('linkname'):
            com=command[8:]
            if com=='Undo':
                self.vm.undo()
                self.redefine()
            elif com=='up':
                self.vm.delta(['swaplink',index],True)
                self.redefine()
            elif com=='down':
                self.vm.delta(['swaplink',index+1],True)
                self.redefine()
            elif com in ('ins','Add link'):
                self.vm.delta(['inslink',index,''],True)
                self.redefine()
            elif com=='del':
                self.vm.delta(['dellink',index],True)
                self.redefine()
            else:
                raise Exception('unknown linkname instr:'+com)
            return

        log('ED command',command)
        if command.startswith('assign:'):
            com=command[7:]
            ins_val=['','']
        elif command.startswith('markup'):
            com=command[6:]
            if com=='ins':
                def select(value):
                    if value is not None:
                        self.vm.delta(['ins',index,[value,'']])
                        self.redefine()
                PopupMenu(self.input_box,
                          ui.mx(),
                          ui.my(),
                          dispmarkups[self.markup_key],
                          select)
                return
        else:
            com=command
            ins_val=''
        if com=='Undo':
            self.vm.undo()
            self.redefine()
        elif com=='up':
            if not command.startswith('markup') and self.links is not None:
                self.vm.delta(['swap',index,index+self.link_off])
            else:
                self.vm.delta(['swap',index])
            self.redefine()
        elif com=='down':
            if not command.startswith('markup') and self.links is not None:
                self.vm.delta(['swap',index+1,index+self.link_off+1])
            else:
                self.vm.delta(['swap',index+1])
            self.redefine()
        elif com == 'ins':
            if self.links is not None:
                if self.block.type_name=='WAIT':
                    def select(value):
                        if value is not None:
                            self.vm.delta(['ins',index,event_types[value],
                                           index+self.link_off,0])
                        self.redefine()
                    PopupChoice(self.input_box,
                          ui.mx(),
                          ui.my(),
                          event_types,
                          client_handler=select,
                          length=20)
                    return
                self.vm.delta(['ins',index,ins_val,index+self.link_off,0])
            else:
                self.vm.delta(['ins',index,ins_val])
            self.redefine()
        elif com=='del':
            if not command.startswith('markup') and self.links is not None:
                self.vm.delta(['del',index,index+self.link_off])
            else:
                self.vm.delta(['del',index])
            self.redefine()
        elif com=='io':
            self.vm.delta(['toggleIO',index])
        elif command=='rightclick':
            widget,variable,contexts=index
            widget.insert('insert','hooey')
            #print('RIGHTCLICK',index)
        else:
            raise Exception('unknown instr:'+com)

    def update_block(self):
        log('updating block')
        if self.is_interface:
            self.block.put_params([p.get() for p in self.params],[ln.get() for ln in self.link_names])
            self.diag_editor.ide.edvm.update_calls_to_diag(self.diag_editor.diag)
            self.diag_editor.ide.update_call_block_presenters(self.block.diag)
        else:
            self.block.params.clear()
            for p in self.params:
                if isinstance(p,list):
                    v=p[1].get()
                    if isinstance(v,bool):
                        v='1' if v else '0'
                    self.block.params.append([p[0].get(),v])
                else:
                    v=p.get()
                    if isinstance(v,bool):
                        v='1' if v else '0'
                    self.block.params.append(v)
        if self.links is not None:
            self.block.links[:]=self.links
            try:
                self.block.compile_code()
            except:
                self.block.code=self.block.code_text()
                self.block.undoable_code=self.block.undoable_code_text()
