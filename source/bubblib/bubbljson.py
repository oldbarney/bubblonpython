"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import json
import types

from bubblib.gutils import BUBBLImage, get_image
from bubblib.iset import Iset
from bubblib.utils import log, print_

if __name__=='__main__':
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .table import Table, RawTable, AbstractRow, row_factory

'''
  bubblDiag JSON data structure
  val: integer|
       number|
       "string"|
       {"intset":[[int,int,...],[int,int,...]]}|
       [val,val...]|
       {"table":{"fieldnames":[str,str...],"rows":[[val,val...],[val,val...],...]}
       {dict} 
  persistent variables data structure
  diag 
    {"signature"::{"params":[],"linknames":[],"start":0,"loop":0,undoable:True}
     "vars":{"vname":val,...}
     "nodes":{"no":{"type":str, "params":[],"links":[],"pos":[int,int],"size:[int,int]},...}
     "imports":[]
    }
  machine
    {"main":diag, ... }
  App
    {"main":machine, ...}
'''

def jsonable(v,debug=False):
    if isinstance(v, (str, int, float, complex,range, bool, Iset,BUBBLImage)):
        return True
    if v is None:
        return True
    if debug:
        log(f'JSONABLE debug',v,level=2)
    if isinstance(v, list):
        if debug:
            for i,el in enumerate(v):
                if not jsonable(el,True):
                    log(f'Not JSONABLE list el[{i}]={el}',level=2)
                    return False
            return True
        return all(jsonable(i) for i in v)
    if isinstance(v, dict):
        if debug:
            for k in v:
                #if not isinstance(k,str):
                #    log(f'Not JSONABLE dict key:{k}',level=2)
                #    return False
                if not jsonable(v[k],True):
                    log(f'Not JSONABLE dict entry:{k}:{v[k]}',level=2)
                    return False
            return True
        return all(jsonable(v[k]) for k in v) #note all keys converted to strings
        #return all(isinstance(k,str) and jsonable(v[k]) for k in v)
    if isinstance(v,set):
        return all(jsonable(el) for el in v)

    if isinstance(v, RawTable):
        if debug:
            for i,row in enumerate(v):
                l=row.get_list()
                if not jsonable(l,True):
                    log(f'Not JSONABLE table row[{i}]={l}',level=2)
                    return False
            return True
        return all(jsonable(row.get_list()) for row in v)
    if isinstance(v, GlobalDatabase):
        return True
    if debug:
        log(f'Not JSONABLE unrecognised type:{v}',level=2)
    return False

class GlobalDatabase(types.SimpleNamespace):
    """_db
    This system variable allows access to 'global' variables.
    Variables assigned in this namespace are directly accessible to all
    diagrams/blocks in the application.  These are not the same as Python
    'global' declarations, and are accessed via this system variable.

    Variables can be accessed either by dot notation, or 'index' notation
        e.g.
            _db.my_global="Hello"
            print(_db["my_global"])  # print("Hello")

    Like normal module-based variables, these variables are considered
    'persistent' and are saved to a database file on program exit and
    initialised from the database on program loading.

    Variables whose names start with an underscore are not considered
    'persistent' and will not be saved on program exit. The exceptions to
    this rule are the tables '_config' and '_history' which contain
    configuration data and user input history respectively.

    <h4>Tables</h4>
    The table 'create','destroy','insert','delete','update' and 'sort' blocks
    work on tables in this global name-space. Tables behave like lists  of
    named tuples and can also be accessed directly through this namespace.

        e.g:
            print(_db.my_table[0])
            _db.my_table[2].Name="bill"
            person=_db["my_table"][index].Name

    The table select and update blocks use expressions.

    Where local variable names and field-names 'collide', all field
    names can be prefixed with '_rec.' to distiguish them from the
    local variables.

    Also the variable '_rn' refers to the index of the currently
    tested/updated row, allowing expressions to refer to relative
    table rows.

    Tables have the following attributes:

    Attribute       Description
    ---------       -----------
    field_names     A list of the table's field names
    field_types     A list of the table's field types (see above) corresponding
                    to the field names
    defaults        A list of default values for 'insert' blocks corresponding
                    to the field names
    rows_matching(field,value,match_func=None)
                    A method returning a list of row numbers whose fields
                    match 'value' (match_func defaults to: lambda a,b:a==b).
    to_csv()        A string of 'new line' separated csv representations of
                    the table's rows
    to_html()       An html table element representation of the table
    table_name      The table's name
    all_records()   A range object spanning the table's row numbers -equivalent
                    to 'range(len(table))'

    Additional Indexing Features:

    Index-type   Returned value
    ----------    --------------
    slice        A copy of the table with the rows indexed by the slice
    list of ints A copy of the table with the rows indexed by the list
    set of ints  A copy of the table with the rows indexed by the set elements
    _Iset        A copy of the table with the rows indexed by the _Iset elements
    str: &lt;field&gt;==&lt;value&gt;
                 The first record in the table with a matching field or None

    Note: Indexing of tables is 'read only'.
          Assignments such as (e.g.) _db.mytable[0]=[1,2,3] are not allowed
    """

    def __init__(self,**initialisation):
        types.SimpleNamespace.__init__(self)
        for k in initialisation:
            self[k]=initialisation[k]

    def __getitem__(self, key):
        return getattr(self,key,None)

    def __setitem__(self, key, value):
        if isinstance(key, str):
            setattr(self,key,value)

    def __delitem__(self,key):
        delattr(self,key)

    def __iter__(self):
        self._list=[attr for attr in dir(self) if (
            (not attr.startswith('_')
             and jsonable(getattr(self,attr))
             )or
            attr in ('_config','_history'))]
        return self

    def __next__(self):
        try:
            return self._list.pop(0)
        except:
            raise StopIteration
    def __len__(self):
        return len([attr for attr in dir(self) if  (
            not attr.startswith('_') or
            attr in ('_config','_history'))])


