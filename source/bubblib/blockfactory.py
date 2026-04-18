"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import sys
from .block import Block, ExecutableBlock
from .globaldefs import dispmarkups, ExState, PythonBlockException
from .presentation import *
from .utils import compilable, compilable_not_a_tuple, quoted, is_lvalue, \
    is_valid_identifier, log
from .bubblrunvmtools import assignation_text

def markups_dict(kv_pairs):
    def mu(pair):
        return f'''try:
    _val={compilable_not_a_tuple(pair[1])}
except:
    _val={quoted(f'{pair[1]}')}
_dict[{quoted(pair[0].replace(' ','_'))}]=_val
'''
    mus='\n'.join(mu(pair) for pair in kv_pairs)
    result=f'''_dict={{}}
{mus}
'''
    return result

class LoopBlock(ExecutableBlock):
    """Complete a loop
The 'Loop' block, in combination with a 'For' block or 'BBSM'
block allows a section of a program to be automatically run
multiple times.

This block should be linked to at the end of the repeated
section where it lets the 'For' block or 'BBSM' block know
where the looped section ends.
"""
    def __init__(self, diag, no, init=None, target=None):
        super().__init__(diag, no, init, loop_presentation(target))

    def code_text(self):
        return self.diag.nodes[self.links[0]].auxcode_text()

    def undoable_code_text(self):
        return self.diag.nodes[self.links[0]].undoable_auxcode_text()

    def auxcode_text(self):
        return self.code_text()

    def undoable_auxcode_text(self):
        return self.undoable_code_text()

class CreateBlock(ExecutableBlock):
    """Create a table object.

This block creates a table with named fields.
Fields can be 'typed' by appending ':<type name>' to
the field name where <type name> is one of:
    int
    float
    complex
    num
    str
    choice
    set

Tables can be searched, updated, sorted; have records added
or removed; or be destroyed using the other table blocks ('Select',
'Update', 'Sort', 'Insert', 'Delete' and 'Destroy').
Tables also appear in the global database (_db) where they
can be directly accessed as (eg) _db.<table-name> or _db["table_name"].
Table rows are numbered from zero and can also be directly accessed
by indexing the table. E.g.  row=_db.my_table[0]
Iterating over a table returns the rows (records) in order

"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, create_presentation)

    def code_text(self):
        return f"""
try:
    _tn={compilable(self.params[0])}
except:
    _tn={quoted(self.params[0])}
try:
    _mach.create_table(_tn,{self.params[1:]},False)
except:
    pass
_mach.node={self.links[0]}
_mach.link=0
"""
    def undoable_code_text(self):
        return f"""
try:
    _tn={compilable(self.params[0])}
except:
    _tn={quoted(self.params[0])}
try:
    _mach.create_table(_tn,{self.params[1:]},True)
except:
    pass
_mach.node={self.links[0]}
_mach.link=0
"""


class SortBlock(ExecutableBlock):
    """Sort a table object.
This block sorts a table.
Sorting is on one or more fields and can be ascending or descending.
Sorting on fieldnames appended with ':cased' will be case-sensitve.
"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, sort_presentation)

    def code_text(self):
        return f"""
try:
    _mach.sort_table({compilable(self.params[0])},
                     {self.params[2:]},
                     {self.params[1]=='1'},False)
except:
    _mach.sort_table({quoted(self.params[0])},
                     {self.params[2:]},
                     {self.params[1]=='1'},False)
_mach.node={self.links[0]}
_mach.link=0
"""
    def undoable_code_text(self):
        return f"""
try:
    _mach.sort_table({compilable(self.params[0])},
                     {self.params[2:]},
                     {self.params[1]=='1'},True)
except:
    _mach.sort_table({quoted(self.params[0])},
                     {self.params[2:]},
                     {self.params[1]=='1'},True)
_mach.node={self.links[0]}
_mach.link=0
"""

class DestroyBlock(ExecutableBlock):
    """Destroy a table.
This block destroys a previously created table.  Tables can be created,
searched, updated, sorted, have records added or removed and destroyed
using the other table blocks ('Create', 'Select', 'Update','Insert',
'Delete' and 'Sort' blocks)
"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, destroy_presentation)

    def code_text(self):
        return f"""
try:
    _mach.destroy_table({compilable(self.params[0])},False)
except:
    _mach.destroy_table({quoted(self.params[0])},False)
_mach.node={self.links[0]}
_mach.link=0
"""

    def undoable_code_text(self):
        return f"""
try:
    _mach.destroy_table({compilable(self.params[0])},True)
except:
    _mach.destroy_table({quoted(self.params[0])},True)
_mach.node={self.links[0]}
_mach.link=0
"""

class DeleteBlock(ExecutableBlock):
    """Delete records (rows) from a table.
This block deletes one or more records from a table. The table
may have been created with a 'Create' block, or it may be one
of the built-in tables (_os.processes, _pg.table), history.
The records to delete may typically be the output of a 'Select'
block.
"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, delete_presentation)

    def code_text(self):
        return f"""
try:
    _table_name={compilable_not_a_tuple(self.params[0])}
except:
    _table_name={quoted(self.params[0])}
try:
    _todel=iter({compilable(self.params[1])})
except TypeError:
    try:
        _todel=[int({compilable(self.params[1])})]
    except TypeError:
        _todel=[]
try:
    _table=_mach.get_table(_table_name)
    _mach.delete_table_rows(_table,_todel,False)
except:
    _mach.log('Failed to delete from table',level=2)
_mach.node={self.links[0]}
_mach.link=0
"""

    def undoable_code_text(self):
        return f"""
try:
    _table_name={compilable(self.params[0])}
except:
    _table_name={quoted(self.params[0])}
try:
    _todel=iter(reversed({compilable(self.params[1])}))
except TypeError:
    try:
        _todel=[int({compilable(self.params[1])})]
    except TypeError:
        _todel=[]
try:
    _table=_mach.get_table(_table_name)
    _mach.delete_table_rows(_table,_todel,True)
except: #Exception as e:
    _mach.log('Failed to delete from table',level=2)
_mach.node={self.links[0]}
_mach.link=0
"""

class SelectBlock(ExecutableBlock):
    """Search a table
This block searches a table's contents and creates an
'iterator' over the record numbers of the matching records.

The search expression ('where' part) should be a valid
Python expression which returns 'True' for a record
which matches the search. Any of the table's fieldnames
used in the expression will give the field value of the
record being tested.

    Eg:  after executing:

      [Select] result
      [from] _pg.table
      [Where] thing=="text"

    iterating over result would give the indices of the
    'text' items displayed on the current page.
    For convenience iterating over result.indexed would give
    the rows themselves.

Note:   If any of the field names in a search expression
        might be the same as a local variable name, all
        field names can be prefixed with '_rec.' in the
        expression to distinguish them from local variables.

    Eg:
      [Select] result
      [from] _pg.table
      [Where] _rec.thing=="text"

    For further flexibility, '_rn' used in the search expression
    gives the record number of the currently searched record.
 """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, select_presentation)

    def filter_string(self):
        if self.params[3].strip():
            return f'''
    try:
        _recs=_Iset({self.params[3].strip()})
    except:
        _recs=_Iset(range(len(_table)))
'''
        return '    _recs=_table.all_records()'

    def code_text(self):
        if self.params[0]=='':
            return """
_mach.runtime_error('Unspecified result variable')
"""
        return f"""
try:
    _table_name={compilable(self.params[1])}
except:
    _table_name={quoted(self.params[1])}
try:
    _table=_mach.get_table(_table_name)
    _result=_Iset(indexed=_table)
{self.filter_string()}
    _sel_expr=_table.get_select_expr({quoted(compilable(self.params[2]))})
    for _rn in _recs:
        _rec=_table[_rn]
        exec(_sel_expr)
        if _in:
            _result+=_rn
except: #Exception as e:
    _mach.log('Exception in table search',level=2)
{self.params[0]}=_result
_mach.node={self.links[0]}
_mach.link=0
"""

    def undoable_code_text(self):
        if self.params[0]=='':
            return """
_mach.runtime_error('Unspecified result variable')
"""
        return f"""
try:
    _table_name={compilable(self.params[1])}
except:
    _table_name={quoted(self.params[1])}
try:
    _table=_mach.get_table(_table_name)
    _result=_Iset(indexed=_table)
{self.filter_string()}
    _sel_expr=_table.get_select_expr({quoted(compilable(self.params[2]))})
    _sel_expr=compile(_sel_expr,'','exec')
    try:
        _mach.add_undo(["varassign",{quoted(self.params[0])},{self.params[0]}])
    except:
        _mach.add_undo(["vardel",{quoted(self.params[0])}])
    for _rn in _recs:
        _rec=_table[_rn]
        exec(_sel_expr)
        if _in:
            _result+=_rn
except: #Exception as e:
    _mach.log('Exception in table search',level=2)
{assignation_text(self.params[0],'_result')}
_mach.node={self.links[0]}
_mach.link=0

"""

class InsertBlock(ExecutableBlock):
    """Insert row into table
    This block inserts a new row (or 'record') into a table.
    The row can be inserted at a specific index (zero inserts
    a row at the beginning of the table). If the insertion index
    is -1 or greater than or equal to the table length the row
    is appended to the table.
    Fields of the new row can be given values with this
    instruction, or they can take on the table's default values.
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, insert_presentation)

    def fields_code(self):
        def field_code(f, v):
            return f"""
    try:
        _row.{f}={compilable(v)}
    except:
        try:
            _row.{f}={quoted(v)}
        except:
            pass
"""
        return "\n".join([
            field_code(f, v)
            for [f, v] in self.params[2:] if is_valid_identifier(f)])

    def code_text(self):
        return f"""
try:
    _table_name={compilable(self.params[0])}
except:
    _table_name={quoted(self.params[0])}
try:
    _index=int({compilable(self.params[1])})
except:
    _index=0
try:
    _table=_mach.get_table(_table_name)
    _row=_table.blank_row
{self.fields_code()}
    _mach.insert_table_row(_table,_index,_row,False)
except: #Exception as e:
    _mach.log('Failed to insert to table',level=2)
_mach.node={self.links[0]}
_mach.link=0
"""

    def undoable_code_text(self):
        return f"""
