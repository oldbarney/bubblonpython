"""Defines RawTable and Table classes
These classes work with the built in 'Create','Destroy',
'Insert','Update','Delete' and 'Sort' instructions.
Tables have named fields and rows numbered from 0.
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"

from bubblib.iset import Iset

if __name__ == '__main__':
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .utils import get_prefixed_substitutions, compilable, quoted, log

class TableIterator:
    def __init__(self, table):
        self.table = table
        self.last = -1

    def __iter__(self):
        self.last = -1
        return self

    def __next__(self):
        self.last += 1
        if self.last >= len(self.table):
            raise StopIteration
        return self.table[self.last]


class ReverseTableIterator:
    def __init__(self, table):
        self.table = table
        self.last = len(table) - 1

    def __iter__(self):
        self.last = len(self.table) - 1
        return self

    def __next__(self):
        if self.last == -1:
            raise StopIteration
        result = self.table[self.last]
        self.last -= 1
        return result


def default_for_field_type(field_type):
    if field_type == 'str':
        return ""
    elif field_type == 'num':
        return 0
    elif field_type == 'int':
        return 0
    elif field_type == 'float':
        return 0.0
    elif field_type == 'complex':
        return 0 + 0j
    elif field_type.startswith == 'choice':
        return field_type.split(",")[1]
    elif field_type=='iset':
        return Iset()
    else:
        return ''


def get_typed_field_value(value, field_type):
    if field_type == 'str':
        try:
            return str(value)
        except:
            return ""
    try:
        if isinstance(value, {'int': int, 'float': (int, float),
                              'num': (int, float, complex), 'none': object}[
            field_type]):
            return value
    except:
        pass

    if field_type == 'set':
        try:
            return set(value)
        except:
            return set()
    if field_type=='iset':
        try:
            return Iset(value)
        except:
            return Iset()
    elif field_type.startswith == 'choice':
        if value in field_type.split(",")[1:]:
            return value
        return field_type.split(",")[1]
    return ''


class AbstractRow:
    pass


def row_factory(fieldnames, values):
    class Row(AbstractRow):
        __slots__ = fieldnames
        def __init__(self):
            for fn, fv in zip(fieldnames, values):
                setattr(self, fn, fv)
    return Row()


class RawTable:
    # descendants must implement:
    #  get_row(index)
    #  insert_row(index,row,undoable)
    #  replace_row(index,row) or ok_swap_fields
    #  remove_row(index,undoable)
    #  __len__(self)
    _new_table_no=0
    @classmethod
    def new_table_name(cls):
        cls._new_table_no+=1
        return f'table_{cls._new_table_no}'

    def __init__(self, name, field_names,
                 defaults=None):
        self.field_types = [f[f.index(':') + 1:] if ':' in f else "none" for f
                            in field_names]
        self.field_names = [fieldname.split(':')[0] for fieldname in
                            field_names]
        self.table_name = name
        if defaults == None:
            self.defaults = [default_for_field_type(self.field_types[i]) for i
                             in range(len(field_names))]
        else:
            self.defaults = defaults

        class Row(AbstractRow):
            __slots__ = self.field_names

            def __init__(self, fields):
                for fn, fv in zip(self.__slots__, fields):
                    setattr(self, fn, fv)

            def get_list(self):
                return [getattr(self, f) for f in self.__slots__]

            def get_dict(self):
                return {f:getattr(self,f) for f in self.__slots__}

            def to_html(self):
                def poss_quoted(d):
                    d = str(d)
                    if d.find(',') > -1:
                        return quoted(d)
                    return d

                return '<td>' + '</td><td>'.join(
                    poss_quoted(d) for d in self.get_list()) + '</td>'

            def to_csv(self):
                def sv(v):
                    v = str(v)
                    if v.find(',') > -1:
                        return quoted(v)
                    return v

                return ','.join(sv(d) for d in self.get_list())

            def __str__(self):
                return ','.join([str(getattr(self, f)) for f in self.__slots__])

        self.Row = Row

    def __iter__(self):
        return TableIterator(self)

    def __reversed__(self):
        return ReverseTableIterator(self)

    def empty_clone(self, name):
        return RawTable(RawTable.new_table_name(), self.field_specs(), self.defaults)

    def to_csv(self):
        return ','.join(fn for fn in self.field_names) + '\n' + \
               '\n'.join(
                   self.get_row(r).to_csv for r in self.all_records()) + '\n'

    @property
    def blank_row(self):
        return self.Row(self.defaults)

    def rename_field(self, fieldname, newname):
        pass

    def all_records(self):
        return range(self.__len__())

    def rows_matching(self, field_name, field_value,match_func=None):
        result = []
        if match_func is None:
            match_func=lambda a,b:a==b
        for i, r in enumerate(self, 0):
            if match_func(getattr(r, field_name),field_value):
                result.append(i)
        return result

    def __str__(self):
        return f'Table({",".join(self.field_names)}) with {self.__len__()} {"recs" if self.__len__() != 1 else "rec"}'

    def field_specs(self):
        return [fn + ':' + ft for fn, ft in
                zip(self.field_names, self.field_types)]

    def full_field_specs(self):
        return [[fn, ft, fd] for fn, ft, fd in
                zip(self.field_names, self.field_types, self.defaults)]

    def __getitem__(self, row):
        if isinstance(row,int):
            if row<0:
                row+=self.__len__()
            if row in range(self.__len__()):
                return self.get_row(row)
            return None
            raise IndexError

        if isinstance(row, slice):  # todo here use slice.indices(len)
            # (start,stop,step=slice.indices(self.__len__())
            # start+=1 if start==0 else 0   ???
            # print('YiPPEE we have a slice')
            start = row.start
            stop = row.stop
            step = row.step
            if step is None:
                step=1
            if start is None:
                start=0
            if stop is None:
                if step>0:
                    stop=self.__len__()
                else:
                    stop=-1
            if start<0:
                start+=self.__len__()
            if stop<0:
                stop+=self.__len__()

            result = self.empty_clone('')

            for i in range(start, stop, step):
                result.insert_row(-1, self.get_row(i))
            return result

        if isinstance(row, set) and all(isinstance(el, int) for el in row):
            result = self.empty_clone('')
            row = sorted(list(row))

            for i in row:
                if i >= 0 and i < self.__len__():
                    result.insert_row(-1, self.Row(self.get_row(i).get_list()))
            return result

        if isinstance(row, Iset):
            result = self.empty_clone('')
            for i in row & self.all_records():
                result.insert_row(-1, self.Row(self.get_row(i).get_list()))
            return result

        if isinstance(row, str):
            try:
                fn, row = row.split(
                    '==')  # todo here could extend to other comparison operators >,>=,<,<=, and or in like etc.
                for i in range(self.__len__()):
                    result = self.get_row(i)
                    if f'{getattr(result, fn, None)}' == row:
                        return result
            except Exception as e:
                log('Bad table lookup',e,level=2)
            return None

        try:    #In case of integer float values!
            row=int(row)
            if row in range(self.__len__()):
                return self.get_row(row)
            if row in range(-self.__len__(), -1):
                return self.get_row(self.__len__() + row)
        except:
            return None

    def ok_swap_fields(self, row, values: dict):
        # return a list of previous values for field updates
        # print(f'ok_swap_fields row:{row}, values:{values}')
        if row<0:
            row+=self.__len__()
        try:
            oldrow = self.get_row(row)
            newrow = self.Row(
                [values[fn] if fn in values else getattr(oldrow, fn) for fn in
                 self.field_names])
            self.replace_row(row, newrow)
            for f in values:
                values[f] = getattr(oldrow, f)
            return True
        except Exception as e:
            log('ok_swap_fields_error:',e,level=2)
            return False


    def get_undoable_update_code(self,field_val_pairs):
        """ first separate rec"""
        def get_undoable_pair(lval, expr_in):
            expr = compilable(
                get_prefixed_substitutions(self.field_names, '_rec.', expr_in))
            if expr_in==expr: #Ensure no namespace errors
                lval=get_prefixed_substitutions(self.field_names, '_rec.', lval)
            if lval.startswith('_rec.') and lval[5:] in self.field_names:
                return f'''
_updates["{lval[5:]}"]={lval}
try:
    {lval}={expr}
except:
    {lval}={quoted(expr)}'''
            else:
                return f'''
try:
    _mach.add_undo(['varassign',"{lval}",{lval}])
except:
    _mach.add_undo(['vardel',"{lval}"])
try:
    {lval}={expr}
except:
    {lval}={quoted(expr)}
'''
        return '_updates={}\n' + '\n'.join(
            get_undoable_pair(f, v) for [f, v] in field_val_pairs) + f'''
if _updates:
    _mach.add_undo(['tableupdate',_table,_rn,_updates])
'''

    def get_update_code(self, field_val_pairs, undoable):
        if undoable:
            return self.get_undoable_update_code(field_val_pairs)
        #
        def get_pair(lval, expr):
            expr = compilable(
                get_prefixed_substitutions(self.field_names, '_rec.', expr))
            return f'''
try:
    {lval}={compilable(expr)}
except:
    {lval}={quoted(expr)}
'''
        return '\n'.join(
            [get_pair(f, v) for [f, v] in field_val_pairs]) + '\n'


    def get_select_expr(self, expr):
        # print(f'table.get_select_expr({expr})')

        result = compilable(
            get_prefixed_substitutions(self.field_names, '_rec.', expr))

        # print(f'returning:{result}')

        return f"""try:
    _in={result}
