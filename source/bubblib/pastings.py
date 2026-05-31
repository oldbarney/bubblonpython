"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import os

from .blockfactory import block_factory
from .bubbljson import fromJSON
from .globaldefs import render_defaults
from .simplebubblapp import SimpleBUBBLApp
from .basebubblapp import BaseBUBBLApp
from .utils import quoted


def web_link_text(uri,index=0):
    name=uri.split(':')[-1]
    if name.startswith('//'):
        name=name[2:]
    name=name.split('/')[0]
    result=f'''"{index+1}":{{"params":[{quoted(name)},{quoted(uri)},"_pg.icons['www']"],
  "type":"WEBLINK","pos":[0,{index}],"size":[11,1],"links":[]}}'''
    #print('JSON',result)
    return result

def text_text(text,index=0):
    result= f'''"{index+1}":{{"params":[{quoted(text)},"Helvetica,10","#000"],
  "type":"TEXT","links":[],"size":[11,0],"pos":[0,{index}]}}'''
    #print('JSON',result)
    return result

def bubbl_prog_text(text,index=0):
    name=text.split(':')[-1]
    if name.startswith('//'):
        name=name[2:]
    filepath=name
    name=name.split('.')[0]
    result=f'''"{index+1}":{{"params":[{quoted(name)},{quoted(filepath)},
  "_pg.icons['_pg.icons['fileexec]',"0"],"pos":[0,{index}],"size":[11,1],
  "links":[],"type":"BUBBL"}}'''
    return result

def image_view_text(uri,index=0,icon=True):
    if icon:
        size=f'"size": [{50 / render_defaults.grid},0],'
    else:
        size='"size": [0,0],'
    return f'''"{index+1}":{{"params": ["{uri}"], "type": "IMAGE_VIEW",
    {size}
   "pos": [0, {index*3}], "links": []}}'''

def python_block_text(filename, index=0):
    try:
        BaseBUBBLApp.get_pbub_from_file(filename)
        return f'''"{index+1}":
           {{"params":["{".".join(filename.split(".")[:-1])}",
                       "{filename}","_pg.icons['fileexec']","0"],   
  "type":"BUBBL",
  "pos":[0,{index}],
  "size":[11,1],
  "links":[0]}}'''
    except:
        pass

    def quoted(s):
        return '"'+s.replace('\\n','\\\\n').replace('"','\\"')+'"'

    with open(filename, 'r') as f:
        nl=',\n'
        lines=f.read().splitlines(keepends=False)
    result= f'''"{index+1}":{{"params":["# imported from {filename} "{nl}
{nl.join(quoted(line) for line in lines)}],
  "type":"PYTHON",
  "pos":[0,{index}],
  "size":[25,1],
  "links":[0]}}'''
    #print('PYTHON BLOCK\n',result)
    return result

def is_text_file(text):
    tl=text.lower()
    if text.find('\n')!=-1:
        return False
    if tl.endswith('.txt') or tl.endswith('.json') or tl.find('.')==-1:
        if os.path.isfile(text):
            return True
    return False

def is_node_list(text):
    #print('CHECKING FOR NODE LIST\n',text,"\nEND OF CHECKING")
    try:
        b = fromJSON(text)
        return isinstance(b, dict) and all(
                b[k]["type"] in block_factory for k in b)
    except:
        return False

def is_html(text):
    tl=text.lower()
    if tl.startswith('http://') or tl.startswith('https://'):
        return True
    if tl.endswith('.htm') or tl.endswith('.html'):
        if os.path.isfile(text):
            return True
    return False

def is_image_file(text):
    for ext in ('.jpg', '.jpeg', '.png', '.gif','.bmp'):
        if text.lower().endswith(ext) and os.path.isfile(text):
            return True
    else:
        return False

def is_python_file(text):
    return text.lower().endswith('.py') and os.path.isfile(text)

def is_url_or_file(text):
    if is_html(text):
        return True
    if is_text_file(text):
        return True
    if is_image_file(text) or is_python_file(text):
        return True
    return False


def get_json_for_text_or_list(text):
    """
    :param text: string or list of strings
    :return: JSON representation of NodeHolder for 1 or
        more nodes from the following:
            WEBLINK
            TEXT
            IMAGE_VIEW
            BUBBL
            PYTHON
            Arbitrary node list from JSON 'cut' or 'copied' from Bubbl Diagram

    If text is a list, it is assumed to be a list of URLS
       Web-address urls (HTTP and HTTPS) are put into WEBLINK nodes
       'File://' urls have the prefix stripped are treated as ordinary files.
       Ordinary files are processed according to extension:
          .htm, .html files are put into WEBLINK blocks
          .jpg.png etc are put into IMAGE_VIEW blocks
          .pbub are put into BUBBL blocks
          .py are put into PYTHON blocks
          If the list has a single .txt,.json or no extension filename,
            its contents will be tested for valid JSON for NodeHolder.
          Otherwise files are put into TEXT blocks (or FILE_EXEC blocks ??)

    if text is a string:
        First it is tested for valid JSON for NodeList
        If it has mutliple lines:
            If any line is a valid URL or existing
                file name, it is split into individual lines and processed as
                if it is a list (as above)
            Otherwise it is put into a (multiline) TEXT block
        Otherwise:
            if it is a valid URL or existing filename it is processed
                as a single-element list of URLs as above
            otherwise it is put into a TEXT block

        Second it is tested for being a url or filename
        If it is a valid filename (i.e. represents an existing file),
          it is processed astext file, the contents is tested for
            valin JSON for Node list

    """
    if isinstance(text,list):
        if len(text)==1:
            fn=text[0]
            if fn.lower().startswith('file://'):
                fn=fn[7:]
            if is_text_file(fn):
                try:
                    with open(fn,'r') as f:
                        contents=f.read()
                    if is_node_list(contents):
                        return contents
                    #return '{'+text_text(text.replace('\n','<br />'))+'}' probably not
                except Exception as e:
                    #print(f'failed to read file contents of {fn} :{e}')
                    return f'{{text_text({text[0]})}}'
        blocks=[]
        for i,res in enumerate(text):
            if res.lower().startswith('file://'):
                res=res[7:]

            if is_html(res):
                blocks.append(web_link_text(res,i))
            elif is_image_file(res):
                blocks.append(image_view_text(res,i))
            elif is_python_file(res):
                blocks.append(python_block_text(res,i))
            else:
                blocks.append(text_text(res,i))
        return('{'+',\n'.join(blocks)+'}')

    if is_node_list(text):
        return text

    lines=text.split('\n')
    if len(lines)>1:
        if any(is_url_or_file(line) for line in lines):
            return get_json_for_text_or_list(lines)
        return '{'+text_text(text.replace('\n','<br />'))+'}'
    if is_html(text):
        return '{'+web_link_text(text)+'}'
    elif is_image_file(text):
        return '{'+image_view_text(text)+'}'
    elif is_python_file(text):
        return '{'+python_block_text(text)+'}'
    else:
        return '{'+text_text(text)+'}'