try:
    _table_name={compilable(self.params[0])}
except:
    _table_name={quoted(self.params[0])}
try:
    _index=int({compilable(self.params[1])})
except:
    _index=0
try:
    _table=_mach.get_table(_table_name)
    _row=_table.blank_row
{self.fields_code()}
    _mach.insert_table_row(_table,_index,_row,True)
except: #Exception as e:
    _mach.log('Failed to insert to table',level=2)
_mach.node={self.links[0]}
_mach.link=0
"""

class JoinBlock(ExecutableBlock):
    """Joiner
    This block is simply to help the layout of the
    BUBBL diagram. All it does is join a link to
    another block, helping avoid 'spaghetti'.
    """
    def __init__(self,diag,no,init=None):
        super().__init__(diag, no, init,join_presentation)
    def code_text(self):
        return f'''
_mach.node={self.links[0]}
_mach.link=0
'''
    def undoable_code_text(self):
        return f'''
_mach.node={self.links[0]}
_mach.link=0
'''

class UpdateBlock(ExecutableBlock):
    """Update (read/write) table contents
    This block allows updating of multiple rows (records) and fields
    of a table with new values. The values are expressions which can
    include references to the row's fields and other items.
    This instruction can also be used to compute 'aggregate' functions
    and/or reading of multiple field values of a table's contents by
    assigning to a variable instead of a field-name.

    The instruction allows for namespace conflicts by allowing
    field-name references to be prefixed with '_rec.' to distinguish
    them from other variables in the global and local namespaces.

    The variable _rn refers to the row of the table being processed
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, update_presentation)

    def code_text(self):
        return f"""
try:
    _table=_mach.get_table({compilable(self.params[0])})
except:
    _table=_mach.get_table({quoted(self.params[0])})
try:
    _indices=iter({compilable(self.params[1])})
except TypeError:
    try:
        _indices=[int({compilable(self.params[1])})]
    except TypeError:
        _indices=[]
try:
    _update_code=_table.get_update_code({self.params[2:]},False)
    _update_code=compile(_update_code,'','exec')
    _all=_table.all_records()
    for _rn in _indices:
        if _rn not in _all:
            continue
        _rec=_table[_rn]
        exec(_update_code)
except: #Exception as e:
    _mach.log('Failed to update table',level=2)
_mach.node={self.links[0]}
_mach.link=0
"""

    def undoable_code_text(self):
        #return self.code_text()
        return f"""
try:
    _table=_mach.get_table({compilable(self.params[0])})
except:
    _table=_mach.get_table({quoted(self.params[0])})
try:
    _indices=iter({compilable(self.params[1])})
except TypeError:
    try:
        _indices=[int({compilable(self.params[1])})]
    except TypeError:
        _indices=[]
try:
    _update_code=_table.get_update_code({self.params[2:]},True)
    _update_code=compile(_update_code,'','exec')
    _all=_table.all_records()
    for _rn in _indices:
        if _rn not in _all:
            continue
        _rec=_table[_rn]
        try:
            exec(_update_code)
        except:# Exception:
            _mach.log('Table update Exec failed',level=2)
except: # Exception as e2:
    _mach.log('Failed to update table',level=2)
_mach.node={self.links[0]}
_mach.link=0
"""

class ForBlock(ExecutableBlock):
    """For loop
    This instruction is similar to the Python 'for loop' except the looping,
    'continue', and 'break' stuctured actions are achieved with BUBBL
     diagram links instead of with key-words.

    Its behaviour is equivalent to the following Python:
        for variable in iterable:
            follow_do_link
        follow_done_link

    When entered from another block the loop iterable is set up and
    if there are iterations the 'do' link is followed.
    However, when entered from the attached 'link' block, the 'next'
    iteration continues via the 'do' link.

    If there were no iterations or the iterations have finished the 'done'
    link is followed.

    Unlike the Python 'for loop' this block 'un-iterates' the iterable
    (restoring value from previous iteration) when stepping the program
    backwards.

    Note:
        As for the Python 'for loop', the 'Variable' parameter can only be
        a simple identifier or tuple of identifiers: dot- or index-notation
        is not supported.
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, for_presentation)

    def iter_name(self):
        return f"_iterator_{self.no}"

    def code_text(self):
        n = self.iter_name()
        lv = self.params[0]
        if all(is_valid_identifier(l) for l in lv.split(',')):
            return f"""
try:
    {n}={compilable(self.params[1])}.__iter__()
except:
    {n}={quoted(self.params[1])}
try:
    {lv}={n}.__next__()
    _mach.node={self.links[0]}
    _mach.link=0
except AttributeError:
    try:
        {lv}={compilable(self.params[1])}
    except:
        {lv}={quoted(self.params[1])}
    _mach.node={self.links[0]}
    _mach.link=0
except StopIteration:
    _mach.node={self.links[1]}
    _mach.link=1
"""
        else:
            return f"""
_mach.node={self.links[1]}
_mach.link=1
"""

    def auxcode_text(self):
        n = self.iter_name()
        lv = self.params[0]
        if all(is_valid_identifier(l) for l in lv.split(',')):
            return f"""
try:
    {lv}={n}.__next__()
    _mach.node={self.links[0]}
    _mach.link=0
except (StopIteration,AttributeError):
    _mach.node={self.links[1]}
    _mach.link=1
"""
        else:
            return f"""
_mach.node={self.links[1]}
_mach.link=1
"""

    def undoable_code_text(self):
        lv = self.params[0]
        if all(is_valid_identifier(l) for l in lv.split(',')):
            n = self.iter_name()
            assig=assignation_text(lv,'_it_val')
            return f"""
try:
    {n}=_mach.get_undoable_iterator({compilable(self.params[1])}).__iter__()
except: #Exception as e:
    _mach.log("undoable_iterator_exception:",level=2)
    {n}=_mach.get_undoable_iterator({quoted(self.params[1])}).__iter__()
try:
    _mach.add_undo(['uniterate',{quoted(n)}])
    _it_val={n}.__next__()
    {indented(assig)}
    _mach.node={self.links[0]}
    _mach.link=0
except AttributeError:
    _mach.log('For Block AttributeError',level=2)
    _mach.node={self.links[1]}
    _mach.link=1
except StopIteration:
    _mach.node={self.links[1]}
    _mach.link=1
"""
        else:
            return f"""
_mach.node={self.links[1]}
_mach.link=1
"""
    def undoable_auxcode_text(self):
        lv=self.params[0]
        if all(is_valid_identifier(l) for l in lv.split(',')):
            n = self.iter_name()
            assig=assignation_text(lv,'_it_val')
            return f"""
_mach.add_undo(['uniterate',{quoted(n)}])
try:
    _it_val={n}.__next__()
    {indented(assig)}
    _mach.node={self.links[0]}
    _mach.link=0
except AttributeError:
    _mach.log('For Aux AttributeError',level=2)
    _mach.node={self.links[1]}
    _mach.link=1
except StopIteration:
    _mach.node={self.links[1]}
    _mach.link=1
"""
        else:
            return f"""
_mach.node={self.links[1]}
_mach.link=1
"""

class FormulaBlock(Block):
    """Live data view
    When the program is paused, or in 'editing' mode, variable values
    and expressions can be shown with this block.

    Note: For large data types which cannot be easily displayed
          on one line, variables can be viewed as 'JSON' encoded
          text (see https://www.json.org/json-en.html) in a larger
          window. Here they can be edited directly to help in debugging
          and program development. Edited values must conform strictly
          to JSON format to be accepted.
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, formula_presentation)

class WriteBlock(ExecutableBlock):
    """Write text on a page (window)
    This block creates text on the current 'page' (or 'window').
    The location, font colour etc. can be controlled with markups.
    The text created can also be manipulated through the table
    _pg.table which gives access to the attributes of the text.
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, write_presentation)
    def code_text(self):
        return f"""
try:
    _text={compilable(self.params[0])}
except:
    _text={quoted(self.params[0])}
_page=_mach.current_page
{markups_dict(self.params[1:])}
try:
    _page.add_text_thing(False,text=_text, **_dict)
except: # Exception as e:
    _mach.log('Text defaulting to add_output',level=2)
    try:
        _page.add_output(_text)
    except:
        pass
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
       return f"""
try:
    _text={compilable(self.params[0])}
except:
    _text={quoted(self.params[0])}
_page=_mach.current_page
{markups_dict(self.params[1:])}
try:
    _page.add_text_thing(True,text=_text,**_dict)
except:# Exception as e:
    #_mach.log('Text defaulting to add_output',level=2)
    try:
        _page.add_output(_text)
    except:
        pass
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class RectangleBlock(ExecutableBlock):
    """Draw a rectangle on a page (window)
    This block creates a rectangle on the current 'page' (or 'window').
     The location, colour etc. can be controlled with markups.
     The rectangle created can also be manipulated through the table
     _pg.table which gives access to the attributes of the rectangle.
     """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, rectangle_presentation)

    def code_text(self):
        return f"""
_page=_mach.current_page
try:
    _width=int({compilable(self.params[0])})
except:
    _width=0
try:
    _height=int({compilable(self.params[1])})
except:
    _height=0
{markups_dict(self.params[2:])}
try:
    _page.add_rect_thing(False,width=_width,height=_height,**_dict)
