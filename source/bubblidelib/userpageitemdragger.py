"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
class UserPageItemDragger:
    """Allows user to modify a display output block's position
parameters by dragging the item drawn by the block on a page.
"""
    def __init__(self,item,node,x,y):
        self.item=item
        self.node=node
        self.params=node.params
        self.xorg=x
        self.yorg=y
        self.item_xorg=item.x
        self.item_yorg=item.y
        self.xoff=x-item.x
        self.yoff=y-item.y
        self.previous_xoffset=0
        self.previous_yoffset=0
        px=self.params[self.xi()][1]
        if isinstance(px,int):
            px=f'{px}'

        if px.endswith('#offset'):
            self.xsuffix='#offset'
            px=px[:-7]
            xi=len(px)
            while xi>1 and px[xi-1]!='+':
                xi-=1
            try:
                self.previous_xoffset=int(px[xi:])
            except ValueError:
                self.previous_xoffset=0
            px=px[:xi]
            if px=='':
                px='0'
            self.xprefix=px
        else:
            i=px.find('#')
            if i>-1:
                px=px[:i]
            try:
                int(px)
                self.xprefix=''
                self.xsuffix=''
            except ValueError:
                self.xprefix=f'({px})+'
                self.xsuffix='#offset'
        py=self.params[self.yi()][1]
        if isinstance(py,int):
            py=f'{py}'
        if py.endswith('#offset'):
            self.ysuffix='#offset'
            py=py[:-7]
            yi=len(py)
            while yi>1 and py[yi-1]!='+':
                yi-=1
            try:
                self.previous_yoffset=int(py[yi:])
            except ValueError:
                self.previous_yoffset=0
            py=py[:yi]
            if py=='':
                py='0'
            self.yprefix=py
        else:
            i=py.find('#')
            if i>-1:
                py=py[:i]
            try:
                int(py)
                self.yprefix=''
                self.ysuffix=''
            except ValueError:
                self.yprefix=f'({py})+'
                self.ysuffix='#offset'

    def xi(self):
        for i,p in enumerate(self.params):
            if isinstance(p,list):
                if p[0]=='x':
                    return i
        else:
            self.params.append(['x',self.item_xorg])
            return len(self.params)-1

    def yi(self):
        for i,p in enumerate(self.params):
            if isinstance(p,list):
                if p[0]=='y':
                    return i
        else:
            self.params.append(['y',self.item_xorg])
            return len(self.params)-1

    def mouse_move(self,x,y):
        dx=x-self.xorg
        self.item.x=x-self.xoff
        dy=y-self.yorg
        self.item.y=y-self.yoff
        if self.xsuffix:
            dx+=self.previous_xoffset
            self.params[self.xi()][1]=self.xprefix+f'{dx}'+self.xsuffix
        else:
            self.params[self.xi()][1]=f'{dx+self.item_xorg}'
        if self.ysuffix:
            dy+=self.previous_yoffset
            self.params[self.yi()][1]=self.yprefix+f'{dy}'+self.ysuffix
        else:
            self.params[self.yi()][1]=f'{dy+self.item_yorg}'

class Handle:
    def __init__(self,canvas,x,y,write_func,tags,radius=4,outline='#F00'):
        self.canvas=canvas
        self.xo=x
        self.yo=y
        self.xoff=0
        self.yoff=0
        self.write_func=write_func
        self.uid=self.canvas.create_rectangle(x-radius,y-radius,x+radius.y+radius,
                                outline=outline,tags=tags)
    def close(self):
        self.canvas.delete(self.uid)

    def contains(self,x,y):
        c=self.canvas.coords(self.uid)
        return x>=c[0] and x<=c[2] and y>=c[1] and y<=c[3]

    def grab(self,x,y):
        self.xoff=x-self.xo
        self.yoff=y-self.yo

    def move(self,x,y):
        dx=x-self.xo-self.xoff
        dy=y-self.yo-self.yoff
        self.xo+=dx
        self.yo+=dy
        self.write_func(self.xo,self.yo)
        self.canvas.move(self.uid,dx,dy)
