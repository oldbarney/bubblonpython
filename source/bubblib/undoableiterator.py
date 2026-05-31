"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from .iset import Iset

class Undoable_Iset:
    def __init__(self,intset):
        self.intset=intset
        self.last=0 if intset.is_empty() else intset[0] - 1
    def __iter__(self):
        return self

    def __next__(self):
        if len(self.intset)==0:
            raise StopIteration
        if self.last>=self.intset.outs[-1]-1:
            raise StopIteration
        self.last=self.intset.next(self.last)
        return self.last

    def uniterate(self):
        self.last=self.intset.prev(self.last)

class UndoableIndexableIterator:
    def __init__(self,indexable):
        self.indexable=indexable
        self.index=0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index==len(self.indexable):
            raise StopIteration
        result=self.indexable[self.index]
        self.index+=1
        return result

    def uniterate(self):
        self.index-=1

class UndoableIterable:
    def __init__(self,iterable):
        self.iter=iterable.__iter__()
        self.history=[]
        self.index=0

    def __iter__(self):
        return self

    def uniterate(self):
        self.index-=1

    def __next__(self):
        if self.index<len(self.history):
            result=self.history[self.index]
        else:
            result=self.iter.__next__()  #StopIteration may be raised
            self.history.append(result)
        self.index+=1
        return result

class UndoableUnitaryIterable:
    def __init__(self,iterable):
        self.iter=iterable
        self.done=False

    def __iter__(self):
        return self

    def uniterate(self):
        self.done=False

    def __next__(self):
        if not self.done:
            self.done=True
            return self.iter
        raise StopIteration

def undoable_iterator(iterable):
    if isinstance(iterable,Iset):
        #print(f'getting undoable intsetiterator:{iterable}')
        return Undoable_Iset(iterable)
    if isinstance(iterable,(list,tuple,str)):
        #print(f'getting undoable indexediterator:{iterable}')
        return UndoableIndexableIterator(iterable)
    try:
        _=iterable.__iter__()
        #print(f'getting undoable iterable:{iterable}')
        return UndoableIterable(iterable)
    except:
        return UndoableUnitaryIterable(iterable)