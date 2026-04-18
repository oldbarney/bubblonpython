"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import time
from datetime import datetime
import zipfile

from bubblib.logger import log_level_map
import os
import sys
#sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+os.sep+'bubblib.zip')
if __name__=='__main__':
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import traceback
import keyword
from ast import literal_eval
import math
from pathlib import Path

windows=sys.platform.startswith('win')

def is_venv():
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

log_level=2
runtime_log_level=1

class AffineTransform:
    def __init__(self,*args,rotate=None,cxy=(0,0),scale=None):
        if len(args)==6:
            self.matrix=args
        elif rotate is not None:
            a=rotate*math.pi/180
            s=-math.sin(a)
            c=math.cos(a)
            x,y=cxy
            dx=-c*x+s*y+x
            dy=-c*y-s*x+y
            self.matrix=(c,-s,dx,s,c,dy)
        else:
            self.matrix=(1,0,0,0,1,0)
        if scale is not None:
            self.matrix=[x*scale for x in self.matrix]
    def __str__(self):
        return self.matrix

    def transform(self,*xys):
        a1,b1,c1,a2,b2,c2=self.matrix
        result=[]
        for i in range(0,len(xys),2):
            result.append(a1*xys[i]+b1*xys[i+1]+c1)
            result.append(a2 * xys[i] + b2 * xys[i+1] + c2)
        return result

rel_to_nw={'n':(1, 0),
          'nw':(0,0),
          'ne':(2,0),
          's':(1,2),
          'se':(2,2),
          'sw':(0,2),
          'e':(2,1),
          'w':(0,1),
          'center':(1,1)
           }

def get_anchor_offsets_to_nw(anchor,width,height):
    try:
        dx, dy = rel_to_nw[anchor]
    except KeyError:
        dx,dy=0,0
    return (dx * width) // 2, (dy * height) // 2


def print_log(*args,level=1,runtime=False):
    if runtime:
        c_level=runtime_log_level
    else:
        c_level=log_level

    if level>=c_level:
        print(f'{log_level_map[level]}:{datetime.now().strftime("%Y %b %d %H:%S.%f")[:-3]}:',
              f'{" ".join(str(arg) for arg in args)}')

def set_log_level(level,runtime=False):
    global log_level,runtime_log_level
    if runtime:
        runtime_log_level=level
    else:
        log_level=level

logger_func=print_log

def set_logger_func(func):
    global logger_func
    logger_func=func

runtime_logger_func=print_log

def set_runtime_logger_func(func):
    global runtime_logger_func
    runtime_logger_func=func

def runtime_log(*args,**kwargs):
    runtime_logger_func(*args,**kwargs,runtime=True)

def log(*args,level=1,**kwargs):
    #if threading.current_thread().name=='main_main':
    #    runtime_logger_func('BBSM',*args,level=level,**kwargs)
    #else:
    logger_func(*args,level=level,**kwargs)


def print_(*args,**kwargs):
    log(*args,**kwargs)



def get_resource(filename):
    #print('SYSPATH0',sys.path[0])
    if sys.path[0].endswith('bubblib.zip'):
        try:
            with zipfile.ZipFile(sys.path[0], 'r') as f:
                contents = f.read(filename)
                return contents
        except:
            pass
    try:
        src=(os.path.dirname(os.path.abspath(__file__))+os.sep+filename)
        #print('SRC',src)
        with open(src,'r') as f:
            contents=f.read()
            return contents
    except Exception as e:
        log('Failed to load resource',filename,'from',src,level=3)
        return None


def scaled_kwargs(scale,kwargs):
    result={}
    for k,v in kwargs.items():
        if k=='font':
            try:
                parts=v.split(',')
                parts[1]=f'{int(parts[1])*scale}'
                v=','.join(parts)
            except:
                pass
        elif k in ('clip','points'):
            if v is not None:
                v=[round(float(el)*scale) for el in v]
        elif k in ('x','y','width','height','line_width'):
            v=round(float(v)*scale)
        result[k]=v
    return result