except: #Exception as e:
    _mach.log('Failed to create Rectangle,level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
        return f"""
_page=_mach.current_page
try:
    _width=int({compilable(self.params[0])})
except:
    _width=0
try:
    _height=int({compilable(self.params[1])})
except:
    _height=0
{markups_dict(self.params[2:])}
try:
    _page.add_rect_thing(True,width=_width,height=_height,**_dict)
except: #Exception as e:
    _mach.log('Failed to create Rectangle',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class PolygonBlock(ExecutableBlock):
    """Draw a polygon on a page (window)
    This block creates a polygon on the current 'page' (or 'window').
     The location, colour etc. can be controlled with markups.
     The polygon created can also be manipulated through the table
     _pg.table which gives access to the attributes of the polygon.
     """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, polygon_presentation)

    def code_text(self):
        return f"""
_page=_mach.current_page
{markups_dict(self.params[2:])}
try:
    _dxs={compilable(self.params[0])}
    if isinstance(_dxs,str):
        _dxs=[int(p) for p in _dxs.split(',')]
    _dys={compilable(self.params[1])}
    if isinstance(_dys,str):
        _dys=[int(p) for p in _dys.split(',')]
    _page.add_polygon_thing(False,dxs=_dxs,dys=_dys,**_dict)
except: #Exception as e:
    _mach.log('Failed to create polgyon',level=2)
    #_page.add_text_thing(False,text=str(e))
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
        return f"""
_page=_mach.current_page
{markups_dict(self.params[2:])}
try:
    _dxs={compilable(self.params[0])}
    if isinstance(_dxs,str):
        _dxs=[int(p) for p in _dxs.split(',')]
    _dys={compilable(self.params[1])}
    if isinstance(_dys,str):
        _dys=[int(p) for p in _dys.split(',')]
    _page.add_polygon_thing(True,dxs=_dxs,dys=_dys,**_dict)
except: #Exception as e:
    _mach.log('Failed to create polygon',level=2)
    #_page.add_text_thing(True,text=str(e))
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class EllipseBlock(ExecutableBlock):
    """Draw an ellipse (circle) on a page (window)
    This block creates an ellipse or circle on the current 'page' (or 'window').
     The location, colour etc. can be controlled with markups.
     The ellipse created can also be manipulated through the table
     _pg.table which gives access to the attributes of the ellipse.
     """

    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, ellipse_presentation)

    def code_text(self):
        return f"""
_page=_mach.current_page
try:
    _width=int({compilable(self.params[0])})
except:
    _width=0
try:
    _height=int({compilable(self.params[1])})
except:
    _height=0
{markups_dict(self.params[2:])}
try:
    _page.add_ellipse_thing(False,width=_width,height=_height,**_dict)
except: #Exception as e:
    _mach.log('Failed to create ellipse',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
        return f"""
_page=_mach.current_page
try:
    _width=int({compilable(self.params[0])})
except:
    _width=0
try:
    _height=int({compilable(self.params[1])})
except:
    _height=0
{markups_dict(self.params[2:])}
try:
    _page.add_ellipse_thing(True,width=_width,height=_height,**_dict)
except: #Exception as e:
    _mach.log('Failed to create ellipse',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class ArcBlock(ExecutableBlock):
    """Draw an arc, chord or 'pie-slice' on a page (window)
    This block creates an arc, segment or sector ('pie-slice') of
    an ellipse on the current page (or 'window').
     The location, outline style, colour etc. can be controlled with markups.
     The shape created can also be manipulated through the table
     _pg.table which gives access to the attributes of the shape.
     """

    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, arc_presentation)

    def code_text(self):
        return f"""
_page=_mach.current_page
try:
    _width=int({compilable(self.params[0])})
except:
    _width=0
try:
    _height=int({compilable(self.params[1])})
except:
    _height=0
{markups_dict(self.params[2:])}
try:
    _page.add_arc_thing(False,width=_width,height=_height,&&_dict)
except: #Exception as e:
    _mach.log('Failed to create arc',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
        return f"""
_page=_mach.current_page
try:
    _width=int({compilable(self.params[0])})
except:
    _width=0
try:
    _height=int({compilable(self.params[1])})
except:
    _height=0
{markups_dict(self.params[2:])}
try:
    _page.add_arc_thing(True,width=_width,height=_height,**_dict)
except: #Exception as e:
    _mach.log('Failed to create arc',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class LineBlock(ExecutableBlock):
    """Draw a line on a page (window)
    This block creates a line on the current 'page' (or 'window').
    The line can be a single straight line, or a connected sequence
    of straight segments.
    The location, colour etc. can be controlled with markups.
    The line created can also be manipulated through the table
    _pg.table which gives access to the attributes of the line.
     """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, line_presentation)

    def code_text(self):
        return f"""
_page=_mach.current_page
try:
    _dxs={compilable(self.params[0])}
except:
    _dxs=0
try:
    _dys={compilable(self.params[1])}
except:
    _dys=0
{markups_dict(self.params[2:])}
try:
    _page.add_line_thing(False,dxs=_dxs,dys=_dys,**_dict)
except: #Exception as e:
    _mach.log('Failed to create line',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""
    def undoable_code_text(self):
        return f"""
_page=_mach.current_page
try:
    _dxs={compilable(self.params[0])}
except:
    _dxs=0
try:
    _dys={compilable(self.params[1])}
except:
    _dys=0
{markups_dict(self.params[2:])}
try:
    _page.add_line_thing(True,dxs=_dxs,dys=_dys,**_dict)
except: #Exception as e:
    _mach.log('Failed to create line',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class ImageBlock(ExecutableBlock):
    """Show an image on a page (window)
    This block shows an image on the current 'page' (or 'window').
    The image source can be read from a file (e.g. .png or .jpg) or
    Python PIL image object or a BUBBLImage object.
    The location, dimensions and orientation etc. can be controlled
    with markups.
    The image created can also be manipulated through the table
    _pg.table which gives access to the attributes of the image.
     """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, image_presentation)

    def code_text(self):
        if self.init['params'][0] == '':
            return f"""
_mach.node={self.init['links'][0]}
_mach.link=0
"""
        return f"""
_page=_mach.current_page
{markups_dict(self.params[1:])}
try:
    _image_ref={compilable(self.init['params'][0])}
    _page.add_image_thing(False,filename=_image_ref,**_dict)
except:
    try:
        _image_ref={quoted(self.init['params'][0])}
        _page.add_image_thing(False,filename=_image_ref,**_dict)
    except:# Exception as e:
        _mach.log('Failed to create image',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
        if self.init['params'][0] == '':
            return f"""
_mach.node={self.init['links'][0]}
_mach.link=0
"""

        return f"""
_page=_mach.current_page
{markups_dict(self.params[1:])}
try:
    _image_ref={compilable(self.init['params'][0])}
    _page.add_image_thing(True,filename=_image_ref,**_dict)
except:
    try:
        _image_ref={quoted(self.init['params'][0])}
        _page.add_image_thing(True,filename=_image_ref,**_dict)
    except: # Exception as e:
        _mach.log('Failed to create image',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class WaitBlock(ExecutableBlock):
    """Wait for event
    This instruction is the main way BUBBL implements real-time
    program behaviour.  It responds to user actions (e.g. mouse
    movement or key presses), timer and other 'events', selecting
    a link to follow depending on the event source.  Events are
    queued and processed in the order in which they are received
    so that program behaviour is precisely defined.
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, wait_presentation)

    def code_text(self):
        if len(self.params)==1:
            return "raise _mach.wait_exception_class('EMPTYWAIT')"
        def testline(i):
            if self.params[i]=='Any':
                return f'''
    _mach.node={self.links[i - 1]}
    _mach.set_event(_event)
    _mach.link={i - 1}
    break'''
            return f'''
    if _event.event_type == {quoted(self.params[i])} :
        _mach.node={self.links[i - 1]}
        _mach.link={i - 1}
        _mach.set_event(_event)
        break
'''
        nl = '\n'
        return f"""
_event=_mach.get_event()
if _event is None:
    raise _mach.wait_exception_class('WAIT')
while True:
{nl.join(testline(i) for i in range(1, len(self.params)))}
    _event=_mach.get_event()
    if _event is None:
        raise _mach.wait_exception_class('WAIT')
"""
    def undoable_code_text(self):
        return self.code_text()

class MenuBlock(ExecutableBlock):
    """Pop-up a menu
    This block allows the program user to choose an action by
    popping up a menu of choices. Each choice selects a link for
    the program to follow"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, menu_presentation)

    def code_text(self):
        def get_menu_items_str():
            p0="_items=[]\n"
            p1="\n".join(f"""
try:
    _item=({compilable(p)}).__str__()
    _items.append(_item)
except:
    _items.append({quoted(p)})
""" for p in self.params if isinstance(p,str))
            return p0+p1+'\n'

        def get_markups_str():
            p0 = "_mus=[]\n"
            p2 = "\n".join([f"""try:
    try:
        _muv={compilable_not_a_tuple(p[1])}
    except:
        _muv={quoted(p[1])}
    _mus.append([{quoted(p[0])},_muv])
except:
    _mus.append([{quoted(p[0])},
    {quoted(p[1])}])""" for p in self.params if not isinstance(p,str) and p[0] in dispmarkups['menu']])
            return p0 + p2+ '\n'

        return f"""
{get_menu_items_str()}
{get_markups_str()}
_mach.menu(_items,{self.links},_mus)
"""
    def undoable_code_text(self):
        return self.code_text()

    def uncentered_display_line(self,index):
        p=self.params[index-1]
        if isinstance(p,str):
            return p
        else:
            return f'{p[0]} = {p[1]}'

class ColourMenuBlock(ExecutableBlock):
    """Popup a colour chooser
    This block allows a program user to select a colour with
    a colour visualising popup interface. If confirmed by the
    user, the selected colour is assigned to a variable.
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, colourMenu_presentation)
    def code_text(self):
        if not is_valid_identifier(self.params[0]):
            return f"""
_mach.link=0
_mach.node={self.links[0]}
            """
        def get_markups_str():
            p0 = "_mus=[]\n"
            p2 = "\n".join(
                [f"""try:
    _mus.append(["{p[0]}",{compilable_not_a_tuple(p[1])}])
except:
    _mus.append(["{p[0]}",{quoted(p[1])}])""" for p in
                 self.params[1:] if p[0] in dispmarkups['colourmenu']])
            p2 += '\n'
            return p0 + p2
        return f"""
{get_markups_str()}
try:
    _default={compilable(self.params[0])}
except:
    _default="#888"
_result=_mach.colour_menu(_default,_mus)
if _result is None:
    _mach.link=0
    _mach.node={self.links[0]}
else:
    {self.params[0]}=_result
    _mach.link=1
    _mach.node={self.links[1]}
"""
    def undoable_code_text(self):
        return f"""
if {quoted(self.params[0])} in locals():
    _mach.add_undo(['varassign',{quoted(self.params[0])},{self.params[0]}])
else:
    _mach.add_undo(['vardel',{quoted(self.params[0])}])
"""+self.code_text()

class FileMenuBlock(ExecutableBlock):
    """Popup a file chooser
    This block pops up a file dialog for the program user to select
    a file, e.g. for 'save as' or 'load' operations.  The detailed
    behaviour of the dialog can be set with 'markups':
    Markup      Description
    ------      -----------
    saveas      Setting to True allows a new file to be entered and
                pops up an 'overwrite' dialog if the file exists
    folder      Allows selecting an existing folder only.
    multiple    Allows multiple files in a single folder to be selected
    title       Change the title of the dialog from the default
    history     Specify a 'key' to identify a specific list of 'recent'
                files to select from/add to
    hidden      Select whether to show hidden files (default is not to)
    view        Select whether 'list' or 'icon' view
    filetypes   A comma-separated list of '<description>:<mask>[:<mask2>...etc]' where
                <mask> is (e.g.) '*.py'.
                Hint: use <Ctrl> key to toggle selection.
"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, fileMenu_presentation)
    def code_text(self):
        if not is_valid_identifier(self.params[0]):
            return f"""
_mach.link=0
_mach.node={self.links[0]}
            """
        def get_markups_str():
            p0 = "_mus=[]\n"
            p2 = "\n".join([f"""try:
    _mus.append(["{p[0]}",{compilable_not_a_tuple(p[1])}])
except:
    _mus.append(["{p[0]}",{quoted(p[1])}])""" for p in self.params[1:] if p[0] in dispmarkups['filechooser']])
            p2 += '\n'
            return p0 + p2
        return f"""
{get_markups_str()}
try:
    _default={compilable(self.params[0])}
except:
    _default=''
_mach.file_menu({self.links},{quoted(self.params[0])},_default,_mus)
"""
    def undoable_code_text(self):
        return self.code_text()


class AlertBlock(ExecutableBlock):
    """Popup a user message
    This block pops up a window showing a message for the user.  It waits for
    the user to dismiss the window by closing it, pressing the 'Ok' button or
    hitting the escape key.
"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, alert_presentation)
    def code_text(self):
        def get_markups_str():
            p0 = "_mus=[]\n"
            p2 = "\n".join([f"""try:
    _mus.append(["{p[0]}",{compilable_not_a_tuple(p[1])}])
except:
    _mus.append(["{p[0]}",{quoted(p[1])}])""" for p in self.params[1:] if p[0] in dispmarkups['alert']])
            p2 += '\n'
            return p0 + p2
        return f"""
{get_markups_str()}
try:
    _message={compilable_not_a_tuple(self.params[0])}
except:
    _message={quoted(self.params[0])}
_mach.alert({self.links},_message,_mus)
"""
    def undoable_code_text(self):
        return self.code_text()

class AskUserBlock(ExecutableBlock):
    """Ask user 'yes, no or cancel' question
    This block pops up a window showing a 'question' with a
    'Yes', 'No' and a 'Cancel' button.  Each button selects
    a different link to follow.
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, askUser_presentation)

    def code_text(self):
        def get_markups_str():
            p0 = "_mus=[]\n"
            p2 = "\n".join([f"""try:
    _mus.append(["{p[0]}",{compilable_not_a_tuple(p[1])}])
except:
    _mus.append(["{p[0]}",{quoted(p[1])}])""" for p in self.params[1:] if p[0] in dispmarkups['ask']])
            p2 += '\n'
            return p0 + p2

        return f"""
{get_markups_str()}
try:
    _question={compilable_not_a_tuple(self.params[0])}
except:
    _question={quoted(self.params[0])}
_mach.yes_no_esc({self.links},_question,_mus)
"""

    def undoable_code_text(self):
        return self.code_text()

class InputBlock(ExecutableBlock):
    """Popup an input box
    This instruction pops up a window with one or more labelled
    text-input fields, allowing the program user to enter values
    while the program is running.
"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, input_presentation)

    def code_text(self):
        def get_markups_str():
            if any(p[0] == 'defaults' for p in self.params[1:]):
                p0 = "_mus=[]\n"
                extraparam = ""
            else:
                def get_def(val):
                    return f'''
try:
    _defs.append(str({val}))
except:
    _defs.append("")
'''
                p0 = '''
_defs=[]
_mus=[]
'''
                p0 += "\n".join([get_def(p) for p in self.params[0].split(',') if is_valid_identifier(p)])

                p0 += '\n'
                extraparam = '_mus.append(["defaults",_defs])'
            p2 = "\n".join([f"""try:
    _mus.append(["{p[0]}",{compilable_not_a_tuple(p[1])}])
except:
    _mus.append(["{p[0]}",{quoted(p[1])}])""" for p in self.params[1:] if p[0] in dispmarkups['input']])
            p2 += '\n'
            return p0 + p2 + extraparam

        def write_back_str():
            return "\n".join([f"    {p.strip()}=_eval(_res[{i}])" for i, p in enumerate(self.params[0].split(",")) if
                              is_valid_identifier(p.strip())])

        return f"""
{get_markups_str()}
_mach.input_vars({self.links},{self.params[0].split(',')},_mus)
"""
    def undoable_code_text(self):
        return self.code_text()

class ChoiceBlock(ExecutableBlock):
    """Popup a list to choose from
    This block pops up a scrollable list of many items from which
    the user may select.  Markups can be used to alter the look of
    the popup and to set the behaviour (such as whether multiple
    selections are allowed).
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, choice_presentation)

    def code_text(self):
        if self.params[0].strip()=='':
            return "_mach.runtime_error('Unspecified result variable')"
        def get_markups_str():
            return "\n".join([f"""try:
    _mus.append([{quoted(p[0])},{compilable_not_a_tuple(p[1])}])
except:
    _mus.append([{quoted(p[0])},{quoted(p[1])}])""" for p in self.params[2:] if p[0] in dispmarkups['choice']])
        return f"""
_mus=[]
{get_markups_str()}
_defaults=_mach.get_markup('default',_mus,None)
if _defaults is None and {quoted(self.params[0])} in _mach.diag.variables:
    _mus.append(['default',{self.params[0]}])
try:
    _choices={compilable(self.params[1])}
except:
    _choices={quoted(self.params[1])}
_mach.input_choice({self.links},{quoted(self.params[0])},_choices,_mus)
"""
    def undoable_code_text(self):
        return self.code_text()

class AssignBlock(ExecutableBlock):
    """Assign expressions to variables
    This block assigns a variable with the value of an expression, or each
    variable of a tuple variables with the value of a corresponding
    expression from a tuple of expressions.
    Invalid Python expressions may cause a 'runtime' error, or be replaced
    with a literal (quoted) representation of the expression, rather than its
    evaluation.
    Note: Pattern matched 'l-values' (e.g. assignments to sub-ranges of lists)
          do not necessarily have correct 'undo' behaviour when stepping a
          program backwards.
"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, assign_presentation)

    def code_text(self):
        return "\n".join(f"""
try:
    {n.strip()}={compilable(v)}
except: #Exception as e:
    _mach.log('ASSIGN Exeption: ',level=2)
    try:
        {n.strip()}={quoted(v)}
    except:
        pass
""" for [n, v] in self.params
        if is_lvalue(n.strip()))+f"""
_mach.link=0
_mach.node={self.init['links'][0]}"""

    def undoable_code_text(self):
        return '\n'.join(assignation_text(n, v) for [n, v] in
            self.params)+f"\n_mach.link=0\n_mach.node={self.init['links'][0]}"

class IfBlock(ExecutableBlock):
    """Choose next block based on boolean expression
    If the evaluation of the express is True,

    """

    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, if_presentation)

    def code_text(self):
        return f"""
if {compilable(self.init['params'][0])}:
    _mach.node={self.init['links'][0]}
    _mach.link=0
else:
    _mach.node={self.init['links'][1]}
    _mach.link=1
"""
    def undoable_code_text(self):
        return self.code_text()

class PageBlock(ExecutableBlock):
    """Open page (window)
    This block creates or selects a previously created 'page' (or
    'window') for output and/or user interaction.  The size, colours,
    font etc. can be set via 'markups'.  The currently selected page
    is where outputs such as text and graphics and user-interface
    'widgets' are displayed.
    The 'menu' parameter takes a list of one or more 'top-line-menu' items.
    Each item is either 'sub-menu' list or a single choice string.
    Sub-menu lists start with the sub-menu name, followed by the choices.
    e.g.  [['File','New','Open','Save'],'Help']
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, page_presentation)

    def code_text(self):
        if self.init['params'][0] == '':
            return f"""
_mach.node={self.init['links'][0]}
_mach.link=0
"""
        return f"""
try:
    _page={compilable_not_a_tuple(self.init['params'][0])}
except:
    _page={quoted(self.init['params'][0])}
{markups_dict(self.params[1:])}
_mach.select_page(False,_page,**_dict)
_mach.node={self.init['links'][0]}
_mach.link=0
raise _mach.wait_exception_class('PAGE')
"""

    def undoable_code_text(self):
        if self.init['params'][0] == '':
            return f"""
_mach.node={self.init['links'][0]}
_mach.link=0
"""
        return f"""
try:
    _page={compilable_not_a_tuple(self.init['params'][0])}
except:
    _page={quoted(self.init['params'][0])}
{markups_dict(self.params[1:])}
_mach.select_page(True,_page,**_dict)
_mach.node={self.init['links'][0]}
_mach.link=0
raise _mach.wait_exception_class('PAGE')
"""

class PrintBlock(ExecutableBlock):
    """Print page or image or text
    This generates a printable file from a page, an image a string
    or list of strings and attempts to send it to a printer.
    For pages (and tkinter 'Canvas' objects) a 'postscript' file
    called 'bubbl.eps' is created in the temporary directory which
    can then either be sent to the printer directly (if the printer
    supports postscript) or converted to a '.pdf' document using
    'ghostscript' (see: https://www.ghostscript.com).
    The .pdf file can either be sent to a printer, or saved to the
    file system.  Images are first saved as '.png' or '.jpg' files,
    before being sent to the printer.
    The destination printer can be selected with the 'printer' markup:
        To select the printer on Windows:
            /d:<printer name>           refers to a local printer
            \\<server_name>[:port]       refers to a network printer
        To select the printer on Linux:
            -d <printer name>           refers to a local printer
            -h <server name>[:port]     refers to a network printer
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, print_presentation)

    def code_text(self):
        def source_part():
            if self.init['params'][0]=='_pg':
                return '_source=_pg.canvas\n'
            return f"""        
try:
    _source={compilable(self.init['params'][0])}
except:
    _source={quoted(self.init['params'][0])}
if isinstance(_source,str):
    if _source in _pg:
        _source=_pg[_source]
"""
        return f"""
{source_part()}
{markups_dict(self.params[1:])}
if _mach.ok_send_to_printer(_source,**_dict):
    _mach.link=0
else:
    _mach.link=1
_mach.node={self.init['links']}[_mach.link]
"""
    def undoable_code_text(self):
        return self.code_text()

class PageCloseBlock(ExecutableBlock):
    """Destroy (close) the currently selected page
    This block closes and completely removes the currently selected
    page (or 'window')"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, pageClose_presentation)

    def code_text(self):
        return f"""
_mach.close_page(_mach.current_page.name)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
        return f"""
_mach.undoably_close_page(_mach.current_page.name)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class PageClearBlock(ExecutableBlock):
    """Clear the currently selected page
    This block clears all text, graphics and user interface 'widgets'
    from the currently selected page (or 'window') leaving it blank.
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, pageClear_presentation)

    def code_text(self):
        return f"""
_mach.clear_page(_mach.current_page.name)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
        return f"""
_mach.undoably_clear_page(_mach.current_page.name)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class PageUpdateBlock(ExecutableBlock):
    """Update the currently selected page
    This block allows changes to be mage to the currently selected page
    such as its size or where it appears on the screen.
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, pageUpdate_presentation)

    def get_markups_str(self):
        return "\n".join(f"""
try:
    _page.{p[0]}={compilable_not_a_tuple(p[1])}
except:
    _page.{p[0]}={quoted(p[1])}
""" for p in self.params if p[0] in dispmarkups['page'])

    def code_text(self):
        return f"""
_page=_mach.current_page
{self.get_markups_str()}
_mach.refresh_current_page()
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
        return f"""
_page=_mach.current_page
_mach.add_undo(["page_update",_page.name,_page.markups])
{self.get_markups_str()}
_mach.refresh_current_page()
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class TableViewBlock(Block):
    """Non-executable presentation of a table's contents"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, table_view_presentation)

class TextBlock(Block):
    """Free text within a diagram"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, text_presentation)

class VariableBlock(Block):
    """JSON representation of a variable value"""
    def __init__(self,diag, no, init=None):
        super().__init__(diag,no,init,variable_presentation)

class DBVariableBlock(Block):
    """JSON representation of a variable value"""
    def __init__(self,diag, no, init=None):
        super().__init__(diag,no,init,variable_presentation)

class LinkBlock(ExecutableBlock):
    """Close 'loop' section
    This block, exits a block, choosing the labelled link to follow if the
    block has more than one link, or the single un-labelled link."""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, link_presentation)

    def code_text(self):
        pars = self.diag.sig["params"]
        wbacks = [i for i, par in enumerate(pars) if par.startswith('@')]
        index = self.init['params'][0]
        #if index>=len(self.diag.links): #Protect against accidental diag link deletions
        #    index=0
        getwbacks = f'\n_wbackvals=[' + ','.join(f'{pars[i][1:]}'
                                                 for i in wbacks) + ']'
        return f'''
#_mach.print_code()
{getwbacks}
_mach.link={index}
if _mach.stack==[]:
    _mach.node=0
    _mach.stopped=True
    _mach.state={ExState.exited}
else:
    _mach.diag,_node=_mach.stack.pop()
    _params=_mach.diag.nodes[_node].params
    for _si,_di in enumerate({wbacks}):
        _mach.diag.variables[_params[_di]]=_wbackvals[_si]
    _mach.lastnode=_node
    _mach.node=_mach.diag.nodes[_node].links[{index}]
'''

    def undoable_code_text(self):
        pars = self.diag.sig["params"]
        wbacks = [i for i, par in enumerate(pars) if par.startswith('@')]
        index = self.init['params'][0]
        #if index >= len(self.diag.links):  # Protect against accidental diag link deletions
        #    index = 0
        getwbacks = f'\n_wbackvals=[' + ','.join(f'{pars[i][1:]}'
                                                 for i in wbacks) + ']'
        return f'''
#_mach.print_code(undoable=True)
{getwbacks}
_mach.link={index}
if _mach.stack==[]:
    _mach.node=0
    _mach.stopped=True
    _mach.state={ExState.exited}
else:
    _mach.add_undo(["goto",_mach.diag,_mach.node,_mach.link])
    _mach.diag,_node=_mach.stack.pop()
    _mach.add_undo(["push",_mach.diag,_node])
    _params=_mach.diag.nodes[_node].params
    for _si,_di in enumerate({wbacks}):
        if _params[_di] in _mach.diag.variables:
            _mach.add_undo(["varassign",_params[_di],
                            _mach.diag.variables[_params[_di]]])
        else:
            _mach.add_undo(["vardel",_params[_di]])
        _mach.diag.variables[_params[_di]]=_wbackvals[_si]
    _mach.last_node=_node
    _mach.node=_mach.diag.nodes[_node].links[{index}]
'''

def get_link_block(diag, block_no, index):
    link_block = LinkBlock(diag, block_no)
    link_block.init["params"][0] = index
    return link_block

def indented(text,indent=4):
    return '\n'.join(' '*indent+s if not s.isspace() else s for s in text.split('\n'))

class PythonBlock(ExecutableBlock):
    """Pure Python Block
This block should contain pure Python source code.
All such blocks in a diagram have the same globals() and
locals() namespaces, so can be strung together in a
sequence as if they follwed one another in Python module.

The globals() namespace contains these additional
predefined variables, allowing access to BUBBL's internal
structures:
    _mach   The currently running BUBBL virtual machine
    _db     A namespace holding tables and other global
            variables (accessed with dot or index notation).
    _fs     Access to various file-system functions
    _pg     Access to the display/windows
    _os     Access to various O/S functions
    _Iset   An 'ordered set of integers' class
"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, python_presentation)

    def code_text(self):
        text='\n'.join(self.params)
        try:
            compile(text,'python-block','exec')
            if text.isspace():
                return 'pass'
            return text
        except SyntaxError as e:

            log('SyntaxError',self.diag.name,self.no,e,e.lineno,e.offset,len(text),level=2)
            #for i in range(e.lineno-2):
            #    col-=len(self.params[i])+1
            text=f'_mach.python_syntax_error({quoted(e)},{e.lineno},{e.offset})'
            #print('PSE CODE IS',f'>{text}<')
            return text
    def undoable_code_text(self):
        return self.code_text()

    def exec(self):
        try:
            exec(self.code, self.diag.variables)
            self.diag.mach.link=0
            self.diag.mach.node=self.links[0]
        except Exception as e:
            raise PythonBlockException(
                e,
                '\n'.join(self.params))

    def exec_undoable(self):
        before=self.diag.variables.copy()
        try:
            exec(self.undoable_code,self.diag.variables)
            self.diag.mach.link=0
            self.diag.mach.node=self.links[0]
        except Exception as e:
            #self.diag.variables.update(before)
            self.diag.variables.update(before)
            raise PythonBlockException(
                    e,
                    '\n'.join(self.params))
        self.diag.mach.undo_list.append(['varsassign',before])

    def exec_undoably(self):
        #before = {k: v for k, v in self.diag.variables.items() if k[0] != '_'}
        before=self.diag.variables.copy()
        try:
            exec(self.code,self.diag.variables)
            self.diag.mach.link=0
            self.diag.mach.node=self.links[0]
        except Exception as e:
            #self.diag.variables.clear()
            #self.diag.variables.update(before)
            dels = self.diag.variables.keys() - before.keys()
            for k in dels:
                self.diag.variables.pop(k)
            self.diag.variables.update(before)
            raise PythonBlockException(
                    e,
                    '\n'.join(self.params))
        self.diag.mach.undo_list.append(['varsassign',before])

class FileMkDirBlock(ExecutableBlock):
    """Create a directory ('folder') or directories
    This block creates a new directory, including missing directories in
    the directory tree"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, fileMkDir_presentation)

    def code_text(self):
        if self.init['params'][0] == '':
            return f"""
_fs.message='Folder name cannot be empty'
_mach.node={self.init['links'][1]}
_mach.link=1
"""
        return f"""
try:
    _dname={compilable(self.init['params'][0])}
except:
    _dname={quoted(self.init['params'][0])}
try:
    _mach.filevars._make_dirs(_dname)
    _fs.message='Ok'
    _mach.link=0
    _mach.node={self.init["links"][0]}
except: #Exception as e:
    _fs.message=str(e)
    _mach.node={self.init["links"][1]}
    _mach.link=1
"""

    def undoable_code_text(self):
        return self.code_text()

class FileSaveBlock(ExecutableBlock):
    """Save data to a file
    This block creates or overwrites a file with data. Its behaviour depends
    on the type of data and the 'extension' of the file-name as follows:
    Note:1)  If the file is a text file, the encoding is taken from the
        (r/w) system variable '_fs.encoding'. '_fs.encodings' is a list
        of available encodings.
         2) The system variable '_fs.message' will be set to 'Ok' and the
        'Ok' link will be followed if the file was written successfully,
        otherwise _fs.message will be an error message and the 'Fail' link
        will be followed.

    If the data is a Python 'str' it is written directly to the (text) file.
    If the data is a Python list of Python str objects, each element is
        written to the file followed by '\\n' (new line).
    If the data is a list of integers and the file extension is 'HEX' or
        BASE64 the data is written in the appropriate encoding.
    If the data is a ('PAGE' or '_pg[<page-name>]') or an image
       record (from _pg.table) and the extension is one of png,jpeg,
       jpg,xbm,xpm,pbm the appropriate image file is written.
    If the data is a table and the extension is 'html' the table is written
        to the file as a html <table> element.
    If the data is a table and the extension is 'csv' the table field names
        followed by the table rows are written as lines with comma-separated
        values. Each line is followed by a '\\n' (new line character).
    If the data can be converted to JSON representation, this is written
        to the file.
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, fileSave_presentation)

    def code_text(self):
        if self.init['params'][0] == '':
            return f"""
_fs.message='Filename cannot be empty String'            
_mach.node={self.init['links'][1]}
_mach.link=1
"""

        return f"""
try:
    _fname={compilable(self.init['params'][1])}
except:
    _fname={quoted(self.init['params'][1])}
try:
    _what={compilable(self.init['params'][0])}
except:
    _what=None
if _mach.filevars._ok_save_to_file(_what,_fname):
    _mach.link=0
    _mach.node={self.links[0]}
else:
    _mach.link=1
    _mach.node={self.links[1]}
"""

    def undoable_code_text(self):
        return self.code_text()

