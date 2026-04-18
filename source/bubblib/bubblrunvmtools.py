"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import traceback
from io import StringIO, SEEK_SET

from .globaldefs import is_sys_var
from .utils import is_lvalue, compilable, is_valid_identifier, quoted, print_


def assignation_text(lval,expr,target_varnname='_value'):
    #return python source to safely perform assignment,
    #defaulting to expression string if evaluation raises exception
    if lval=='':
        return ''
    lval=lval.strip()
    if not is_lvalue(lval):
        return ""
    if lval.startswith('_db.') and is_lvalue(lval[4:]):
        expl_lval=lval.replace('"',"\"")
        return f"""
try:
    {target_varnname}={compilable(expr)}
except:
    _mach.log('Failed to assign to',{quoted(lval)},level=2)
    {target_varnname}={quoted(expr)}
if {quoted(lval[4:])} in _db.__dict__:
    _mach.add_undo(['varassign',{quoted(lval)},{lval}])
else:
    _mach.add_undo(['explicit',"del {expl_lval}"])
{lval}={target_varnname}
"""
    if is_sys_var(lval):
        return f"""
try:
    {target_varnname}={compilable(expr)}
except:
    _mach.log('ASSIGN Exception',level=2)
    {target_varnname}={quoted(expr)}
try:
    _mach.add_undo(['varassign',"{lval}",{lval}])
    {lval}={target_varnname}
except:
    _mach.log('sys var ASSIGN Exception',e,level=2)
"""
    if is_valid_identifier(lval):
        return f"""
try:
    _mach.add_undo(['varassign',"{lval}",{lval}])
except:
    _mach.add_undo(['vardel',"{lval}"])
try:
    {lval}={compilable(expr)}
except:
    {lval}={quoted(expr)}
"""
    if all(is_valid_identifier(ident) for ident in lval.split(',')):
        undos='\n'.join(f"""
try:
    _mach.add_undo(['varassign',"{ident}",{ident}])
except:
    _mach.add_undo(['vardel',"{ident}"])""" for ident in lval.split(','))
        return f"""
{undos}
try:
    {lval}={compilable(expr)}
except:
    {lval}={[quoted(expr)]*len(lval.split(','))}
"""
    return f"""
try:
    {target_varnname}={compilable(expr)}
except:
    {target_varnname}={quoted(expr)}
try:
    _mach.runvm.value_stack.append(({lval},))
    _mach.add_undo(["explicit",'''{lval}, = _mach.runvm.value_stack.pop()'''])
except:
    pass    #Give up on trying to make things undoable
try:
    {lval}={target_varnname}
except:
    _mach.log('''Failed to Assign to {quoted(lval)}''',Exception("Assignation"),level=2)
"""

def unscrambled_exception(python_exception,diag_name,block_no):
    #
    #Return diag_name,block_no, line_no in source code where exception occurred,
    #   Return:
    #     Exception name,
    #     [(filename,text,line_no,col_no,length)] in bottom to top stack order
    #
    #      List of:
    #         File-name, line_no, source line and  '^^^^..' back through
    #         causation stack.  todo Investigate lack of '^^^^..' for tkinter canvas tag_bind _bind

    exception=python_exception.exception
    data = StringIO()
    traceback.print_tb(exception.__traceback__, file=data)
    data.seek(0, SEEK_SET)
    strs = data.read().splitlines()
    sections=[]

    for i,s in enumerate(strs):
        if s.startswith('  File "'):
            s = s.strip()

            #print('file line',i)
            try:
                fn,ln,func=s.split(',')
                fn=fn[6:-1].strip()
                ln=int(ln[5:])
                func=func[4:].strip()
                sections.append([[fn,ln,func]])
            except Exception as e:
                print_(traceback.extract_tb(e.__traceback__))
                pass
        assert len(sections)>0
        sections[-1].append(s)
    summary_frames = traceback.extract_tb(exception.__traceback__)
    print_('UNSCRAMBLED CODE TEXT\n',python_exception.code_text,'\n------------')
    code_text = python_exception.code_text.split('\n')

    result=[]
    for i,fs in enumerate(summary_frames):
        if sections[i][0][0] in ('_BLOCK_','_UBLOCK_',
                              '_AUX_BLOCK_',
                              '_UAUX_BLOCK_'):
            ln=fs.lineno#-2
            nm=sections[i][0][2]

            lines=[f'{diag_name} node:{block_no} line:{ln}'+
                          (f' in {nm}' if nm!='<module>' else ''),
                   code_text[ln-1],
                   ' ' * (fs.colno) + '^' * (fs.end_colno - fs.colno)]

            result.append((sections[i][0][0],
                           '\n'.join(lines),
                          ln,
                          fs.colno,
                          fs.end_colno-fs.colno))

        else:
            result.append((sections[i][0][0],
                           '\n'.join(sections[i][1:]),
                           fs.lineno,
                           fs.colno,
                           fs.end_colno-fs.colno))

    return  (f'{exception.__class__.__name__} {exception}',
             list(reversed(result)))