def bounding_box(x,y,width,height,anchor,rotation):
    #return x,y,width,height of bounding box
    if rotation==0:
        return x,y,width,height
    if anchor=='nw':
        cx=x
        cy=y
    elif anchor=='ne':
        cx=x+width
        cy=y
    elif anchor=='sw':
        cx=x
        cy=y+height
    elif anchor=='se':
        cx=x+width
        cy=y+height
    else:
        cx=x+width//2
        cy=y+height//2
    cx=round(cx)
    cy=round(cy)
    a=rotation/180*math.pi
    s=math.sin(a)
    c=math.cos(a)
    x1=round(c*(x-cx)+s*(y-cy))
    y1=round(-s*(x-cx)+c*(y-cy))
    x2=round(c*(x-cx+width)+s*(y-cy+height))
    y2=round(-s*(x-cx+width)+c*(y-cy+height))
    return (min(x1,x2)+cx,min(y1,y2)+cy,abs(x2-x1),abs(y2-y1))

def now():
    return time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())

def home():
    try:
        return str(Path.home().absolute())+os.sep
    except RuntimeError:
        return ''

def desktop():
    try:
        if os.sep=='\\':
            return os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')+os.sep
        return os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')+os.sep
    except:
        return ''

def documents():
    return home()+os.sep+'Documents'

def downloads():
    return home()+os.sep+'Downloads'

def reextensioned(filename,extension):
    parts=filename.split('.')
    if len(parts)==1:
        return filename+'.'+extension
    parts[-1]=extension
    return '.'.join(parts)


def ordered(a,b):
    if a>b:
        return b,a
    return a,b

def quoted(s: str):
    return '"' + f'{s}'.replace('"', '\\"').replace('\n','<br />') + '"'

def try_eval(expr,gl):
    try:
        return eval(expr,gl)
    except:
        return quoted(expr)

def compilable(text):
    #log(f'testing:{text} for compilability')
    try:
        compile(text,'','eval')
    except:
        #log(f'returning>>{quoted(text)}<<')
        return(quoted(text))
    #log(f'returning>>{text}<<')
    return text

def compilable_not_a_tuple(text):
    # Return a compilable interpretation of text
    # which will not compile to a tuple
    #log(f'testing:{text} for compilability')
    if not isinstance(text,str):
        text=f'{text}'
    if ',' in text:
        parts=text.split(',')
        if all (compilable(part) is part for part in parts):
            return quoted(text)
    try:
        compile(text,'','eval')
    except:
        #log(f'returning>>{quoted(text)}<<')

        return(quoted(text))
    #log(f'returning>>{text}<<')
    return text

def is_valid_identifier(text):
    if text.isidentifier():
        return not keyword.iskeyword(text)
    return False

def validated_identifier(text):
    if keyword.iskeyword(text):
        return text+'_'
    return f'{text}'

def is_lvalue(text):
    if is_valid_identifier(text):
        return True
    try:
        compile(text+'=None','','exec')
        return True
    except:
        return False

def get_macroed(text,macros,substitutions):
    result=text
    for macro,sub in zip(macros,substitutions):
        result=result.replace(macro,"("+sub+")")

def get_error_and_line(exc):
    lines=list(traceback.format_exception(None, exc, exc.__traceback__))
    #print('lines',lines)
    try:
        line_no=int(lines[2].split(',')[1].strip().split(' ')[1])

        error=lines[1].split('\n')[0]
    #    log('Error in line',line_no)
    #    log('Error is',error)
        return error,line_no
    except:
        return 'indecipherable error',0

def get_prefixed_substitutions(matches,prefix,expr):
    """Return expression with identifiers prefixed
    #matches is a list of identifiers to be prefixed in expr
    #log(f'matches:{matches}')
    #log(f'expression in :{expr}')
"""
    if prefix in expr:   # Do not prefix if any already prefixed
        return expr

    for fn in matches:
        if fn in expr:
            p=expr.find(fn)
            while p>-1:
                rest=expr[p+len(fn):]
                if (p==0 or not (expr[p-1].isalnum() or expr[p-1]=='_')) and (rest=='' or not (rest[0].isalnum() or rest[0]=='_')):
                    expr=expr[:p]+prefix+fn+rest
                    p=expr.find(fn,p+len(fn)+len(prefix))
                else:
                    p=expr.find(fn,p+len(fn))
    #log(f'expression out :{expr}')
    return expr