class FileDeleteBlock(ExecutableBlock):
    """Delete file
    This block attemps to delete a named file from the file system.
    If successful the 'Ok' link is followed, otherwist the 'Fail'
    link is followed"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, fileDelete_presentation)

    def code_text(self):
        return f"""
try:
    _fname={compilable(self.init['params'][0])}
except:
    _fname={quoted(self.init['params'][0])}
if _mach.filevars._ok_delete_file(_fname):
    _mach.link=0
    _mach.node={self.links[0]}
else:
    _mach.link=1
    _mach.node={self.links[1]}
"""

    def undoable_code_text(self):
        return self.code_text()

class FileExecBlock(ExecutableBlock):
    """Execute an OS command
    This block sets up an operating system process to execute a command as if
    typed from a 'console'.  If the parameter 'Synchronous' is true it waits
    until the process has completed before following the either 'Ok' link or
    the fail link if the exit code of the process is non-zero. Otherwise,
    the process is launched asynchronously (or 'in the background').  If the
    background process launches successfully, the 'Ok' link is followed
    immediately, and when the process finishes a 'ProcExit' event is generated.
    The exit code of the process is then available as _ev.exit_code if the
    event is waited for in a 'wait' instruction.
    If the 'fail' link is followed _os.message will be set to a description of
    the error."""

    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, fileExec_presentation)
        #if len(self.init['params']==1): #todo here remove this when no counter examples exist
        #    self.init['params'].append('0')

    def code_text(self):
        if self.init['params'][0] == '':
            return f"""
