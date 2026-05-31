"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import os

from bubblib.bubbljson import fromJSON
from bubblib.bubblmach import BBSM
from bubblib.globaldefs import ExState
from bubblib.gutils import BubblFont
from bubblib.table import Table
from bubblib.utils import log, get_resource


class Dialog:
    #field_specs=['Label','Thing','X:int','Y:int',
    #             'W:int','H:int','Fill','Colour',
    #             'Align','Field','Font','Params']
    #field_names=['Label','Thing','X','Y',
    #             'W','H','Fill','Colour',
    #             'Align','Field','Font','Params']
    def __init__(self,table,fields:dict,callback):
        self.callback=callback
        self.table=table
        self.fields=dict(fields)

        #init = fromJSON(get_resource('bubblutils.pbub'))
        #init=init['machines']['main']
        init=BBSM.sys_init()
        self.mach=BBSM(self,'d_ed',init,external_db=False)
        self.mach.machine_state_changed.connect(self.mach_state_changed)
        self.mach.database[self.table.table_name]=self.table
        self.mach.diags['dialogrunner'].variables['table']=self.table.table_name
        self.mach.diags['dialogrunner'].variables['record']=self.fields
        self.mach.diags['dialogrunner'].variables['x']=None
        self.mach.diags['dialogrunner'].variables['y']=None
        self.mach.command('goto','dialogrunner',1)
        self.mach.command('run')

    def mach_state_changed(self):
        log('dialogrunner mach_state_changed',repr(self.mach.state))
        if self.mach.state==ExState.stopped_on_link:
            self.mach.machine_state_changed.disconnect(self.mach_state_changed)
            if self.mach.diags['dialogrunner'].variables['result']=='Ok':
                self.callback(self.fields)
            else:
                self.callback(None)
            self.mach.command('kill')

            #uiserver.ui.root.after(0, self.mach.command('kill'))
            log('Dialog runner machine told to die')
            #self.mach.thr.join()
            self.mach=None

def popup_input(title,x,y,prompt,client_callback,default=''):
    log('popup_input xy',x,y)
    result={'value':default}
    def callback(value):
        log('popup_input_callback>{value}<')
        if value is None:
            client_callback(None)
        else:
            client_callback(value['value'])
    table=Table('dialog',field_names=['Label','Thing','X','Y',
                 'W','H','Fill','Colour',
                 'Align','Field','Font','Params'])
    table.insert_row(-1,[title,"win",x,y,311,40,"#FFF","#000","","","sanserif,10","autoexit"])
    table.insert_row(-1,[prompt,"inputline",BubblFont("sanserif,10").width(prompt)+6,15,164,30,"#8FF","#000","TLR","value","sanserif,10",""])
    table.insert_row(-1,["Ok","ok",265,6,30,30,"#FFF","#000","Tl","","sanserif,10",""])
    Dialog(table,result,callback)

def popup_editor(x,y,json_text,client_callback,values):
    table=fromJSON(json_text)
    table[0].X=x
    table[0].Y=y
    Dialog(table,values,client_callback)

def popup_line_settings(x,y,client_callback,values):
    json_text="""{"_table":{"defaults":["","",0,0,0,0,"","","","","",""],
"fieldnames":["Label:none","Thing:none","X:int","Y:int","W:int","H:int","Fill:none","Colour:none","Align:none","Field:none",
  "Font:none","Params:none"],
"name":"",
"rows":[["Line drawing settings","win",0,0,252,226,"#FFF","#000","","","sanserif,10",""],
  ["Line width:    ","inputline",96,13,69,30,"#8FF","#000","TLR","width","sanserif,10",""],
  ["Ok","ok",201,187,30,30,"#FFF","#000","Tl","","sanserif,10",""],
  ["","radio",95,41,30,30,"#FFF","#000","TL","ends","sanserif,10","Round,Butt,Projecting"],
  ["Line ends:","label",16,71,30,30,"#FFF","#000","TL","","sanserif,10",""],
  ["","radio",96,134,30,30,"#FFF","#000","","joins","sanserif,10","Round,Mitre,Bevel"],
  ["Line joins:","label",19,160,30,30,"#FFF","#000","","","sanserif,10",""]]}}"""
    popup_editor(x,y,json_text,client_callback,values)

def popup_config_editor(x,y,client_callback,values):
    json_text="""{"_table":{"defaults":["","",0,0,0,0,"","","","","",""],
"fieldnames":["Label:none","Thing:none","X:int","Y:int","W:int","H:int","Fill:none","Colour:none","Align:none","Field:none",
  "Font:none","Params:none"],
"name":"table_4",
"rows":[["Configuration Editor","win",0,1,500,280,"#FFF","#000","","","sanserif,10",""],
  ["Ok","ok",430,239,30,30,"#CCC","#000","tl","","sanserif,10",""],
  ["Cancel","esc",12,238,30,30,"#CCC","#000","tL","","sanserif,10",""],
  ["Diagram display scale","radio",315,16,30,30,"#FFF","#000","TL","scale","sanserif,10","tiny,small,normal,large,huge"],
  ["Use tkinter file dialog","check",307,190,30,30,"#FFF","#000","TL","tkinterfiledialog","sanserif,10",""],
  ["Debug to STDOUT","check",20,190,30,30,"#FFF","#000","TL","debugtostdout","sanserif,10",""],
  ["Select this for system file","label",314,161,30,30,"#FFF","#000","","","sanserif,10",""],
  ["dialog on  Windows","label",315,176,30,30,"#FFF","#000","","","sanserif,10",""],
  ["App Log level","radio",164,13,60,27,"#FFF","#000","","loglevel","sanserif,10",
  "Debug,Info,Warning,Error,Runtime error,Fatal"],
  ["IDE Log level","radio",15,12,60,27,"#FFF","#000","","ideloglevel","sanserif,10",
  "Debug,Info,Warning,Error,Runtime error,Fatal"]]}}"""
    popup_editor(x,y,json_text,client_callback,values)