def forced_indent(data,indent):
    items=data.split('\n')
    return items[0]+'\n'+'\n'.join((indent+item) for item in items[1:])

def chunked_list(data,indent,max_len=120):  #data is list with no n/l
    result=data[0]
    cum=len(result)
    for el in data[1:]:
        cum=cum+len(el)
        if cum<max_len:
            result+=','+el
            cum+=1
        else:
            result+=',\n'+indent+el
            cum=len(el)
    return result

def toJSON(data,indent='',pad='  ',max_len=120):
    nl='\n'
    if  isinstance(data,Iset):
        return toJSON({"_Iset":[data.ins,data.outs]},indent,pad,max_len)
    elif isinstance(data, Table):
        return toJSON({"_table":{
            "fieldnames":data.field_specs(),
            "defaults":data.defaults,
            "rows":[row.get_list() for row in data._data],
            "name":data.table_name}},indent,pad,max_len)
    elif isinstance(data,AbstractRow):
        return toJSON({"_table_row":[list(data.__slots__),[getattr(data,field) for field in data.__slots__]]})
    elif isinstance(data,BUBBLImage):
        return toJSON({"_png_image":data.to_base64()})
    elif isinstance(data, (list,tuple)):
        if data==[]:
            return indent+'[]'
        if data == tuple():
            return indent+'[]'
        contents=[toJSON(el,'',pad,max_len) for el in data]
        #print('contents1',contents,'end of contents1')
        if any(nl in el for el in contents):
            #print('found nl')
            return indent+'['+f',{nl}{indent}{pad}'.join(el for el in contents)+']'
        line=",".join(contents)
        #print('line is ',line,'end of line')
        if len(line)>max_len:
            return '['+chunked_list(contents,indent+pad,max_len)+']'
        return f'{indent}[{line}]'
    elif isinstance(data, dict):
        keys=[(f'{k}'.replace('"','\\"'),k) for k in data]
        keys.sort()
        if keys==[]:
            return indent+'{}'
        result=(f'{keys[0][0]}":').replace('\\','\\\\')
        el1=toJSON(data[keys[0][1]],'',pad,max_len)
        if nl in el1:
            el1=forced_indent(el1,indent+pad)
        result+=el1
        if len(keys)==1:
            return indent+'{"'+result+'}'
        else:
            result=indent+'{"'+result
        for key in keys[1:]:
            result+=f',\n{indent+pad}"{key[0]}":'
            eln=toJSON(data[key[1]],'',pad,max_len)
            if nl in eln:
                eln=forced_indent(eln,indent+pad)
            result+=eln
        return result+'}'
    elif isinstance(data,complex):
        return f'{indent}{{"_complex":[{data.real},{data.imag}]}}'
    elif isinstance(data,range):
        return f'{indent}{{"_range":[{data.start},{data.stop},{data.step}]}}'
    elif isinstance(data,set):
        return f'{{"_set":{toJSON(list(data))}}}'
    elif isinstance(data, GlobalDatabase):
        contents={key:data[key] for key in data if (
                    not key.startswith('_') or
                    key in ('_config','_history'))
                  }
        return f'{{"_namespace":{toJSON(contents)}}}'
    else:
        #print(f'returning json.dumps>>{json.dumps(data)}<<')
        try:
            return indent+json.dumps(data)
        except Exception as e:
            #print(f'Attempt to JSONise \n{data}\n failed with {e}')
            return f'"{type(data)}"'