_fs.message='Cannot execute empty command'
_mach.node={self.init['links'][1]}
_mach.link=1
"""
        return f"""
try:
    _fname={compilable(self.init['params'][0])}
except:
    _fname={quoted(self.init['params'][0])}
_mach.create_process(_fname,{self.links} {",synch=True" if self.init['params'][1]=="1" else ""})
"""
    def undoable_code_text(self):
        return self.code_text()

class PlayMediaBlock(ExecutableBlock):
    """Play a sound or video file
    The actual program used to play sound and/or video files is system
    dependent.
    On Ubuntu Linux and its derivatives 'mpv' is a good option and can
    play sound-only if run with '--no-video' option.  Alternatively on
    most Linux systems 'aplay' can be used to play .wav, .raw, .au and
    .voc sound files.
    To play a sound-only file on Windows, a suitable media player needs
    to be installed, e.g.
        vlc (https://www.videolan.org/vlc/download-windows.html)
    or  mvp (https://mpv.io/installation/)

    If 'async' is selected the 'Ok' (or 'Fail') link will be followed
    immediately and a 'ClipEnd' event will be generated when the clip
    has finished playing, otherwise the instruction either waits until
    the clip is finished before following the 'Ok' link, or it follows
    the 'Fail' link immediately.

    If the program is stopped while any asynchronous clip is playing,
    the clip will be also be stopped. This means that when (e.g.)
    stepping through a program, it may appear that the instruction is
    not working.  A 'wait' instruction can be used to keep the program
    running whilst testing.

    If the 'Fail' link is followed, _fs.message will have a description
    of the error"""

    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, play_media_presentation)

    def code_text(self):
        if self.init['params'][0] == '':
            return f"""
_fs.message='Cannot play an empty file'
_mach.node={self.init['links'][1]}
_mach.link=1
"""
        return f"""
try:
    _fname={compilable(self.init['params'][1])}
except:
    _fname={quoted(self.init['params'][1])}
_mach.play_media({quoted(self.init['params'][0])},_fname,{self.links}{",synch=True" if self.init['params'][2]=="1" else ""})
"""
    def undoable_code_text(self):
        return self.code_text()

class FileAppendBlock(ExecutableBlock):
    """Append data to a text file
    This block appends to or creates a text file. Its behaviour depends
    on the type of data and the 'extension' of the file-name as follows:
    Note:  The encoding is taken from the (r/w) system variable
        '_fs.encoding'.
           The system variable '_fs.message' will be set to 'Ok' and the
        'Ok' link will be followed if the file was written successfully,
        otherwise 'File.message' will be an error message and the 'Fail'
        link will be followed.

    If the data is a Python 'str' it is appended directly to the file.
    If the data is a Python list of Python str objects, each element is
        written to the file followed by '\n' (new line).
    If the data is a table and the extension is 'html' the table is
        appended to the file as a html <table> element.
    If the data is a table and the extension is 'csv' the table field names
        followed by the table rows are appended as lines with comma-separated
        values. Each line is followed by a '\\n' (new line character).
    If the data can be converted to JSON representation, this is written
        to the file.
    """

    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, fileAppend_presentation)

    def code_text(self):
        if self.init['params'][0] == '':
            return f"""
_fs.message='Cannot append to empty filename'        
_mach.node={self.init['links'][1]}
_mach.link=1
"""

        return f"""
try:
    _fname={compilable(self.init['params'][1])}
except:
    _fname={quoted(self.init['params'][1])}
try:
    _what={compilable(self.init['params'][0])}
except:
    _what=None
if _mach.filevars._ok_append_to_file(_what,_fname):
    _mach.link=0
    _mach.node={self.links[0]}
else:
    _mach.link=1
    _mach.node={self.links[1]}
"""

    def undoable_code_text(self):
        return self.code_text()

class FileCopyBlock(ExecutableBlock):
    """Copy a file
    This block attempts to make a copy of a file.
    It can also create and append to 'zip' files by
    prefixing the destination filename with 'ZIP:'
    If the filename is prefixed with 'ZIP:DEFLATE:' the
    file is compressed as it is added to the zip file.
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, fileCopy_presentation)

    def code_text(self):
        if self.init['params'][0] == '':
            return f"""
_fs.message='Empty source filename'
_mach.node={self.init['links'][1]}
_mach.link=1
"""
        if self.init['params'][1] == '':
            return f"""
_fs.message='Empty destination filename'
_mach.node={self.init['links'][1]}
_mach.link=1
"""
        return f"""
try:
    _fsname={compilable(self.init['params'][0])}
except:
    _fsname={quoted(self.init['params'][0])}
try:
    _fdname={compilable(self.init['params'][1])}
except:
    _fdname={quoted(self.init['params'][1])}
if _mach.filevars._ok_copy_file(_fsname,_fdname):
    _mach.link=0
    _mach.node={self.links[0]}
else:
    _mach.link=1
    _mach.node={self.links[1]}
"""

    def undoable_code_text(self):
        return self.code_text()

class FileRenameBlock(ExecutableBlock):
    """Rename file
    This block renames a file in a folder. It does not move the file
    if the new filename is in a different folder
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, fileRename_presentation)

    def code_text(self):
        return f"""
try:
    _fsname={compilable(self.init['params'][0])}
except:
    _fsname={quoted(self.init['params'][0])}
try:
    _fdname={compilable(self.init['params'][1])}
except:
    _fdname={quoted(self.init['params'][1])}
if _mach.filevars._ok_rename_file(_fsname,_fdname):
    _mach.link=0
    _mach.node={self.links[0]}
else:
    _mach.link=1
    _mach.node={self.links[1]}
"""

    def undoable_code_text(self):
        return self.code_text()

class SwitchBlock(ExecutableBlock):
    """Choose code based on an expression ('switch' or 'case')
    An expession is evaluated in this instruction, and a link is
    chosen based on the value of the expression. If the expression
    is an integer, the values which choose a link should be an integer
    or a tuple, set or list of integers.  If it is a string the values
    choosing links should be comma-separated strings.
    """
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, switch_presentation)

    def code_text(self):
        def get_int_case_str(i):
            return f"""
        try:
            _item=iter({compilable(self.params[i])})
        except:
            _item=[{compilable(self.params[i])}]
        if _expr in _item:
            _mach.link={i}
            _mach.node={self.links[i]}
            break
"""
        def get_string_case_str(i):
            return f"""
        try:
            _item={compilable(self.params[i])}
        except:
            _item={quoted(self.params[i])}
        try:
            if _expr in _item.split(','):
                _mach.link={i}
                _mach.node={self.links[i]}
                break
        except: #Exception as e:
            _mach.log('SWITCH ERROR',level=2)
            break
"""
        def string_cases():
            return '\n'.join([get_string_case_str(i) for i in range(1,len(self.params))])
        def int_cases():
            return '\n'.join([get_int_case_str(i) for i in range(1,len(self.params))])

        return f"""
_mach.link=0
_mach.node={self.links[0]}
try:
    _expr={compilable(self.params[0])}
except:
    _expr={quoted(self.params[0])}
if isinstance(_expr,str):
    while True:
{string_cases()}
        break
elif isinstance(_expr,int):
    while True:
{int_cases()}
        break
"""
    def undoable_code_text(self):
        return self.code_text()

class ImageViewBlock(Block):
    """Show image on desktop or block-diagram"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, imageView_presentation)

class GraphicBlock(Block):
    """Show graphical item on desktop or block-diagram"""
    def __init__(self,diag,no,init=None):
        super().__init__(diag,no,init,graphic_presentation)


class BubblBlock(Block):
    """Executable link to BUBBL app"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, bubbl_presentation)
        self.runs=set()

class CommandBlock(Block):
    """Executable Operating System command"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, command_presentation)
        self.threads=set()

class WeblinkBlock(Block):
    """Web hyper-link"""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, weblink_presentation)