html_tags=('<b>','<i>','<mark>','<sub>','<super>','<br />')

bold_attr=0x01
italic_attr=0x02
sub_attr=0x04
super_attr=0x08
mark_attr=0x10

def find_func(key,cased=False,whole=False):
    #return a function(key,string) returning a tuple of
    # indices of key in string
    if not whole:
        if cased:
            def func(string):
                start=string.find(key)
                result=tuple()
                while start!=-1:
                    result+=start,
                    start=string.find(key,start+len(key))
                return result
            return func
        else:
            key=key.lower()
            def func(string):
                string=string.lower()
                start=string.find(key)
                result=tuple()
                while start!=-1:
                    result+=start,
                    start=string.find(key,start+len(key))
                return result
            return func

    if cased:
        prefix_func=lambda x:x
    else:
        prefix_func=lambda x:x.lower()

    def func(string,key=key):
        string=prefix_func(string)
        key=prefix_func(key)
        result=tuple()
        def find_in_str(start):
            p=string.find(key,start)
            if p==-1:
                return -1,None
            if p==0 or not string[p-1].isalnum():
                if (len(string)==p+len(key)
                    or not string[p+len(key)].isalnum()):
                    return p+len(key),p
            return p+len(key),None

        start,ind=find_in_str(0)
        while start!=-1:
            if ind is not None:
                result+=ind,
            start,ind=find_in_str(start+len(key))

        return result
    return func

class IndexedParams:
    def __init__(self,key,cased,whole,params):
        #find instances of key in params:[str] | [[str,str]]

        self.key=key
        func=find_func(key,cased,whole)
        self.params=params
        self.find_map={}
        for i,par in enumerate(params):
            if isinstance(par,str):
                f=func(par)
                if f:
                    self.find_map[(i,None)]=f
            else:
                f=func(par[0])
                if f:
                    self.find_map[(i,0)]=f
                f=func(par[1])
                if f:
                    self.find_map[(i,1)]=f
    def __len__(self):
        #return len(self.find_map)
        if self.find_map:
            return sum(1 for i in self.find_map.items() if len(i)!=1 and i[1]!='txt' )
        return 0

    def row(self,index):
        #return list of tags with
        #tag=['['], [']'] or ['],['] for framing items
        #tag=[key,index,sub-index,pos in list element] for highlighted keys
        #tag=[txt,pos in list element] for non-highlighted text
        #sub-index is None for [str] elements, 0 or 1 for [[str,str]] elements
        result=[['[']]
        pos=0
        line=self.params[index]
        if isinstance(line,str):
            if (index,None) in self.find_map:
                inds=self.find_map[(index,None)]
                while inds:
                    if pos<inds[0]:
                        result.append([line[pos:inds[0]],'txt',index,None,pos])
                        pos=inds[0]
                    result.append([line[pos:pos+len(self.key)],
                                   'key',index,None,pos])
                    pos+=len(self.key)
                    inds=inds[1:]
            if pos<len(line):
                result.append([line[pos:],'txt',index,None,pos])
            result.append([']'])
            return result
        line0,line1=line
        if (index,0) in self.find_map:
            inds=self.find_map[(index,0)]
            while inds:
                if pos<inds[0]:
                    result.append([line0[pos:inds[0]],'txt',index,0,pos])
                    pos=inds[0]
                result.append([line0[pos:pos+len(self.key)],'key',index,0,pos])
                pos+=len(self.key)
                inds=inds[1:]
        if pos<len(line0):
            result.append([line0[pos:],'txt',index,0,pos])
        result.append(['],['])
        pos=0
        if (index,1) in self.find_map:
            inds=self.find_map[(index,1)]
            while inds:
                if pos<inds[0]:
                    result.append([line1[pos:inds[0]],'txt',index,1,pos])
                    pos=inds[0]
                result.append([line1[pos:pos+len(self.key)],'key',index,1,pos])
                pos+=len(self.key)
                inds=inds[1:]
        if pos<len(line1):
            result.append([line1[pos:],'txt',index,1,pos])
        result.append([']'])
        return result

    @staticmethod
    def param_line_from_tag_list(tag_list):
        #log('tag list',tag_list)
        def get_par(tags):
            return ''.join(tag[0] for tag in tags[1:-1])

        if ['],['] in tag_list:
            middle=tag_list.index(['],['])
            return [get_par(tag_list[:middle+1]),
                    get_par(tag_list[middle:])
                    ]
        return get_par(tag_list)
        #log('param_line_from_tag_list:',tag_list,'=',result)

    @staticmethod
    def params_from_tag_list_list(tag_list_list):
        return [IndexedParams.param_line_from_tag_list(tag_list)
                    for tag_list in tag_list_list]

