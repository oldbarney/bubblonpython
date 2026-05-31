"""
This class implements

"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"


class _Iterator:
    def __init__(self, i_set):
        self.i_set = i_set
        # print(f"Iset={Iset}")
        # assert(isinstance(Iset,Iset))
        if len(i_set) == 0:
            self.last = None
        else:
            self.last = i_set.ins[0] - 1

    def __iter__(self):
        return self

    def __next__(self):
        if self.last is None:
            raise StopIteration
        if self.last >= self.i_set.outs[-1] - 1:
            raise StopIteration
        self.last = self.i_set.next(
            self.last)  # raise StopIteration as necessary
        return self.last


class _ReverseIterator:
    def __init__(self, i_set):
        self.i_set = i_set
        if len(i_set) == 0:
            self.last = None
        else:
            self.last = i_set[-1] + 1

    def __iter__(self):
        return self

    def __next__(self):
        if self.last is None:
            raise StopIteration
        if self.last <= self.i_set.ins[0]:
            raise StopIteration
        self.last = self.i_set.prev(self.last)
        return self.last


class IndexedIterator:
    def __init__(self,i_set,indexed):
        self.i_set = i_set
        # print(f"Iset={Iset}")
        # assert(isinstance(Iset,Iset))
        if len(i_set) == 0:
            self.last = None
        else:
            self.last = i_set.ins[0] - 1
        self.indexed=indexed

    def __iter__(self):
        return self

    def __next__(self):
        if self.last is None:
            raise StopIteration
        if self.last >= self.i_set.outs[-1] - 1:
            raise StopIteration
        self.last = self.i_set.next(
            self.last)  # raise StopIteration as necessary
        return self.indexed[self.last]

class Iset:

    def __init__(self, *args,**kwargs):
        self.ins = []
        self.outs = []

        if 'indexed' in kwargs:
            self._indexed=kwargs['indexed']
        else:
            self._indexed=None

        if len(args) == 0:
            return
        elif len(args) == 1:
            par = args[0]
            if isinstance(par, Iset):
                self.ins[:] = par.ins
                self.outs[:] = par.outs
                return
            elif isinstance(par, range):
                if par.step == 1 and par.start < par.stop:
                    self.ins.append(par.start)
                    self.outs.append(par.stop)
                else:
                    for i in par:
                        self.add_element(i)
                return

            elif isinstance(par, int):
                self.ins.append(par)
                self.outs.append(par + 1)
                return
            elif isinstance(par,str):
                try:
                    if par.startswith('{') and par.endswith('}'):
                        par=par[1:-1]
                        if par=='':
                            return
                        pars=par.split(',')
                        res=Iset()
                        for part in pars:
                            parts=part.split('..')
                            if len(parts)==1:
                                res.add_element(int(parts[0]))
                            else:
                                res|=Iset(range(int(parts[0]),int(parts[1])+1))
                        self.ins=res.ins
                        self.outs=res.outs
                        return
                except Exception as e:
                    return
                    #print(f'_Iset cannot be created from {par} {e}')
            try:
                it = iter(par)
                for i in it:
                    self.add_element(i)
                return
            except Exception:
                raise (TypeError(
                    '_Iset can only be created empty or from Iset, int(s), or iterator over ints'))
        try:
            for i in args:
                self.add_element(i)
        except Exception:
            raise (TypeError(
                'Iset can only be created empty or from Iset, int(s), or iterator over ints'))

    @property
    def indexed(self):
        if self._indexed is not None:
            return IndexedIterator(self,self._indexed)
        return None

    def __iter__(self):
        return _Iterator(self)

    def __reversed__(self):
        return _ReverseIterator(self)

    def __getitem__(self, n):
        if isinstance(n, int):
            if n < 0:
                n += self.__len__()
                if n < 0:
                    raise IndexError(
                        f'Iset index {n - self.__len__()} out of range')
            if n >= self.__len__():
                raise IndexError(f'Iset index {n} out of range')
            for i, o in zip(self.ins, self.outs):
                if n < o - i:
                    return i + n
                else:
                    n -= (o - i)
            raise Exception('Iset should not raise this')
        elif isinstance(n, Iset):
            return self.__rshift__(n)
        if isinstance(n, slice):
            #print(n,n.start,n.stop,n.step)
            start = n.start
            stop = n.stop
            step = n.step
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
            if step>0:
                return Iset(self[i] for i in range(max(0,start),min(self.__len__(),stop),step))
            else:
                return Iset(self[i] for i in range(min(self.__len__(),start),max(-1,stop),step))


        raise IndexError(f'Iset invalid index: {n}')



    def __rshift__(self, n):  # index to indexed
        if isinstance(n, int):
            return self.__getitem__(n)
        if not isinstance(n, Iset):
            n = Iset(n)
        res = Iset()
        for i in n:
            el = self.__getitem__(i)
            res.add_element(el)
        return res

    def __lshift__(self, index):  # indexed to index == lookup
        if isinstance(index, int):
            return self.__index__(index)
        if not isinstance(index, Iset):
            index = Iset(index)
        res = Iset()
        for i in index:
            el = self.__index__(i)
            res.add_element(el)
        return res

    def __len__(self):
        return sum(self.outs) - sum(self.ins)

    def __bool__(self):
        return self.ins!=[]

    def reversed(self):
        return _ReverseIterator(self)

    def is_empty(self):
        return len(self.ins) == 0

    def __eq__(self, other):
        if isinstance(other, Iset):
            return bool(self.ins == other.ins and self.outs == other.outs)
        if isinstance(other, int):
            return bool(self.__len__() == 1 and self.ins[0] == other)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def _find_block_gt(self,
                       n):  # Returns index to element after n (called with at least 3 blocks)
        low = 0
        h = len(self.ins) - 1
        while h != low:
            m = (low + h) // 2
            if self.outs[m] - 1 > n:
                h = m
            else:
                low = m + 1
        return low

    def _find_block_lt(self,
                       n):  # Returns index to element before n(called with at least 3 blocks)
        low = 0
        h = len(self.ins) - 1
        while h != low:
            m = (low + h + 1) // 2
            if self.ins[m] < n:
                low = m
            else:
                h = m - 1
        return low

    def add_element(self, el):
        if self.ins == []:
            self.ins.append(el)
            self.outs.append(el + 1)
            return
        if self.outs[-1] == el:
            self.outs[-1] += 1
            return
        if self.ins[0] == el + 1:
            self.ins[0] -= 1
            return
        if el < self.ins[0]:
            self.ins.insert(0, el)
            self.outs.insert(0, el + 1)
            return
        if el == self.outs[-1]:
            self.outs[-1] += 1
            return
        if el > self.outs[-1]:
            self.ins.append(el)
            self.outs.append(el + 1)
            return

        res = self + Iset(el)

        self.ins = res.ins
        self.outs = res.outs

    def next(self, n):
        if len(self.ins) > 3:
            m = self._find_block_gt(n)
            if n < self.ins[m]:
                return self.ins[m]
            return n + 1
        for i in range(3):
            if n < self.ins[i]:
                return self.ins[i]
            if n < self.outs[i] - 1:
                return n + 1
        raise IndexError('There is no next')

    def prev(self, n):
        li = len(self.ins)
        if li > 3:
            m = self._find_block_lt(n)
            if n > self.outs[m]:
                return self.outs[m] - 1
            return n - 1

        for i in range(li - 1, -1, -1):
            if n >= self.outs[i]:
                return self.outs[i] - 1
            if n > self.ins[i]:
                return n - 1
        raise IndexError('There is no prev')

    def _get_amalgamated(self, other):
        tn = len(self.ins)
        on = len(other.ins)
        bound = [None] * (tn + on) * 2
        mode = [None] * (tn + on) * 2
        this_i = 0
        that_i = 0
        if self.ins[0] < other.ins[0]:
            bound[0] = self.ins[0]
            mode[0] = 1
        elif self.ins[0] > other.ins[0]:
            mode[0] = 2
            bound[0] = other.ins[0]
        else:
            mode[0] = 3
            bound[0] = self.ins[0]
        n = 0
        while this_i < tn and that_i < on:
            m = mode[n]
            n += 1
            if m == 0:  # not a not b
                if self.ins[this_i] < other.ins[that_i]:
                    mode[n] = 1
                    bound[n] = self.ins[this_i]
                elif self.ins[this_i] > other.ins[that_i]:
                    mode[n] = 2
                    bound[n] = other.ins[that_i]
                else:
                    mode[n] = 3
                    bound[n] = self.ins[this_i]
            elif m == 1:  # a not b
                if self.outs[this_i] < other.ins[that_i]:
                    mode[n] = 0
                    bound[n] = self.outs[this_i]
                    this_i += 1
                elif self.outs[this_i] > other.ins[that_i]:
                    mode[n] = 3
                    bound[n] = other.ins[that_i]
                else:
                    mode[n] = 2
                    bound[n] = self.outs[this_i]
                    this_i += 1
            elif m == 2:  # b not a
                if self.ins[this_i] > other.outs[that_i]:
                    mode[n] = 0
                    bound[n] = other.outs[that_i]
                    that_i += 1
                elif self.ins[this_i] < other.outs[that_i]:
                    mode[n] = 3
                    bound[n] = self.ins[this_i]
                else:
                    mode[n] = 1
                    bound[n] = other.outs[that_i]
                    that_i += 1
            else:  # a and b
                if self.outs[this_i] < other.outs[that_i]:
                    mode[n] = 2
                    bound[n] = self.outs[this_i]
                    this_i += 1
                elif self.outs[this_i] > other.outs[that_i]:
                    mode[n] = 1
                    bound[n] = other.outs[that_i]
                    that_i += 1
                else:
                    mode[n] = 0
                    bound[n] = self.outs[this_i]
                    this_i += 1
                    that_i += 1
        while this_i < tn:
            m = mode[n]
            n += 1
            if m == 0:
                mode[n] = 1
                bound[n] = self.ins[this_i]
            else:
                mode[n] = 0
                bound[n] = self.outs[this_i]
                this_i += 1
        while that_i < on:
            m = mode[n]
            n += 1
            if m == 0:
                mode[n] = 2
                bound[n] = other.ins[that_i]
            else:
                mode[n] = 0
                bound[n] = other.outs[that_i]
                that_i += 1
        n += 1
        return mode, bound, n

    def __add__(self, other):
        return self.__or__(other)

    def __iadd__(self, other):
        return self.__ior__(other)

    def __ior__(self, other):
        res = self.__or__(other)
        self.ins = res.ins
        self.outs = res.outs
        return self

    def __or__(self, other):
        if isinstance(other, int):
            res = Iset(self)
            res.add_element(other)
            return res
        if not isinstance(other, Iset):
            other = Iset(other)

        if self.__len__() == 0:
            return Iset(other)
        elif other.__len__() == 0:
            return Iset(self)
        mode, bound, n = self._get_amalgamated(other)
        res = Iset()
        na = 0
        while na < n:
            res.ins.append(bound[na])
            while mode[na] != 0:
                na += 1
            res.outs.append(bound[na])
            na += 1
        return res

    def __mul__(self, other):
        return self.__and__(other)

    def __imul__(self, other):
        return self.__iand__(other)

    def __iand__(self, other):
        res = self.__and__(other)
        self.ins = res.ins
        self.outs = res.outs
        return self

    def __and__(self, other):
        if isinstance(other, int):
            if self.__contains__(other):
                return Iset(other)
            else:
                return Iset()
        if not isinstance(other, Iset):
            other = Iset(other)
        if len(self.ins) == 0 or len(other.ins) == 0:
            return Iset()
        # print('other is:',other)
        # print('self is:',self)
        mode, bound, n = self._get_amalgamated(other)
        res = Iset()
        na = 0
        while na < n:
            if mode[na] == 3:
                res.ins.append(bound[na])
                na += 1
                res.outs.append(bound[na])
            na += 1
        return res

    def __sub__(self, other):
        if not isinstance(other, Iset):
            other = Iset(other)
        if len(self.ins) == 0 or len(other.ins) == 0:
            return Iset(self)
        mode, bound, n = self._get_amalgamated(other)
        res = Iset()
        na = 0
        while na < n:
            if mode[na] == 1:
                res.ins.append(bound[na])
                na += 1
                res.outs.append(bound[na])
            na += 1
        return res

    def __isub__(self, other):
        res = self.__sub__(other)
        self.ins = res.ins
        self.outs = res.outs
        return self

    def __contains__(self, n):
        if isinstance(n, int):
            if len(self.ins) == 0:
                return False
            mini = 0
            maxi = len(self.ins) - 1
            while maxi > mini:
                i = (mini + maxi) // 2
                if n < self.ins[i]:
                    maxi = i
                elif n >= self.outs[i]:
                    mini = i + 1
                else:
                    return True
            return n >= self.ins[mini] and n < self.outs[mini]
        if not isinstance(n, Iset):
            try:
                n = Iset(n)
            except Exception:
                return False
        return self.__or__(n) == self

    def __index__(self, n):
        try:
            n = int(n)
        except Exception:
            raise TypeError(f'Iset index must be an integer: {n}')
        if len(self.ins) == 0:
            raise IndexError('Iset is empty')
        res = 0
        for i, o in zip(self.ins, self.outs):
            if n < i:
                raise IndexError(f'Iset index {n} out of range')
            if n < o:
                return res + n - i
            res += o - i
        raise IndexError(f'{n} not an element of Iset')

    def __int__(self):
        if self.__len__() == 1:
            return self.ins[0]
        raise TypeError('Only an Iset with a single element can cast to an int')

    def __repr__(self):
        # return "["+repr(self.ins)+','+repr(self.outs)+"]"
        return "{" + ",".join(
            [str(a) if a + 1 == b else str(a) + '..' + str(b - 1) for a, b in
             zip(self.ins, self.outs)]) + "}"


    def pop(self,index=-1):
        result=self[index]
        self-=result
        return result


def main():
    s = Iset(2)
    s.add_element(4)

    a = Iset(2,3,4,5,6,7)
    b = Iset((1, 8))
    print(a)
    print(b)
    c = a & b
    print(c)

    print(Iset((23, 24)))
    print(Iset(23))
    print(Iset())
    print(Iset(4, 5, 6, 23))
    s = Iset(range(2,6))|range(15,12)|range(-1,11)
    print(s)
    print(s[5])
    print(s << -6)
    # print(Iset(2) >> s)
    # print(Iset(range(11)) >> s)
    print(Iset(range(2, 6)))
    print(Iset(2))
    print(Iset('{2,4..6}') - Iset(5))
    print(Iset('{2,4..6}') - 6)
    print(Iset((2, 3, 4, 5, 6, 7, 8)) - Iset((4, 5, 6)))

    print(Iset(range(1, 10)) | Iset(3))

    r = Iset(range(1, 10))
    r -= 5
    r |= 32
    print(r)
    r = Iset((5, 11))
    print(r)
    r |= 11
    print(r)
    print(r[1])

    print(1 not in Iset(range(4)))


if __name__ == '__main__':
    main()