class ButtonBlock(ExecutableBlock):
    """Create a button on the current page (window)
    This block creates a button on a page which generates
    a BUBBL events when clicked by the user."""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, button_presentation)

    def code_text(self):
        return f"""
try:
    _text={compilable_not_a_tuple(self.params[0])}
except:
    _text={quoted(self.params[0])}
_page=_mach.current_page
{markups_dict(self.params[1:])}
try:
    _page.add_button_thing(False,text=_text,**_dict)
except: #Exception as e:
    _mach.log('Button defaulting to add_output',level=2)
    try:
        _page.add_output(_text)
    except:
        pass
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
       return f"""
try:
    _text={compilable_not_a_tuple(self.params[0])}
except:
    _text={quoted(self.params[0])}
_page=_mach.current_page
{markups_dict(self.params[1:])}
try:
    _page.add_button_thing(True,text=_text,**_dict)
except: #Exception as e:
    _mach.log('button defaulting to add_output',level=2)
    try:
        _page.add_output(_text)
    except:
        _mach.log('Unabled to output button text',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class TextEdBlock(ExecutableBlock):
    """Create a text-editor window on the current page (window)
    This block creates a text-editor window on a page which
    generates BUBBL events as the user edits the text."""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, texted_presentation)

    def code_text(self):
        return f"""
try:
    _default=str({compilable_not_a_tuple(self.params[0])})
except:
    _default={quoted(self.params[0])}
_page=_mach.current_page
{markups_dict(self.params[1:])}
try:
    _page.add_texted_thing(False,value=_default,**_dict)
except: #Exception as e:
    _mach.log('Failed to create texted',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
       return f"""
