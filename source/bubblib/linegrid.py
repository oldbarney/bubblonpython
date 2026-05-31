"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
#from PySide6.QtCore import QPointF

N=0
NE=1
E=2
SE=3
S=4
SW=5
W=6
NW=7

fwdx=[0,1,1,1,0,-1,-1,-1]
fwdy=[-1,-1,0,1,1,1,0,-1]

xymap=((0,-1),(),(1,0),(),(0,1),(),(-1,0),())

def arrow_coords(x, y, dirn, gridsize):
    dx,dy=xymap[dirn]
    return [x,y,x+dx*gridsize//2,y+dy*gridsize//2]

def touching_arrow_coords(x,y,dirn,gridsize):
    dx,dy=xymap[dirn]
    gby4=gridsize//4
    dx*=gby4
    dy*=gby4

    return [x-dx,y-dy,x+dx,y+dy]


diagtestorder=[(0,1,7,2,6,3,5,4),
           (1,2,0,3,7,4,6,5),
           (2,3,1,4,0,5,7,6),
           (3,4,2,5,1,6,0,7),
           (4,5,3,6,2,7,1,0),
           (5,6,4,7,3,0,2,1),
           (6,7,5,0,4,1,3,2),
           (7,0,6,1,5,2,4,3)
           ]
testorder={ 0:(0,2,6,4),
            2:(2,0,4,6),
            4:(4,6,2,0),
            6:(6,0,4,2)
          }

class Pos:
    def __init__(self,*args):
        if len(args)==0:
            self.x=0
            self.y=0
        elif len(args)==1:
            arg=args[0]
            if isinstance(arg,list):
                self.x=arg[0]
                self.y=arg[1]
            elif isinstance(arg,Pos):
                self.x=arg.x
                self.y=arg.y
        else:
            self.x=round(args[0])
            self.y=round(args[1])

    def __hash__(self):
        return (self.x<<16)|(self.y&65535)
    def __eq__(self,other):
        return isinstance(other,Pos) and self.__hash__()==other.__hash__()
    def __str__(self):
        return f"({self.x},{self.y})"
    def __repr__(self):
        return f"({self.x},{self.y})"
    def __add__(self, other):
        try:
            return Pos(self.x+other.x,self.y+other.y)
        except:
            try:
                return self.__add__(Pos(other))
            except:
                try:
                    return  Pos(self.x+round(other[0]),self.y+round(other[1]))
                except:
                    print(f'unable to add {other} to pos')
                    return self

    def __sub__(self, other):
        try:
            return Pos(self.x-other.x,self.y-other.y)
        except:
            try:
                return self.__sub__(Pos(other))
            except:
                try:
                    return  Pos(self.x-round(other[0]),self.y-round(other[1]))
                except:
                    print(f'unable to subtract {other} from pos')
                    return self

    def __bool__(self):
        return self.x!=0 or self.y!=0

    def adjacent(self,direction):
        return Pos(self.x+fwdx[direction],self.y+fwdy[direction])

    def diagdirection(self,pos):
        dx=pos.x-self.x
        dy=pos.y-self.y
        if dx>0:
            if dy>0:  #E,SE,S
                if dx>dy:  #E,SE
                    if dx>=2*dy:
                        return 2
                    else:
                        return 3
                else: #SE,S
                    if dy>=2*dx:
                        return 4
                    else:
                        return 3
            else: #N,NE,E
                if dx>-dy: #E,NE
                    if dx>=-2*dy:
                        return 2
                    else:
                        return 1
                else:  #N,NE
                    if -dy>=2*dx:
                        return 0
                    else:
                        return 1
        else:
            if dy>0:  #W,SW,S
                if -dx>dy:#W SW
                    if -dx>=2*dy: #W,SW
                        return 6
                    else:
                        return 5
                else: #S,SW
                    if dy>=-2*dx:
                        return 4
                    else:
                        return 5
            else: #W,NW,N
                if -dx>-dy: #W,NW
                    if -dx>=-2*dy:
                        return 6
                    else:
                        return 7
                else:  #N,NW
                    if -dy>=-2*dx:
                        return 0
                    else:
                        return 7
    def direction(self,pos):
        dx=pos.x-self.x
        dy=pos.y-self.y
        if dx>0:
            if dy>0:  #E,SE,S
                if dx>dy:  #E,SE
                    return 2
                else: #SE,S
                    return 4
            else: #N,NE,E
                if dx>-dy: #E,NE
                    return 2
                else:  #N,NE
                    return 0
        else:
            if dy>0:  #W,SW,S
                if -dx>dy:#W SW
                    return 6
                else: #S,SW
                    return 4
            else: #W,NW,N
                if -dx>-dy: #W,NW
                    return 6
                else:  #N,NW
                    return 0

class Grid:
    def __init__(self):
        self.points={}
    def clear(self):
        self.points={}
    def cell(self,pos):
        if pos in self.points:
            return self.points[pos]
        return 0
    def set(self,pos:Pos,node:int):
        if node:
            self.points[pos]=node
        else:
            if pos in self.points:
                del(self.points[pos])
    def blockout(self,centre:Pos,width:int,height:int,node:int):
        #print(f"centre:{centre} wd:{width} he:{height}")
        centre.x=round(centre.x) #for interface block
        centre.y=round(centre.y)
        hw=(width-1)//2
        #print(f"hw:{hw}")
        for x in range(centre.x-hw,centre.x+hw+1):
            self.points[Pos(x,centre.y-1)]=node
            self.points[Pos(x,centre.y+height)]=node
        for y in range(centre.y,centre.y+height):
            for x in range(centre.x-hw-1,centre.x+hw+2):
                self.points[Pos(x,y)]=node

    def __str__(self):
        if not self.points:
            return '-empty'
        left=min(p.x for p in self.points)
        top=min(p.y for p in self.points)
        right=max(p.x for p in self.points)
        bot=max(p.y for p in self.points)
        res=f'({left,top}) to  ({right,bot})'
        for row in range(top,bot+1):
            res=res+'\n'+' '.join(str(self.cell(Pos(x,row))) for x in range(left,right+1))
        return res


class OldGrid:
    def __init__(self,size):
        self.size=size
        self.cols=[]
        j=0
        for i in range(size):
            col=[]
            for k in range(size):
                col.append(0)
                j+=1
            self.cols.append(col)

    def cell(self,pos):
        try:
            return self.cols[pos.x][pos.y]
        except:
            raise Exception(f"Reading cell outside range:{pos}")

    def setxy(self,x:int,y:int,node:int):
        try:
            self.cols[x][y]=node
        except:
            raise Exception(f"Writing cell outside range:({x},{y}")

    def set(self,pos:Pos,node:int):
        self.setxy(pos.x,pos.y,node)

    def blockout(self,centre:Pos,width:int,height:int,node:int):
        #print(f"centre:{centre} wd:{width} he:{height}")
        hw=(width-1)//2
        #print(f"hw:{hw}")
        for x in range(centre.x-hw,centre.x+hw+1):
            self.setxy(x,centre.y,node)
            self.setxy(x,centre.y+height,node)
        for y in range(centre.y,centre.y+height):
            for x in range(centre.x-hw-1,centre.x+hw+2):
                self.setxy(x,y,node)

    def __repr__(self):
        def row(y):
            return " ".join(str(self.cols[i][y]) for i in range(self.size))
        return "\n".join(row(y) for y in  range(self.size))
    def __str__(self):
        return self.__repr__()

def findpath(grid:Grid,startpos:Pos,targetpos:Pos):  # todo here change strategy - straight lines from each end until can join with 45deg diagonal
    #unless path to self
    #print(grid)
    print(f'type of targetpos={type(targetpos)}')
    targetnode=grid.cell(targetpos)
    targetdir=startpos.direction(targetpos)
    path=[]                               #      Stores pos, directons to try in order,  previous contents

    testlist=list(testorder[targetdir])
    lastpos=startpos
    while True:  #Here we have a last position, and a list of directions to try
        print(f"from {lastpos} to {targetpos} is {targetdir}")

        if not testlist:
            print('testlist empty')
            if not path:
                print('path empty')
                return [startpos,targetpos] #no path found -draw a straight line
            (lastpos,testlist)=path.pop()
            grid.set(lastpos,0)
            continue
        print(f"lastpos={lastpos} testlist={testlist}")

        nextpos=lastpos.adjacent(testlist[0])

        testlist=testlist[1:]
        print(f"nextpos={nextpos} testlist={testlist}")

        #print(f"nextpos={nextpos} testlist={testlist}")
        #print(f"from:{lastpos} to {nextpos} with {grid.cell(nextpos)}")
        nextcell=grid.cell(nextpos)

        print(f"nextcell={nextcell} targetnode={targetnode}")
        #print(f'grid={grid}')

        if nextcell==targetnode: #yippee
            result=[startpos]
            for (p,_) in path:
                grid.set(p,targetnode)
                result.append(p)
            result.append(targetpos)
            return result
        elif nextcell:
            continue
        print(f"marking:{nextpos} testlist={testlist}")

        grid.set(nextpos,-1)  #mark where we have been
        path.append((nextpos,testlist))
        lastpos=nextpos
        targetdir=nextpos.direction(targetpos)
        testlist=list(testorder[targetdir])
#for i in range(8):
#    print(Pos(0,0).adjacent(i))