def text_lines_from_html(html):
    return html.split('<br />')



def tabs_altered(tabs,index,new_value,min_space=4):
    if index==len(tabs)-1:
        if new_value<tabs[index-1]+min_space:
            new_value=tabs[index-1]+min_space
    else:
        if new_value<tabs[index-1]+min_space:
            new_value=tabs[index-1]+min_space
        elif new_value>tabs[index+1]-min_space:
            new_value=tabs[index+1]-min_space
    if tabs[index]!=new_value:
        tabs[index]=new_value
        return True
    return False

def split_html(text):  #todo here add support for html entities , eg. &lt; &amp; etc
    '''
    return text,attributes as arrays of string and bitmasks derived from html tags removed from text
    <b> 1
    <i> 2
    <sub> 4
    <super> 8
'''
    def get_line(mask,line):
        def get_tag(text):
            #return front,back,tag or front,'' None
            st=text.find('<')
            if st==-1:
                return text,'',None
            end=text.find('>',st)
            if end==-1:
                return text,'',None
            return text[:st],text[end+1:],text[st+1:end]
        res=''
        resa=''
        front, back, tag = get_tag(line)
        while tag is not None:
            res += front
            resa += f'{mask:1x}' * len(front)
            if tag=='b':
                mask|=bold_attr
            elif tag=='/b':
                mask&=~bold_attr
            elif tag=='i':
                mask|=italic_attr
            elif tag == '/i':
                mask &= ~italic_attr
            elif tag=='sub':
                mask|=sub_attr
            elif tag == '/sub':
                mask &= ~sub_attr
            elif tag=='super':
                mask|=super_attr
            elif tag=='/super':
                mask&=~super_attr
            line=back
            front,back,tag=get_tag(line)
        return mask,res+front,resa+f'{mask:1x}'*len(front)
    reslines=[]
    resattribs=[]
    lines=text.replace('\n','').split('<br />')
    for line in lines:
        mask,string,cattr=get_line(0,line)
        reslines.append(string)
        resattribs.append(cattr)
    return reslines,resattribs


def dequoted(s:str):
    if s.startswith("'") and s.endswith("'") or s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s

def assoc(key,target,default=''):
    try:
        p=(' '+target).index(' '+key)
        target=target[p+len(key):]
        p=(target+' ').index(' ')
        return target[:p].replace('#',' ')
    except:
        return default

def value_from_str(string):
    if not isinstance(string,str):
        return string
    try:
        return literal_eval(string)
    except:
        return string

def get_val_from_kvlist(key,kv_pairs,default):
    #finds val from [(key,val),...]
    for (k,v) in kv_pairs:
        if k==key:
            return value_from_str(v)
    return default

def get_raw_val_from_kvlist(key,kv_pairs,default):
    #finds val from [(key,val),...]
    for (k,v) in kv_pairs:
        if k==key:
            return v
    return default

def get_imports(imports):
    result={"imports":{}}
    code='\n'.join(f'''
import {imp}
imports["{imp}"]={imp}
''' for imp in imports)
    exec(code,{},result)
    return result