try:
    _default=str({compilable_not_a_tuple(self.params[0])})
except:
    _default={quoted(self.params[0])}
_page=_mach.current_page
{markups_dict(self.params[1:])}
try:
    _page.add_texted_thing(True,value=_default,**_dict)
except: #Exception as e:
    _mach.log('Failed to create texted',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class InputDispBlock(ExecutableBlock):
    """Create a text-input box on the current page (window)
    This block creates a text-input box ontext-editor window on a page which
    generates BUBBL events as the user edits the text."""

    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, inputdisp_presentation)

    def code_text(self):
        return f"""
try:
    _default=str({compilable_not_a_tuple(self.params[0])})
except:
    _default={quoted(self.params[0])}
_page=_mach.current_page
{markups_dict(self.params[1:])}
try:
    _page.add_input_thing(False,value=_default,**_dict)
except: #Exception as e:
    _mach.log('Failed to create input',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
       return f"""
try:
    _default=str({compilable_not_a_tuple(self.params[0])})
except:
    _default={quoted(self.params[0])}
_page=_mach.current_page
{markups_dict(self.params[1:])}
try:
    _page.add_input_thing(True,value=_default,**_dict)
except: #Exception as e:
    _mach.log('Failed to create input',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class CheckboxBlock(ExecutableBlock):
    """Create a check-box on the current page (window)
    This block creates a check-box widget on the current page which
    generates BUBBL events as the user checks/un-checks it."""

    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, checkbox_presentation)

    def code_text(self):
        return f"""
try:
    _prompt=str({compilable_not_a_tuple(self.params[0])})
except:
    _prompt={quoted(self.params[0])}
_page=_mach.current_page
{markups_dict(self.params[1:])}
try:
    _page.add_checkbox_thing(False,prompt=_prompt,**_dict)
except: #Exception as e:
    _mach.log('Failed to create checkbox',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
       return f"""
try:
    _prompt=str({compilable_not_a_tuple(self.params[0])})
except:
    _prompt={quoted(self.params[0])}

_page=_mach.current_page
{markups_dict(self.params[1:])}
try:
    _page.add_checkbox_thing(True,prompt=_prompt,**_dict)
except: #Exception as e:
    _mach.log('Failed to create checkbox',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class RadioBlock(ExecutableBlock):
    """Create a set of 'radio' buttons on the current page (window)
    This block creates a set of 'radio' buttons on the current page
    which generate BUBBL events as the user selects a button."""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, radio_presentation)

    def code_text(self,undoable='False'):

        nitems=sum(1 for _ in self.params if isinstance(_,str))
        def get_menu_items_str():
            if nitems==1 and self.params[0]!='':
                return f"_items={self.params[0]}.split(',')\n"
            p0="_items=[]\n"
            p1="\n".join(f"""
try:
    _item={compilable(p)}
    if not isinstance(_item,str):
        raise Exception()
    _items.append(_item)
except:
    _items.append({quoted(p)})
""" for p in self.params[:nitems])
            return p0+p1+'\n'
        return f"""{get_menu_items_str()}
_page=_mach.current_page
{markups_dict(self.params[nitems:])}
try:
    _page.add_radio_thing({undoable},items=_items,**_dict)
except: #Exception as e:
    _mach.log('Failed to create RadioGroup',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
       return self.code_text('True')

class ChoiceDispBlock(ExecutableBlock):
    """Create a 'choice' widget on the current page (window)
    This block creates a 'choice' widget on the current page.  The widget
    automatically adds scrolling if necessary and can be configured via
    markups to allow single or multiple selections.  The widget generates
    BUBBL events when choices are made."""
    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, choiceDisp_presentation)

    def code_text(self,undoable='False'):
        if self.params[0]=='':
            return """
_mach.runtime_error('Nothing to choose from')
"""
        return f"""
try:
    _items={self.params[0]}
except:
    _items={quoted(self.params[0])}
_page=_mach.current_page
{markups_dict(self.params[1:])}
_dict['items']=_items

try:
    _page.add_choice_thing({undoable},**_dict)
except: #Exception as e:
    _mach.log('Failed to create choice',level=2)
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
       return self.code_text(undoable='True')

class ScrollbarBlock(ExecutableBlock):
    """Create a 'scroll-bar' widget on the current page (window)
    This block creates a horizontal or vertical scrollbar on the
    current page. It generates BUBBL event as the user interacts
    with it."""

    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, scrollbar_presentation)

    def code_text(self):
        return f"""
_page=_mach.current_page
try:
    _low={compilable(self.params[0])}
    _high={compilable(self.params[1])}
except:
    _low=0
    _high=100
{markups_dict(self.params[2:])}
try:
    _page.add_scrollbar_thing(False,low=_low,high=_high,**_dict)
except:
    _page.add_output('Error: Scrollbars can only be output to pages')
_mach.node={self.init['links'][0]}
_mach.link=0
"""

    def undoable_code_text(self):
        return f"""
_page=_mach.current_page
try:
    _low={compilable(self.params[0])}
    _high={compilable(self.params[1])}
except:
    _low=0
    _high=100
{markups_dict(self.params[2:])}
try:
    _page.add_scrollbar_thing(True,low=_low,high=_high,**_dict)
except:
    _page.add_output('Error: scrollbars can only be output to pages')
_mach.node={self.init['links'][0]}
_mach.link=0
"""

class DialogBlock(ExecutableBlock): #here markups
    """Create a custom dialog
    This block binds together many user-interface widgets to make
    a flexible dialog widget.
    The dialog is defined by a table, and a unique name for this
    table should be given before creating the elements of the dialog.
    This can be done by selecting 'Edit parameters' from the right-
    click menu and entering a name for 'Definition table'.

    The 'Record/Dict' parameter is used to pass information to and
    from the dialog when it is run, and can be a dictionary or a
    table record.  The dictionary's keys or the table record's field-
    names should correspond to 'tag' fields of the dialog's widgets.
    These can be set up when the dialog is edited.

    When the dialog is run dictionary or record items which match widget
    tags are automatically updated as the user interacts with the dialog.
    Interactions with widgets without a tag trigger the 'event' link of the
    dialog instruction to be followed, with the system variable '_ev'
    capturing the widget details.  After processing the event the 'loop'
    link should be followed to continue with the dialog.

    If the 'Esc' link is followed from the dialog instruction, the
    'Record/Dict' value is restored to its initial state."""

    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, dialog_presentation)

    def code_text(self):
        return f"""
try:
    _name={compilable_not_a_tuple(self.params[0])}
except:
    _name={quoted(self.params[0])}
try:
    _t=_db[_name]
except KeyError:
    _t=_name
{markups_dict(self.params[2:])}
_mach.run_dialog({self.links},_t,{compilable_not_a_tuple(self.params[1])},False,**_dict)
"""
    def undoable_code_text(self):
        return self.code_text()

    def auxcode_text(self):
        return f"""
try:
    _name={compilable_not_a_tuple(self.params[0])}
except:
    _name={quoted(self.params[0])}
try:
    _t=_db[_name]
except KeyError:
    _t=_name
{markups_dict(self.params[2:])}
_mach.run_dialog({self.links},_t,{compilable_not_a_tuple(self.params[1])},True,**_dict)
"""
    def undoable_auxcode_text(self):
        return self.auxcode_text()


class EditorBlock(ExecutableBlock): #here markups
    """Pop-up a table/text editor
    """

    def __init__(self, diag, no, init=None):
        super().__init__(diag, no, init, editor_presentation)

    def code_text(self):
        result_ref=self.params[1]
        if result_ref=='':
            return f"""
_mach.link=1
_mach.node={self.links[1]}
"""
        if self.params[0]=='Text':
            if not is_valid_identifier(self.params[1]):
                if result_ref=='':
                    return f"""
_mach.link=1
_mach.node={self.links[1]}
"""
            return f"""
{markups_dict(self.params[2:])}
_mach.run_text_editor({self.links},"{self.params[1]}",**_dict)
"""
        return f"""
{markups_dict(self.params[2:])}
try:
    _table=_mach.get_table({compilable(self.params[1])})
except:
    _table=_mach.get_table({quoted(self.params[1])})
if _table is None:
    _mach.link=1
    _mach.node={self.links[1]}
else:
    try:
        _parent=_mach.current_page.window
    except:
        _parent=_mach.get_parent()
    _mach.run_table_editor(_parent,{self.links},_mach,_table,**_dict)
"""
    def undoable_code_text(self):
        return self.code_text()