except Exception as e:
    _mach.log('Invalid selection',e,level=2)
    _in=False"""
        # return expr
    def __rshift__(self,other):
        return self.__getitem__(Iset(other))



class Table(RawTable):
    def __init__(self, name, field_names, defaults=None, machine=None):
        RawTable.__init__(self, name, field_names, defaults)
        self.mach = machine
        self._data = []

    def update_or_insert_record(self, field, value, where_key, equals_value):
        rows=self.rows_matching(where_key,equals_value)
        if rows:
            setattr(self[rows[0]],field,value)
        else:
            row=self.blank_row
            setattr(row,field,value)
            setattr(row,where_key,equals_value)
            self.insert_row(-1,row)

    def insert_row(self, ind, row, undoable=True):
        if isinstance(row, list):
            row = self.Row(row)
        if ind < 0 or ind > len(self._data):
            ind = len(self._data)
        if undoable:
            if self.mach is not None:
                self.mach.undo_list.append(["tabledelete",
                                            self.table_name,
                                            ind])
        self._data.insert(ind, row)

    def remove_row(self, ind, undoable=True):
        try:
            row = self._data.pop(ind)
            if undoable:
                if self.mach is not None:
                    self.mach.undo_list.append(["tableinsert",
                                                self.table_name,
                                                ind,
                                                row])
            return row
        except:
            log('Trying to remove non existent row', ind,level=2)
            return None

    def pop(self,ind=-1):
        return self.remove_row(ind,self.mach.undoable)

    def replace_row(self, ind, newrow):
        self._data[ind] = newrow

    def get_row(self, index):
        return self._data[index]

    def empty_clone(self, name):
        return Table(RawTable.new_table_name(), self.field_specs(), self.defaults)


    def rename_field(self, fieldname, newname):
        i = self.field_names.index(fieldname)
        new_field_names = list(self.field_names)
        new_field_names[i] = newname

        class NewRow(AbstractRow):
            __slots__ = new_field_names

            def __init__(self, fields):
                for fn, fv in zip(self.__slots__, fields):
                    setattr(self, fn, fv)

            def get_list(self):
                return [getattr(self, f) for f in self.__slots__]

            def get_dict(self):
                return {f:getattr(self,f) for f in self.__slots__}

            def to_html(self):
                return '<td>' + '</td><td>'.join(
                    str(d) for d in self.get_list()) + '</td>'

            def to_csv(self):
                def sv(v):
                    v = str(v)
                    if v.find(',') > -1:
                        return quoted(v)
                    return v

                return ','.join(sv(d) for d in self.get_list())

            def __str__(self):
                return ','.join([str(getattr(self, f)) for f in self.__slots__])

        for rn in self.all_records():
            old_row = self.get_row(rn)
            self.replace_row(rn, NewRow(
                [getattr(old_row, fn) for fn in self.field_names]))
        self.Row = NewRow
        self.field_names = new_field_names

    def __len__(self):
        return len(self._data)

    def to_html(self):
        return '<table>\n<th><td>' + '</td><td>'.join(
            fn for fn in self.field_names) + '</td><th>\n' + \
               '\n'.join('<tr>' + self.get_row(r).to_html() + '<\tr>' for r in
                         self.all_records()) + '\n</table>'

    def to_csv(self):
        return ','.join(fn for fn in self.field_names) + '\n' + \
               '\n'.join(
                   self.get_row(r).to_csv for r in self.all_records()) + '\n'

    def sort(self,field_names,descending,undoable):
        if field_names==[]:
            field_names=self.field_names[:1]
        field_funcs=[]
        for fn in field_names:
            if fn.endswith(':cased'):
                wfn=fn[:-6]
                field_funcs.append(lambda row,wfn=wfn:getattr(row,wfn))
            else:
                def func(row,fn=fn):
                    result=getattr(row,fn)
                    if isinstance(result,str):
                        return result.lower()
                    return result
                field_funcs.append(func)

        try:
            def get_sort_row(index):
                row=self._data[index]
                return [func(row) for func in field_funcs]+[index]
            data = sorted([get_sort_row(i) for i in range(len(self))],
                          reverse=descending)
            order=[r[-1] for r in data]
            if undoable:
                self.mach.add_undo(['tablesort',
                                   self.table_name,
                                   order])
            old_order=self[:]
            self._data.clear()
            for i in order:
                self._data.append(old_order[i])
        except:
            log('Failed to sort',self.table_name,'with',field_names,level=2)

    def unsort(self,order):
        log('unsorting')
        #reorder=[0]*min(len(order),len(self))
        #for i,pos in enumerate(order):
        #    reorder[pos]=i
        old_order=self[:]
        self._data.clear()
        for i in order:
            self._data.append(old_order[i])

if __name__ == "__main__":
    t = Table('table', ["f1", "f2", "f3:num"])
    print(f't={t}')
    t.insert_row(0, [1, 2, 3])
    print(f't={t}')
    print(f't[1]={t[1]}')

    t.insert_row(1, ["r21", "r32", 43])
    print(t[2])

    print(t.field_types)
    print(t.field_names)
    print('t[2].f3=' + str(t[2].f3))
    print(f't={t}')
    print(f't[1]={t[1]}')
    print(f't[2]={t[2]}')

    print(f't[1].f1={t[1].f1}')
    print(f't[1].f3={t[1].f3}')
    print(f't[2][2]={t[2][2]}')
    print(f't[2]["f3"]={t[2]["f3"]}')
    print(f't[2].f3={t[2].f3}')