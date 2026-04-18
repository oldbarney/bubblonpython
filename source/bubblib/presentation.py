"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from collections import defaultdict

from .machineimports import get_imported_machine_init
from .globaldefs import event_types

'''
block init structure:
{"id_no":int,
 "type":"<block type>",
 "params":[ pars ],
 "pos":[x,y],
 "size":[width,height]
}

_presentation
{
 "title":"<title>",
 "default_init":<default init>,
 "shape":"rect" or "round" or "rhombus",
 "border": style,
 "bgcol":colour,
 "fgcol":colour

 "edlines":...
 "block":block-defn
 }

_presentation['edlines']=
['single',prompt,'button' (,icon) ]
                 'input',[context,...]]
                 'check',
                 'choice',[choice,...]]

['multi',prompt(,field),prefix,add_text]
         [prompt1(,field),prompt2(,field)],add_text]

if add_text is 'Add markup' prefix is markup selection key

'''

assign_presentation = {
    "title": "Assign instruction",
    "default_init": {"params": [['','']], "type": "ASSIGN", "size": [5, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",
    "edlines": [['multi',['Let','='],'Add line']],

    "block": {"colour": "#DD9",
              "linktype": "single",
              "linknames": []
              }
}

if_presentation = {
    "title": "If instruction (make decision)",
    "default_init": {"params": ["True"], "type": "IF", "size": [1, 1], "pos": [0, 0], "links": [0, 0]},
    "shape": "rhombus",
    "edlines": [['single','Expression','input',[]]],
    "block": {"colour": '#E90', "linktype": "if", "linknames": []}
}


link_presentation = {
    "title": "Link instruction (choose exit link)",
    "default_init": {"params": [0], "type": "LINK", "size": [3, 2], "pos": [0, 0], "links": []},
    "shape": "round",
    "edlines": [],
    "block": {"colour": '#E90',
              "linktype": "none",
              "linknames": []
              }
}

wait_presentation = {
    "title": "Wait instruction",
    "default_init": {"params": ['wait'], "type": "WAIT", "size": [5, 1], "pos": [0, 0], "links": []},
    "shape": "round",
    "edlines": [['single','Description','input',[]],
                ['multi','Event','','Add event',event_types]],
    "block": {"colour": "#E90",
              'vertical_sizing':True,
              "linktype": "wait",
              "linknames": [],
              'height_adjust':'wait'
              }
}

dialog_presentation = {
    "title": "Dialog",
    "default_init": {"params": ["",""], "type": "DIALOG", "size": [7, 1], "pos": [0, 0], "links": [0, 0,0]},
    "shape": "rect",

    "edlines": [['single','Definition table','input',['table']],
                ['single','Record/Dict','input',[]],
                ['multi','dialog','markup']],
    "block": {"colour": '#CEF',
              "linktype": "multiple", "linknames": ["Ok","Esc","Event"]
              }
}

editor_presentation = {
    "title": "Editor",
    "default_init": {"params": ["Text",""], "type": "EDITOR", "size": [7, 1], "pos": [0, 0], "links": [0, 0]},
    "shape": "rect",

    "edlines": [['single','Editor-type','choice',['Text','Table']],
                ['single','Variable','input',[]],
                ['multi','editor','markup']],
    "block": {"colour": '#CEF',
              "linktype": "multiple", "linknames": ["Ok","Esc"]
              }
}

def import_presentation(target='',diag='main',link_names=[]):
    return {
    "title": "Imported BUBBL block",
    "default_init":{"params":[target,diag,True],"type":"IMPORT","size":[9,2],"pos":[0,0],"links": [0]},
    "shape":"rect",
    "edlines":[["single","Source file","input",["file"]],
               ["single","Block name","input",["importdiag"]],],
    "block": {"colour": '#FCC',
              "linktype":"single",
              "linknames":[]}
}

def async_presentation(filename='',diagname=''):
    init=get_imported_machine_init(filename)
    try:
        par_names=init["diags"][diagname]["signature"]["params"][1:]
    except:
        par_names=[]
    params=[["single",par_name,"input",[]] for par_name in par_names]
    return {
    "title": "Imported BUBBL block",
    "default_init":{"params":[filename,''],"type":"ASYNC","size":[9,2],"pos":[0,0],"links":[0]},
    "shape":"rect",
    "edlines":[["single","Source file","input",["file"]],
               ["single","Block name","input",["importdiag"]]]+params,
    "block": {"colour": '#FCC',
              "linktype":"single",
              "linknames":[]}
}

write_presentation={
    "title": "Write instruction (output text)",
    "default_init": {"params": [""], "type": "WRITE", "size": [5, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",
    "edlines": [['single','Expression','input',[]],
                ['multi','write','markup']],
    "block": {"colour": '#CEF',
               "linktype": "single", "linknames": []
             }
}

page_presentation= {
        "title": "Page instruction (make or change window)",
        "default_init":{"params": [""], "type": "PAGE", "size": [5, 1], "pos": [0, 0], "links": [0]},
        "shape": "rect",
        "edlines": [['single','Page name','input',[]],
                    ['multi','page','markup']],
        "block": {"colour": '#CFE',
                  "linktype": "single", "linknames": []
        }
}

print_presentation= {
        "title": "Print instruction (send data to printer of PDF file)",
        "default_init":{"params": [""], "type": "PRINT", "size": [5, 2], "pos": [0, 0], "links": [0,0]},
        "shape": "rect",
        "edlines": [['single','Page or other object','input',[]],
                    ['multi','print','markup']],
        "block": {"colour": '#AFE',
                  "linktype": "multiple", "linknames": ["Ok","Fail"]
        }
}

pageUpdate_presentation={
        "title": "Page Update (change window settings)",
        "default_init": {"params": [], "type": "PAGE_UPDATE", "size": [5, 1], "pos": [0, 0], "links": [0]},
        "shape": "rect",
        "edlines": [['multi','page','markup']],
        "block": {"colour": '#CFE',
                  "linktype": "single", "linknames": []
                 }
    }

pageClose_presentation = {
    "title":"Close page",
    "default_init": {"params": [], "type": "PAGE_CLOSE", "size": [5, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",
    "edlines": [],
    "block": {"colour": '#CFE',
              "linktype": "single", "linknames": []
              }
}
pageClear_presentation = {
    "title":"Clear page",
    "default_init": {"params": [], "type": "PAGE_CLEAR", "size": [5, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",
    "edlines": [],
    "block": {"colour": '#CFE',
              "linktype": "single", "linknames": []
              }
}
join_presentation={
    "titl":'Join',
    "shape":"oval",
    "default_init":{"params":[],"type":"JOIN","size":[0,0],"pos":[0,0],"links":[0,0]},
    "edlines":[],
    "block":{"colour":"#888",
             "linktype":"join","linknames":[""]}
}


def loop_presentation(target):
    return {
    "title": "Loop instruction Not editable",
    "default_init":{"params":[],"type":"LOOP","size":[3,1],"pos":[0,0],"links":[target]},
    "shape": "round",
    "edlines": [],
    "block": {
    "colour": '#E90',
        "linktype": "single",
        "linknames": []
    }
    }

delete_presentation = {
    "title": "Delete Table rows instruction",
    "default_init": {"params": ["",""], "type": "DELETE", "size": [7, 2], "pos": [0, 0], "links": [0]},
    "shape": "rect",
    "edlines": [['single','Table-name','input',['table']],
                ['single','Rows (records)','input',[]]],

    "block": {"colour": '#E90',
              "linktype": "single", "linknames": []
              }
}

fileMkDir_presentation = {
    "title": "Make folder",
    "default_init": {"params": [""], "type": "FILE_MKDIR", "size": [7, 1], "pos": [0, 0], "links": [0,0]},
    "shape": "rect",
    "edlines": [['single','Folder-name','input',[]]],
    "block": {"colour": '#F88',
              "linktype": "multiple", "linknames": ['Ok','Fail']
              }
}

create_presentation = {
    "title": "Create Table instruction",
    "default_init": {"params": [""], "type": "CREATE", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",
    "edlines": [['single','Table-name','input',['table']],
                ['multi','Field','','Add field']],
    "block": {"colour": '#E90',
              "linktype": "single", "linknames": []
              }
}

sort_presentation = {
    "title": "Sort Table instruction",
    "default_init": {"params": ["","0"], "type": "SORT", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",
    "edlines": [['single','Table-name','input',['table']],
                ['single','Descending','check'],
                ['multi','Field,field','','Add field']],
    "block": {"colour": '#E90',
              "linktype": "single", "linknames": []
              }
}

destroy_presentation = {
    "title": "Destroy Table instruction",
    "default_init": {"params": [""], "type": "DESTROY", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",
    "edlines": [['single','Table-name','input',['table']]],
    "block": {"colour": '#E90',
              "linktype": "single", "linknames": []
              }
}

select_presentation = {
    "title": "Select from Table instruction",
    "default_init": {"params": ["","","",""], "type": "SELECT", "size": [7, 3], "pos": [0, 0], "links": [0]},
    "shape": "rect",
    "edlines": [['single','Result variable','input',[]],
                ['single','Table-name','input',['table']],
                ['single','Where','input',['field']],
                ['single','Filter','input',[]],
               ],
    "block": {"colour": '#E90',
              "linktype": "single", "linknames": []
              }
}

insert_presentation={
    "title": "Insert into table",
    "default_init":{"params":["",""],"type":"INSERT","size":[7,2], "pos":[0,0],"links":[0]},
    "shape": "rect",
    "edlines":[['single','Table-name','input',['table']],
               ['single','@ Index','input',[]],
               ['multi',['Field name,field','='],'Add field']],
    "block":{"colour":'#E90',
               "linktype":"single","linknames":[]
            }
}

update_presentation={
    "title": "Update rows in table",
    "default_init":{"params":["",""],"type":"UPDATE","size":[7,2], "pos":[0,0],"links":[0]},
    "shape": "rect",
    "edlines":[['single','Table-name','input',['table']],
               ['single','Indices(rows)','input',[]],
               ['multi',['Field/variable name,field','=,field'],'Add field']],
    "block":{"colour":'#E90',
             "linktype":"single","linknames":[]
            }
}

for_presentation = {
    "title": "For instruction (iterate through values)",
    "default_init": {"params": ["", ""], "type": "FOR", "size": [7, 2], "pos": [0, 0], "links": [0, 0]},
    "shape": "rect",
    "edlines": [['single','Variable','input',[]],
                ['single','Set or iterable','input',[]]],
    "block": {"colour": '#E90',
              "linktype": "multiple", "linknames": ["do", "done"]
              }
}

image_presentation = {
    "title": "Image instruction (show image)",
    "default_init": {"params": [""], "type": "IMAGE", "size": [5, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Image reference','input',['image_file']],
                ['multi','image','markup']],

    "block": {"colour": '#CEF',
              "linktype": "single", "linknames": []
              }
}


polygon_presentation = {
    "title": "Polygon instruction (draw polygon)",
    "default_init": {"params": ["",""], "type": "POLYGON", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Horizontals','input',[]],
                ['single','Verticals','input',[]],
                ['multi','polygon','markup']],
"block": {"colour": '#CEF',
            "linktype": "single", "linknames": [""]
              }
}

rectangle_presentation = {
    "title": "Rectangle instruction (draw rectangle)",
    "default_init": {"params": ["0","0"], "type": "RECT", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Width','input',[]],
                ['single','Height','input',[]],
                ['multi','rect','markup']],

    "block": {"colour": '#CEF',
               "linktype": "single", "linknames": [""]
              }
}

button_presentation = {
    "title": "Button widget instruction",
    "default_init": {"params": ["press"], "type": "BUTTON", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Text','input',[]],
                ['multi','button','markup']],
    "block": {"colour": '#CEF',
              "linktype": None, "linknames": None
              }
}

inputdisp_presentation = {
    "title": "Text input widget instruction",
    "default_init": {"params": [""], "type": "INPUTDISP", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Inital value','input',[]],
                ['multi','inputdisp','markup']],
    "block": {"colour": '#CEF',
              "linktype": "single", "linknames": [""]
              }
}

texted_presentation = {
    "title": "Text edit widget instruction",
    "default_init": {"params": [""], "type": "TEXTED", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Inital value','input',[]],
                ['multi','texted','markup']],
    "block": {"colour": '#CEF',
              "linktype": "single", "linknames": [""]
              }
}

checkbox_presentation = {
    "title": "Checkbox widget instruction",
    "default_init": {"params": [""], "type": "CHECKBOX", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Prompt','input',[]],
                ['multi','checkbox','markup']],
    "block": {"colour": '#CEF',
              "linktype": "single", "linknames": [""]
              }
}

radio_presentation = {
    "title": "Radio-group widget instruction",
    "default_init": {"params": [""], "type": "RADIO", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['multi','Item','','Add item'],
                ['multi','radio','markup']],
    "block": {"colour": '#CEF',
              "linktype": "single", "linknames": [""]
              }
}

choiceDisp_presentation = {
    "title": "Choice widget instruction",
    "default_init": {"params": [""], "type": "CHOICEDISP", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Choices','input',[]],
                ['multi','choicedisp','markup']],
    "block": {"colour": '#CEF',
              "linktype": "single", "linknames": [""]
              }
}

scrollbar_presentation = {
    "title": "Scrollbar widget instruction",
    "default_init": {"params": ["0","100"], "type": "SCROLLBAR", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','From-value','input',[]],
                ['single','To-value','input',[]],
                ['multi','scrollbar','markup']],

    "block": {"colour": '#CEF',
              "linktype": "single", "linknames": [""]
              }
}

line_presentation = {
    "title": "Line instruction (draw [poly-]line)",
    "default_init": {"params": ["0","0"], "type": "LINE", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Horizontal(s)','input',[]],
                ['single','Vertical(s)','input',[]],
                ['multi','line','markup']],

    "block": {"colour": '#CEF',
              "linktype": "single", "linknames": [""]
              }
}

ellipse_presentation = {
    "title": "Ellipse instruction (draw ellipse or circle)",
    "default_init": {"params": ["0","0"], "type": "ELLIPSE", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Width','input',[]],
                ['single','Height','input',[]],
                ['multi','ellipse','markup']],

    "block": {"colour": '#CEF',
               "linktype": "single", "linknames": [""]
              }
}

arc_presentation = {
    "title": "Arc instruction (draw pieslice(sector), chord(segment) or arc",
    "default_init": {"params": ["0","0"], "type": "ARC", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Width','input',[]],
                ['single','Height','input',[]],
                ['multi','arc','markup']],

    "block": {"colour": '#CEF',
               "linktype": "single", "linknames": [""]
              }
}

colourMenu_presentation = {
    "title": "Colour-chooser",
    "default_init": {"params": [""], "type": "COLOUR_MENU", "size": [7, 1], "pos": [0, 0], "links": [0,0]},
    "shape": "rect",

    "edlines": [['single','Result','input',[]],
                ['multi','colourmenu','markup']],
    "block": {"colour": '#CEF',
              "linktype": "multiple", "linknames": ["Cancel","Ok"]
              }
}

fileMenu_presentation = {
    "title": "File-chooser",
    "default_init": {"params": [""], "type": "FILE_MENU", "size": [7, 1], "pos": [0, 0], "links": [0,0]},
    "shape": "rect",

    "edlines": [['single','Result','input',[]],
                ['multi','filechooser','markup']],
    "block": {"colour": '#CEF',
               "linktype": "multiple", "linknames": ["Cancel","Ok"]
              }
}

alert_presentation = {
    "title": "Alert",
    "default_init": {"params": ["!"], "type": "ALERT", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Message','input',[]],
                ['multi','alert','markup']],
    "block": {"colour": '#CEF',
               "linktype": "single", "linknames": [""]
              }
}

askUser_presentation = {
    "title": "Ask User",
    "default_init": {"params": [""], "type": "ASK_USER", "size": [7, 1], "pos": [0, 0], "links": [0, 0, 0]},
    "shape": "rect",

    "edlines": [['single','Question','input',[]],
                ['multi','ask','markup']],
    "block": {"colour": '#CEF',
              "linktype": "multiple", "linknames": ["Cancel","No", "Yes"]
              }
}

input_presentation = {
    "title": "Input",
    "default_init": {"params": [""], "type": "INPUT", "size": [7, 1], "pos": [0, 0], "links": [0, 0]},
    "shape": "rect",

    "edlines": [['single','Variable(s)','input',[]],
                ['multi','input','markup']],
    "block": {"colour": '#CEF',
              "linktype": "multiple", "linknames": ["Cancel", "Ok"]
              }
}

choice_presentation = {
    "title": "Choice",
    "default_init": {"params": ["",""], "type": "CHOICE", "size": [7, 2], "pos": [0, 0], "links": [0, 0]},
    "shape": "rect",

    "edlines": [['single','Variable','input',['variable']],
                ['single','Choose from','input',['variable']],
                ['multi','choice','markup']],
    "block": {"colour": '#CEF',
              "linktype": "multiple", "linknames": ["Cancel", "Ok"]
              }
}

table_view_presentation = {
    "title": "Table view",
    "default_init": {"params": ["",0,[0]],  #table name, row No. ['field_widths',[int,...]]
                     "type": "TABLE",
                     "size": [7, 1],
                     "pos": [0, 0],
                     "links": []},
    "shape": "rect",
    "edlines": [['single','Table name','input',['table']],
                ['single','First row','input',[]],
                ['single','Field widths','input',[]],
                ['multi','tableview','markup']],
    "block": {'colour':'#EEF','vertical_sizing':True,'linktype':None,'linknames':None}
}

text_presentation={
    "title": "Text Attributes",
    "default_init": {"params": ["", "FreeMono,10","#000"], "type": "TEXT", "size": [0,0], "pos": [0, 0], "links": []},
    "shape": "none",
    "edlines": [['single','Text (html)','input',[]],
                ['single','Font(,<point size>(,b(,i)))','input',['font']],
                ['single','Colour','input',['colour']],
                ],
    "block": {'colour':None,'linktype':None,'linknames':None}
}

button_presentation={
    "title": "Button widget instruction",
    "default_init": {"params": ["press"], "type": "BUTTON", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Text','input',[]],
                ['multi','button','markup']],
    "block": {"colour": '#CEF',
              "linktype": "single", "linknames": [""]
              }
}


db_variable_presentation={
    "title": "_db Variable viewer",
    "default_init": {"params": [""], "type": "DBVARIABLE", "size": [7, 1],
                     "pos": [0, 0], "links": []},
    "shape": "rect",
    "edlines": [['single', 'Variable name', 'input', ['variable']]],
    "block": {"colour": "#225",
              "vertical_sizing": True,
              "linktype": "none",
              "linknames": []
              }
}


variable_presentation = {
    "title":"Variable viewer",
    "default_init":{"params":[""],"type":"VARIABLE","size":[7,1],"pos":[0,0],"links":[]},
    "shape":"rect",
    "edlines":[['single','Variable name','input',['variable']]],
    "block":{"colour":"#225",
             "vertical_sizing":True,
             "linktype":"none",
             "linknames":[]
            }
}

def call_presentation(target):
    return {
        "title": f"{target}",
        "default_init": {"params": [f'{target}'], "type": "CALL", "size": [5, 1], "pos": [0, 0], "links": [0]},
        "shape": "rect",
        "edlines": [['call',target]],
        "block": {"colour":'#ECA',
                  "linktype": "call",
                  "linknames": []
                  }
    }

interface_presentation={
        "title": "Block Interface",
        "default_init": {"params": [], "type": "INTERFACE", "size": [5, 1], "pos": [0, 0], "links": [0]},
        "shape": "round",
        "interface":True,
        "edlines":[ ['single','Colour','input',['colour']],
                    ['single','Has loop input','check'],
                    ['single','Undoable','check'],
                    ['multi','Parameter','','Add parameter'],
                    ['multi','Link name','linkname','Add link']
                  ],
        #3+len(diag.params)+len(diag.links)
        "block": {"colour":'#FF0',
                  "interface":True,
                  "linktype": "interface", "linknames": ["Start","Loop"],
                'height_adjust':'interface'
        }
    }

python_presentation={
        "title": f"Python",
        "default_init": {"params":[""],"type":"PYTHON","size":[7, 1],"pos":[0,0], "links": [0]},
        "shape": "rect",
        "edlines": [['single','Name','text',[]],
                    ],
        "block": {"colour":'#FF0',
                  "linktype": "python",
                  "linknames": [],
                  "vertical_sizing":True
    }
}

fileSave_presentation = {
    "title": "Save File",
    "default_init": {"params": ["",""], "type": "FILE_SAVE", "size": [7, 2], "pos": [0, 0], "links": [0,0]},
    "shape": "rect",
    "edlines": [['single','What to save','input',[]],
                ['single','File-name','input',['file']]],

    "block": {"colour": '#F88',
              "linktype": "multiple", "linknames": ['Ok','Fail']
             }
}

fileDelete_presentation = {
    "title": "Delete File",
    "default_init": {"params": [""], "type": "FILE_DELETE", "size": [7, 1], "pos": [0, 0], "links": [0,0]},
    "shape": "rect",
    "edlines": [['single','File-name','input',['file']]],
    "block": {"colour": '#F88',
              "linktype": "multiple", "linknames": ['Ok','Fail']
             }
}
fileExec_presentation = {
    "title": "Exec Command",
    "default_init": {"params": ["","0"], "type": "FILE_EXECUTE", "size": [7, 2], "pos": [0, 0], "links": [0,0]},
    "shape": "rect",
    "edlines": [['single','Command','input',[]],
                ['single','Synchronous','check',[]]],
    "block": {"colour": '#F88',
              "linktype": "multiple", "linknames": ['Ok','Fail']
             }
}

play_media_presentation = {
    "title": "Play Media",
    "default_init": {"params": ["","","0"], "type": "PLAY", "size": [7, 2], "pos": [0, 0], "links": [0,0]},
    "shape": "rect",
    "edlines": [['single','Program','input',['media_player']],
                ['single','Media-file','input',['media_file']],
                ['single','Synchronous','check',[]]],
    "block": {"colour": '#F88',
              "linktype": "multiple", "linknames": ['Ok','Fail']
             }
}

fileAppend_presentation = {
    "title": "Save File",
    "default_init": {"params": ["",""], "type": "FILE_APPEND", "size": [7, 2], "pos": [0, 0], "links": [0,0]},
    "shape": "rect",
    "edlines": [['single','What to append','input',[]],
                ['single','File-name','input',['file']],
               ],

    "block": {"colour": '#F88',
              "linktype": "multiple", "linknames": ['Ok','Fail']
             }
}

fileCopy_presentation = {
    "title": "Copy File",
    "default_init": {"params": ["",""], "type": "FILE_COPY", "size": [7, 2], "pos": [0, 0], "links": [0,0]},
    "shape": "rect",
    "edlines": [['single','Source File','input',['file']],
                ['single','Destination File','input',['file']],
               ],

    "block": {"colour": '#F88',
              "linktype": "multiple", "linknames": ['Ok','Fail']
             }
}

fileRename_presentation = {
    "title": "Rename File",
    "default_init": {"params": ["",""], "type": "FILE_RENAME", "size": [7, 2], "pos": [0, 0], "links": [0,0]},
    "shape": "rect",
    "edlines": [['single','Source File','input',['file']],
                ['single','New name','input',[]],
               ],

    "block": {"colour": '#F88',
              "linktype": "multiple", "linknames": ['Ok','Fail']
             }
}
menu_presentation = {
    "title": "Menu",
    "default_init": {"params": [""], "type": "MENU", "size": [7, 2], "pos": [0, 0], "links": [0,0]},
    "shape": "rect",

    "edlines": [['multi','Item','','Add item'],
                ['multi','menu','markup']],
    "block": {"colour": '#CEF',
              "menustylelinks":True,
              "linktype": "menu", "linknames": ["Cancel"],
              'height_adjust':'menu'
              }
}


switch_presentation = {
    "title": "Switch",
    "default_init": {"params": [""], "type": "SWITCH", "size": [7, 1], "pos": [0, 0], "links": [0]},
    "shape": "rect",

    "edlines": [['single','Expression','input',[]],
                ['multi','Case','','Add item'],
               ],
    "block": {"colour": '#E90',
              "menustylelinks":True,
              "linktype": "menu", "linknames": ["Default"]
              }
}

imageView_presentation={
    "title": "Image Attributes",
    "default_init": {"params": [""], "type": "IMAGE_VIEW", "size": [0,0], "pos": [0, 0], "links": []},
    "shape": "rect",
    "edlines": [['single','Image reference','input',['image_file']],
                ['multi','image_view','markup']],
    "block": {"colour":'#000',"linktype":"","linknames":[]}
}

graphic_presentation={  #params=[thing,points,line_width,outline,fill,hl-outline,hl-fill]
    "title": "Graphic Attributes",
    "default_init": {"params": ["line",[0,0,20,20]],
                                 "type": "GRAPHIC", "size": [0,0], "pos": [0, 0], "links":[] },
    "shape": "rect",
    "edlines": [['single','Thing','choice',['line','rect','polygon','ellipse','arc']],
                ['single','Points','input',[]],
                ['multi','graphic','markup']],
    "block": {"colour":'#000',"linktype":"none","linknames":[]}
}

formula_presentation = {
    "title": "Formulas",
    "default_init": {"params": [''], "type": "FORMULA", "size": [7, 2], "pos": [0, 0], "links": []},
    "shape": "rect",
    "edlines": [['multi','Expression','','Add line']],
    "block": {"colour": "#DDE",
              "linktype": "none",
              "linknames": []
              }
}

bubbl_presentation={
    "title": "Run Bubbl program",
    "default_init": {"params": ["BUBBL app",".pbub","_pg.icons['fileexec']","0"], "type": "BUBBL", "size": [5,1], "pos": [0, 0], "links": []},
    "shape": "rect",
    "edlines": [['single','Launcher name','input',[]],
                ['single','Bubbl program file','input',['file']],
                ['single','Icon file','input',['image_file']],
                ['single','Allow multiple','check',[]]
               ],
    "block": {"colour":'#DDE',"executable":True,"linktype":"","linknames":[]}
}

command_presentation={
    "title": "Run program",
    "default_init": {"params": ["OS command","","_pg.icons['fileexec']","0"], "type": "COMMAND", "size": [5,1], "pos": [0, 0], "links": []},
    "shape": "rect",
    "edlines": [['single','Launcher name','input',[]],
                ['single','Command line','input',[]],
                ['single','Icon file','input',['file']],
                ['single','Allow multiple','check',[]]
               ],
    "block": {"colour":'#DDE',"executable":True,"linktype":"","linknames":[]}
}

weblink_presentation={
    "title": "Web Link",
    "default_init": {"params": ["Web link","","_pg.icons['www']"], "type": "WEBLINK", "size": [5,1], "pos": [0, 0], "links": []},
    "shape": "rect",
    "edlines": [['single','Launcher name','input',[]],
                ['single','URL','input',[]],
                ['single','Icon file','input',['image_file']],
                ],
    "block": {"colour":'#DDE',"executable":True,"linktype":"","linknames":[]}
}

const_map={
    'ASSIGN':assign_presentation,
    'IF':if_presentation,
    'WRITE':write_presentation,
    'IMAGE':image_presentation,
    'POLYGON':polygon_presentation,
    'RECT': rectangle_presentation,
    'ELLIPSE': ellipse_presentation,
    'ARC':arc_presentation,
    'PAGE':page_presentation,
    'PAGE_CLEAR':pageClear_presentation,
    'PAGE_CLOSE':pageClose_presentation,
    'PAGE_UPDATE':pageUpdate_presentation,
    'WAIT':wait_presentation,
    'FORMULA':formula_presentation,
    'TABLE':table_view_presentation,
    'TEXT':text_presentation,
    'FOR':for_presentation,
    'INPUT':input_presentation,
    'CREATE':create_presentation,
    'SORT':sort_presentation,
    'INSERT':insert_presentation,
    'DELETE':delete_presentation,
    'DESTROY':destroy_presentation,
    'UPDATE':update_presentation,
    'SELECT':select_presentation,
    'CHOICE':choice_presentation,
    'PRINT':print_presentation,
    'ASK_USER':askUser_presentation,
    'MENU':menu_presentation,
    'ALERT':alert_presentation,
    'FILE_MENU':fileMenu_presentation,
    'COLOUR_MENU':colourMenu_presentation,
    'PYTHON': python_presentation,
    'LINE': line_presentation,
    'FILE_MKDIR' :fileMkDir_presentation,
    'FILE_SAVE': fileSave_presentation,
    'FILE_APPEND':fileAppend_presentation,
    'FILE_DELETE':fileDelete_presentation,
    'FILE_RENAME':fileRename_presentation,
    'FILE_COPY': fileCopy_presentation,
    'FILE_EXECUTE':fileExec_presentation,
    'PLAY':play_media_presentation,
    'SWITCH':switch_presentation,
    'IMAGE_VIEW':imageView_presentation,
    'LINK':link_presentation,
    'BUTTON':button_presentation,
    'SCROLLBAR':scrollbar_presentation,
    'VARIABLE':variable_presentation,
    'DBVARIABLE':db_variable_presentation,
    'JOIN':join_presentation,
    'INTERFACE':interface_presentation,
    'INPUTDISP':inputdisp_presentation,
    'CHECKBOX':checkbox_presentation,
    'RADIO':radio_presentation,
    'DIALOG':dialog_presentation,
    'EDITOR':editor_presentation,
    'CHOICEDISP':choiceDisp_presentation,
    'TEXTED':texted_presentation,
    'WEBLINK':weblink_presentation,
    'COMMAND':command_presentation,
    'BUBBL':bubbl_presentation,
    'GRAPHIC':graphic_presentation,
}

func_map= {
    'ASYNC':async_presentation,
    'CALL':call_presentation,
    'LOOP':loop_presentation,
    'IMPORT':import_presentation,
}

def get_presentation(node_type,*pars):
    try:
        return const_map[node_type]
    except:
        try:
            #print(f'getting presentation for {node_type}, ({par0})')
            return func_map[node_type](*pars)
        except:
            return None