def bubblFromStruct(struct):
    if isinstance(struct, dict):
        if len(struct) == 1:
            #print('len struct 1')
            key=list(struct)[0]
            if key=='_Iset':
                try:
                    result=Iset()
                    result.ins[:],result.outs[:] = struct['_Iset']
                    return result
                except Exception as e:
                    log('BAD _Iset in JSON',e,level=2)
            elif key=='_table':
                try:
                    contents = struct['_table']
                    fns = contents['fieldnames']
                    defaults = contents['defaults']
                    try:
                        name = contents['name']
                    except:
                        name=''
                    result = Table(name,fns,defaults)
                    rows = contents['rows']
                    for row in rows:
                        result.insert_row(-1,result.Row(bubblFromStruct(row)))
                    return result
                except Exception as e:
                    log('BAD _table in JSON',e,level=2)
            elif key=='_complex':
                try:
                    components=struct['_complex']
                    return complex(float(components[0]),float(components[1]))
                except Exception as e:
                    log('BAD _complex in JSON',e,level=2)
            elif key=='_range':
                try:
                    [start,stop,step]=struct["_range"]
                    return range(int(start),int(stop),int(step))
                except Exception as e:
                    log('BAD _range in JSON',e,level=2)
            elif key=='_set':
                try:
                    return set(fromJSON(struct["_set"]))
                except Exception as e:
                    log('BAD _set in JSON',e,level=2)

            elif key=='_table_row':
                try:
                    fieldnames,values=struct['_table_row']
                    return row_factory(fieldnames,[bubblFromStruct(value) for value in values])
                except Exception as e:
                    log('BAD _table_row in JSON',e,level=2)
            elif key=='_png_image':
                try:
                    data=struct['_png_image']
                    return get_image(hash(data),base64_data=data)
                except:
                    log('BAD PNG image data',level=2)
            elif key=='_namespace':
                return GlobalDatabase(**struct['_namespace'])

        return {el: bubblFromStruct(struct[el]) for el in struct}
    elif isinstance(struct, list):
        return [bubblFromStruct(el) for el in struct]
    else:
        return struct

def fromJSON(text):
    # print(f"{text}")
    result = json.loads(text)
    # return result
    return bubblFromStruct(result)

def main():
    #print(chunked_list(['a','b','c']+[f'{i}' for i in range(500)],'',maxlen=50))
    #print(toJSON({'a':[i for i in range(100)]}))
    print_(toJSON({"params":[""],"type":"VARIABLE","size":[7,1],"pos":[0,0],"links":[]}))
    #print(toJSON({'kEy':[f'{i}' for i in range(100,500)],'key2':'just a string','key3':{'subkey1':43,'subkey2':[i for i in range(200)]}},'     ','   ',50))

    print_(fromJSON("""{"_table":{"defaults":["","",0,0,0,0,"","","","","",""],
            "fieldnames":["Label:none","Thing:none","X:int","Y:int","W:int","H:int","Fill:none","Colour:none","Align:none","Field:none",
              "Font:none","Params:none"],
            "name":"",
            "rows":[["Line drawing settings","win",0,0,252,226,"#FFF","#000","","","sanserif,10",""],
              ["Line width:    ","inputline",96,13,69,30,"#8FF","#000","TLR","width","sanserif,10",""],
              ["Ok","ok",201,187,30,30,"#FFF","#000","Tl","","sanserif,10",""],
              ["Round,Butt,Projected","radio",95,41,30,30,"#FFF","#000","TL","ends","sanserif,10",""],
              ["Line ends:","label",16,71,30,30,"#FFF","#000","TL","","sanserif,10",""],
              ["Round,Mitre,Bevel","radio",96,134,30,30,"#FFF","#000","","joins","sanserif,10",""],
              ["Line joins:","label",19,160,30,30,"#FFF","#000","","","sanserif,10",""]]}}"""))

if __name__=='__main__':
    main()