def lookup(key,keys):
    #return index of key in sorted keys or None
    top=len(keys)-1
    if top<10:
        try:
            return keys.index(key)
        except IndexError:
            return None
    if key>keys[top]:
        return None
    if key<keys[0]:
        return None
    bot=0
    while top>bot:
        mid=(top+bot)//2
        if key>keys[mid]:
            bot=mid+1
        elif key<keys[mid]:
            top=mid-1
        else:
            return mid
    return None



ubinames=[
'__loader__','__import__','abs', 'any', 'ascii', 'bin', 'breakpoint', 'callable', 'chr', 'compile',
'delattr', 'dir', 'divmod', 'eval', 'exec', 'format', 'getattr', 'globals', 'hasattr', 'hash', 'hex', 'id', 'input', 'isinstance', 'issubclass',
'iter', 'len', 'locals', 'max', 'min', 'next', 'oct', 'ord', 'pow', 'print', 'repr', 'round', 'setattr', 'sorted', 'sum', 'vars', 'None', 'Ellipsis',
'NotImplemented', 'False', 'True', 'bool', 'memoryview', 'bytearray', 'bytes', 'classmethod', 'complex', 'dict', 'enumerate', 'filter', 'float',
'frozenset', 'property', 'int', 'list', 'map', 'object', 'range', 'reversed', 'set', 'slice', 'staticmethod', 'str', 'super', 'tuple', 'type',
'zip', '__debug__', 'BaseException', 'Exception', 'TypeError', 'StopAsyncIteration', 'StopIteration', 'GeneratorExit', 'SystemExit',
'KeyboardInterrupt', 'ImportError', 'ModuleNotFoundError', 'OSError', 'EnvironmentError', 'IOError', 'EOFError', 'RuntimeError', 'RecursionError',
'NotImplementedError', 'NameError', 'UnboundLocalError', 'AttributeError', 'SyntaxError', 'IndentationError', 'TabError', 'LookupError', 'IndexError',
'KeyError', 'ValueError', 'UnicodeError', 'UnicodeEncodeError', 'UnicodeDecodeError', 'UnicodeTranslateError', 'AssertionError', 'ArithmeticError',
'FloatingPointError', 'OverflowError', 'ZeroDivisionError', 'SystemError', 'ReferenceError', 'MemoryError', 'BufferError', 'Warning', 'UserWarning',
'DeprecationWarning', 'PendingDeprecationWarning', 'SyntaxWarning', 'RuntimeWarning', 'FutureWarning', 'ImportWarning', 'UnicodeWarning',
'BytesWarning', 'ResourceWarning', 'ConnectionError', 'BlockingIOError', 'BrokenPipeError', 'ChildProcessError', 'ConnectionAbortedError',
'ConnectionRefusedError', 'ConnectionResetError', 'FileExistsError', 'FileNotFoundError', 'IsADirectoryError', 'NotADirectoryError', 'InterruptedError',
'PermissionError', 'ProcessLookupError', 'TimeoutError', 'open']

"""
with open('mybuiltins.py',"w") as f:
        f.write('my_builtins={\n')
        for n in ubinames:
            f.write(f"'{n}':{n},\n")
        f.write('}\n')
"""
'''
loc=get_imports(["random"])
res={}
exec('result=random.choice(["A","B","C","D"])',loc,res)

log(res)


s=quoted(""""this''""")



p=eval(s)

log(s)
log(p)
'''

#get_prefixed_substitutions(["x"],"_rec.","x+mx-xo")
#print(usable_builtins)
def main():
    t=AffineTransform(rotate=45,cxy=(1,0))
    print('AT',t.transform(1,0,0,0))
    print(compilable_not_a_tuple('this'))
    print(compilable_not_a_tuple('this,that'))
    print(compilable_not_a_tuple('this:that'))
    print(compilable_not_a_tuple("['this','that']"))
    print(compilable_not_a_tuple("a=['this','that']"))
    print(compilable_not_a_tuple('fun(this,that)'))
    print(compilable('"this"'))


if __name__=='__main__':
    main()