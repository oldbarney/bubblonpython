"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from collections import deque
class History:
    def __init__(self):
        self.data={}

    def add_to_history(self,key,value,max_length=20):
        if not key in self.data:
            self.data[key]=deque()
        queue=self.data[key]
        if value in queue:
            queue.remove(value)
        while len(queue)>=max_length:
            queue.pop()
        queue.appendleft(value)

    def get_jsonable(self):
        return {k:list(self.data[k]) for k in self.data}

    def clear(self,key):
        if key in self.data:
            self.data[key].clear()

    def get_list(self,key):
        try:
            return list(self.data[key])
        except KeyError:
            return []

    def replace_list(self,key,replacement):
        for value in reversed(replacement):
            self.add_to_history(key,value)



class HistoryTable:
    def __init__(self,table,max_length=20):
        self.table=table
        self.max_length=max_length

    def add(self,key,value):
        rows=self.table.rows_matching('key',key)
        for r in rows:
            if self.table[r].value==value:
                break
        else:
            r=rows[0] if len(rows)==self.max_length else None
        if r is not None:
            self.table.remove_row(r)
        self.table.insert_row(-1,[key,value])

    def get_list(self,key):
        rows=self.table.rows_matching('key',key)
        return [self.table[row].value for row in rows]