class CallBlock(ExecutableBlock):
    """Call another block (diagram)
    This block encapsulates a call to another 'user-defined' block,
    the user-defined block (diagram) may have input parameters,
    output parameters and named 'links'
    """
    def __init__(self, diag, no, init=None):
        if init is None:
            self.target_name = ''
        else:
            self.target_name = init["params"][0]
        super().__init__(diag, no, init, call_presentation(self.target_name))
    def get_expr_text(self, vname, expr):
        if vname.startswith('@'):
            vname=vname[1:]
        return f"""
        try:
            _target.variables[{quoted(vname)}]={compilable(expr)}
        except:
            _target.variables[{quoted(vname)}]={quoted(expr)}
"""

    def get_undoable_expr_text(self, vname, expr):
        if vname.startswith('@'):
            vname=vname[1:]
        return f"""
        if {quoted(vname)} in _target.variables:
            _mach.add_undo(["targetvarassign",{quoted(self.target_name)},{quoted(vname)},_target.variables[{quoted(vname)}]])
        try:
            _target.variables[{quoted(vname)}]={compilable(expr)}
        except:
            _target.variables[{quoted(vname)}]={quoted(expr)}
"""

    def gen_code_text(self, aux):
        target_diag = self.diag.mach.diags[self.target_name]
        assignments = '\n'.join(
            [self.get_expr_text(vname, par)
               for vname, par in zip(target_diag.params[1:], self.params[1:])
             if is_valid_identifier(vname) or
                vname.startswith('@') and is_valid_identifier(vname[1:])])
        push="_mach.diag.nodes[_mach.node].links[0]" if aux else '_mach.node'
        result=f"""
try:
    _target=_mach.diags[{quoted(self.target_name)}]
    if _target==_mach.diag or any(diag==_target for (diag,_) in _mach.stack):
        _mach.runtime_error('BUBBL blocks cannot be called/run from themselves')
    else:
{assignments}
        _node=_target.links[{"1" if aux else "0"}]
        if _node!=0:
            _mach.stack.append((_mach.diag,{push}))
            _mach.diag=_target
            _mach.link=0
            _mach.node=_node
        else:
            _mach.node=0
except:
    _mach.link=0
    _mach.node={self.init['links'][0]}
"""
        return result
    def gen_undoable_code_text(self, aux):
        target_diag = self.diag.mach.diags[self.target_name]
        assignments = '\n'.join(
         [self.get_undoable_expr_text(vname, par)
            for vname, par in zip(target_diag.params[1:],
                                  self.params[1:])
          if is_valid_identifier(vname) or
             vname.startswith('@') and is_valid_identifier(vname[1:])
         ])
        push="_mach.diag.nodes[_mach.node].links[0]" if aux else "_mach.node"
        return f"""
try:
    _target=_mach.diags[{quoted(self.target_name)}]
    if _target==_mach.diag or any(diag==_target for (diag,_) in _mach.stack):
        _mach.runtime_error('BUBBL blocks cannot be called/run from themselves')
    else:
{assignments}
        _node=_target.links[{"1" if aux else "0"}]
        if _node!=0:
            _mach.add_undo(["pop"])
            _mach.stack.append((_mach.diag,{push}))
            _mach.diag=_target
            _mach.link=0
            _mach.node=_node
        else:
            _mach.node=0
except:
    _mach.link=0
    _mach.node={self.init['links'][0]}
"""

    def code_text(self):
        return self.gen_code_text(False)

    def undoable_code_text(self):
        return self.gen_undoable_code_text(False)

    def auxcode_text(self):
        return self.gen_code_text(True)

    def undoable_auxcode_text(self):
        return self.gen_undoable_code_text(True)

class ImportBlock(ExecutableBlock):
    """Run a block in target machine without stacking return.
    Wait until the target machine exits then update
    any variables from target machine attribute _wbackvals and
    follow the link in target machine attribute _link
    """

    def __init__(self, diag, no, init=None):
        if init is None:
            self.target_filename = ''
            self.target_diag=''
        else:
            self.target_filename= init["params"][0]
            self.target_diag = init["params"][1]

        import_init=diag.mach.app.get_imported_machine_init(self.target_filename)
        try:
            diag_sig=import_init['diags']['target_diag']['signature']
        except:
            diag_sig={"hasloop":False,
            "linknames":[],
            "params":["#DDD"]
            }


        pars=diag_sig["params"][1:]
        call_pars=[f'{self.target_diag}']
        for par in pars:
            fr=1 if par.startswith('@') else 0
            diag_sig["variables"][par[fr:]]=''
            call_pars.append(par[fr:])

        call_init={"params": call_pars, "type": "CALL",
                   "size": [1, 1], "pos": [0, 0], "links": [0]}
        used_nodes=import_init['diags']['main']['nodes']
        if used_nodes:
            self.node_no=max(int(n) for n in used_nodes)+1
        else:
            self.node_no=1
        import_init['diags']['main']['nodes'][f'{self.node_no}']=call_init

        main_init=import_init['diags']['main']
        if len(main_init['nodes'])==0:
            self.node_base=1
        else:
            self.node_base=max(int(n) for n in main_init['nodes'])

        main_init['nodes'][f'{self.node_base}']=call_init

        super().__init__(diag, no, init,
                         import_presentation(import_init,
                                             self.target_diag))

class AsyncBlock(ExecutableBlock):
    """Run a block in target machine without stacking return
    Note: When target machine exits it generates Async event"""
    def __init__(self, diag, no, init=None):
        if init is not None:
            target_name = init["params"][0]
            target_diag = init["params"][1]
            mach_init=get_imported_machine_init(target_name)
            try:
                sig=mach_init["diags"][target_diag]["signature"]
                mach_pars=sig["params"][1:]
            except Exception: #KeyError:
                mach_pars=[]

            while len(init["params"])-2<len(mach_pars):
                init["params"].append('')

        else:
            target_name = ''
            target_diag = ''

        super().__init__(diag, no, init,
                         async_presentation(target_name,target_diag))

    def get_expr_text(self, vname, expr):
        if vname.startswith('@'):
            vname=vname[1:]
        return f"""
try:
    _variables[{quoted(vname)}]={compilable(expr)}
except:
    _variables[{quoted(vname)}]={quoted(expr)}
"""
    def code_text(self):
        init=get_imported_machine_init(self.params[0])
        if init is None or not self.params[1] in init["diags"]:
            return f"_mach.link=0\n_mach.node={self.links[0]}"
        params=init["diags"][self.params[1]]["signature"]["params"][1:]
        assignments = '\n'.join(
            [self.get_expr_text(vname, par)
               for vname, par in zip(params,self.params[2:])
             if is_valid_identifier(vname) or
                vname.startswith('@') and is_valid_identifier(vname[1:])])
        return f"""
_variables={{}}
{assignments}
_mach.run_async_block("{self.params[0]}",
    "{self.params[1]}",
    _variables)
_mach.link=0
_mach.node={self.links[0]}
"""
    def undoable_code_text(self):
        return self.code_text()

display_blocks= (
   ArcBlock,
   ButtonBlock,
   CheckboxBlock,
   ChoiceDispBlock,
   EllipseBlock,
   ImageBlock,
   InputDispBlock,
   LineBlock,
   PolygonBlock,
   RadioBlock,
   ScrollbarBlock,
   TextEdBlock,
   WriteBlock
)

def library(params):
    return {name:code for [name,code] in params}

block_factory = {
    'ASSIGN':  AssignBlock,
    'IF':  IfBlock,
    'WAIT':  WaitBlock,
    'SWITCH':SwitchBlock,
    'FOR':  ForBlock,
    'LOOP':  LoopBlock,
    'CALL':  CallBlock,
    'LINK':  LinkBlock,
    'PYTHON': PythonBlock,
    'JOIN':JoinBlock,

    'CREATE':  CreateBlock,
    'SORT': SortBlock,
    'INSERT':  InsertBlock,
    'DELETE':  DeleteBlock,
    'DESTROY':  DestroyBlock,
    'UPDATE':  UpdateBlock,
    'SELECT':  SelectBlock,

    'PAGE':  PageBlock,
    'PRINT': PrintBlock,
    'PAGE_CLOSE':  PageCloseBlock,
    'PAGE_CLEAR':  PageClearBlock,
    'PAGE_UPDATE':  PageUpdateBlock,

    'WRITE':  WriteBlock,
    'LINE': LineBlock,
    'IMAGE':  ImageBlock,
    'POLYGON':  PolygonBlock,
    'RECT':  RectangleBlock,
    'ELLIPSE':  EllipseBlock,
    'ARC': ArcBlock,

    'INPUT':  InputBlock,
    'CHOICE':  ChoiceBlock,
    'ASK_USER':  AskUserBlock,
    'MENU':  MenuBlock,
    'ALERT':  AlertBlock,
    'FILE_MENU':  FileMenuBlock,
    'COLOUR_MENU':  ColourMenuBlock,
    'DIALOG': DialogBlock,
    'EDITOR':EditorBlock,
    'PLAY':PlayMediaBlock,
    'FILE_MKDIR' : FileMkDirBlock,
    'FILE_SAVE':  FileSaveBlock,
    'FILE_APPEND':  FileAppendBlock,
    'FILE_DELETE':  FileDeleteBlock,
    'FILE_RENAME':  FileRenameBlock,
    'FILE_COPY':  FileCopyBlock,
    'FILE_EXECUTE':  FileExecBlock,

    'FORMULA':  FormulaBlock,
    'VARIABLE':  VariableBlock,
    'DBVARIABLE': DBVariableBlock,
    'TABLE':  TableViewBlock,
    'TEXT':  TextBlock,
    'IMAGE_VIEW':ImageViewBlock,

    'BUTTON':  ButtonBlock,
    'SCROLLBAR': ScrollbarBlock,
    'INPUTDISP': InputDispBlock,
    'CHOICEDISP': ChoiceDispBlock,
    'CHECKBOX': CheckboxBlock,
    'RADIO': RadioBlock,
    'TEXTED': TextEdBlock,
    'BUBBL':  BubblBlock,
    'COMMAND':  CommandBlock,
    'WEBLINK':  WeblinkBlock,
    'GRAPHIC': GraphicBlock,
    'IMPORT':ImportBlock,
    'ASYNC':AsyncBlock,

}

def get_block(diag, no, init):
    return block_factory[init["type"]](diag, no, init)
