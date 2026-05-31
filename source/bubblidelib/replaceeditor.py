"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import tkinter as tk

from bubblib.gutils import BubblFont, AutoScrollbar
from bubblib.uiserver import ui
from bubblib.utils import IndexedParams, log
from bubblidelib.blockeditor import BlockEditor


class ReplaceEditor():
    def __init__(self,editor,presenter,find,cased,whole,replace_text=None,undos=[]):
        self.editor=editor
        self.presenter=presenter
        pars=IndexedParams(find,cased,whole,presenter.params)
        no_matches=len(pars)
        self.pars=[pars.row(i) for i in range(len(presenter.params))]
        #print(self.pars)
        self.find=find
        self.undos=undos
        self.replace_text=replace_text
        self.font=BubblFont()
        try:
            self.window=tk.Toplevel(editor.canvas)
        except:
            self.window=tk.Toplevel()

        self.window.grid_rowconfigure(0,weight=1)
        self.window.grid_rowconfigure(1, weight=0)
        self.window.grid_columnconfigure(0,weight=1)

        width = self.font.width('m'*40)
        height= width*3//4
        self.window.geometry(f'{width}x{height}+{max(0,ui.mx()-40)}+{max(0,ui.my()-30)}')


        mt=f'{no_matches} match{"" if no_matches==1 else "es"}'

        if replace_text is not None:
            self.window.title(f'{presenter.node.type_name} block. {mt}. Click to replace with "{self.replace_text}"')
        else:
            self.window.title(f'{presenter.node.type_name} block parameters with {mt} in red')
        self.frame=tk.Frame(self.window)
        self.frame.grid(row=0,column=0,sticky='nsew')
        self.frame.columnconfigure(0,weight=1)
        self.frame.columnconfigure(1, weight=0)

        self.frame.rowconfigure(0,weight=1)
        self.frame.rowconfigure(1,weight=0)

        self.vsb = AutoScrollbar(self.frame, orient=tk.VERTICAL)
        self.vsb.grid(row=0, column=1, sticky='ns')
        self.hsb = AutoScrollbar(self.frame,orient=tk.HORIZONTAL)
        self.hsb.grid(row=1,column=0,sticky='ew')
        self.canvas=tk.Canvas(self.frame,
                              yscrollcommand=self.vsb.set,
                              xscrollcommand=self.hsb.set)
        self.canvas.grid(row=0,column=0,sticky='nsew')

        self.vsb.config(command=self.canvas.yview)
        self.hsb.config(command=self.canvas.xview)

        button_frame=tk.LabelFrame(self.window)
        button_frame.grid(row=1,column=0,sticky='ew')

        tk.Button(button_frame,
                  command=self.ok,
                  text='Ok').grid(row=0,
                                  column=2,
                                  sticky='e')
        if replace_text is not None:
            tk.Button(button_frame,
                  command=self.undo,
                  text='Undo').grid(row=0,column=0,sticky='w')
            tk.Button(button_frame,
                      text='Replace All',
                      command=self.replace_all).grid(row=0,column=1,stick='w')
        button_frame.columnconfigure(0,weight=0)
        button_frame.columnconfigure(1,weight=0)
        button_frame.columnconfigure(2,weight=1)
        self.canvas.bind('<1>',self.mouse_click)
        self.undos.append(None) #Mark
        self.draw()
        #print('before',self.presenter.params)


    def draw(self):
        self.canvas.delete('all')
        for ind,line in enumerate(self.pars):
            x=0
            y=ind*self.font.line_space
            for i,par in enumerate(line):
                if len(par)==1:  #[ , ] etc
                    fill='#888'
                    tags=''
                elif par[1]=='txt':
                    fill='#000'
                    tags='txt',f'ind_{par[2]}_{par[3]}_{i}'
                else:
                    fill='#F33'
                    tags='key',f'ind_{par[2]}_{par[3]}_{i}'
                #print(x,par[0])
                self.canvas.create_text(x,y,text=par[0],fill=fill,tags=tags,
                                        font=self.font.font,anchor='nw')
                x+=self.font.width(par[0])
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        #try:
        #    self.canvas['height']=self.font.line_space*(len(self.pars)+2)
        #except Exception as e:
        #    print('THIS SHOULNT HAPPEN',e)

    def ok(self):
        new_params=IndexedParams.params_from_tag_list_list(self.pars)
        if new_params!=self.presenter.params:
            key=f'{self.editor.diag.name},{self.presenter.node_no}'
            if key in BlockEditor.undo_map:
                undos=BlockEditor.undo_map[key]
            else:
                undos=[]
                BlockEditor.undo_map[key]=undos

            for i,(new_row,row) in enumerate(zip(new_params,self.presenter.params)):
                if new_row!=row:
                    #["upd",(ind,subind|None),data:str]
                    if isinstance(new_row,list):
                        if new_row[0]!=row[0]:
                            undos.append(["upd",(i,0),row[0]])
                            row[0]=new_row[0]
                        if new_row[1]!=row[1]:
                            undos.append(["upd",(i,1),row[1]])
                            row[1]=new_row[1]
                    else:
                        undos.append(["upd",(i,None),row])
                        self.presenter.params[i]=new_row
            self.presenter.refresh()
            if self.presenter.node.links:
                try:
                    self.presenter.node.compile_code()
                except:
                    self.presenter.node.code=self.presenter.node.code_text()
                    self.presenter.node.undoable_code=self.presenter.node.undoable_code_text()



        #print('after',self.presenter.params)

        self.window.destroy()

    def mouse_click(self,event):
        ex,ey=event.x,event.y
        cx,cy=self.canvas.canvasx(ex),self.canvas.canvasy(ey)
        if self.replace_text is None:
            return
        cid_s=self.canvas.find_closest(round(cx),round(cy))
        cid=cid_s[0]
        tags=list(self.canvas.gettags(cid))
        if 'key' in tags:
            for tag in tags:
                if tag.startswith('ind'):
                    tag=tag.split('_')
                    row=int(tag[1])
                    line=self.pars[row]
                    self.replace(line,int(tag[3]))
            self.draw()

    def replace(self,items,index):
        if items[index][0]!=self.replace_text:
            self.undos.append((items[index],items[index][0]))
            items[index][0]=self.replace_text

    def replace_all(self):
        for line in self.pars:
            for par in line:
                log('replace all par',par)
                if len(par)==5 and par[1]=='key':
                    if par[0]!=self.replace_text:
                        self.undos.append((par,par[0]))
                        par[0]=self.replace_text
        self.draw()

    def undo(self):
        while self.undos[-1]!=None:
            items,value=self.undos.pop(-1)
            items[0]=value
        self.draw()



def main():
    root=tk.Tk()
    class D:
        def __init__(self):
            self.name='this'
    class E:
        def __init__(self):
            self.diag=D()
    class N:
        def __init__(self):
            self.links=[0]
        def compile_code(self):
            print('compiling')
    class P:
        def __init__(self,params):
            self.params=params
            self.node=N()
            self.node_no=1

    p=P(["tu","recite","pu","reC.Field","_pg.table[pu[0]].tags",["txt","str(wk_rec)"]])
    ed=ReplaceEditor(E(),p,'rec',False,True,'well I never')

    root.mainloop()


if __name__=='__main__':
    main()