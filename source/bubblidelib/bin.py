"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from bubblib.gutils import full_icon


class Bin:
    empty=full_icon('hole', 150, 80)
    approaching=full_icon('hole2', 150, 80)
    full=full_icon('hole3', 150, 80)

    def __init__(self,x,y,canvas):
        self.canvas=canvas
        self.y=round(y)
        self.x=round(x)
        canvas.create_image(x,y,image=Bin.empty,tags=('bin',),anchor='sw')
        canvas.tag_raise('bin','all')
        self.mode='far'

    def update(self, proximity):
        if proximity == 'over':
            if self.mode=='over':
                return
            self.canvas.itemconfig('bin', image=Bin.full)
            self.canvas.moveto('bin', '', self.y - 80)
            self.mode='over'
        elif proximity== 'far':
            if self.mode=='far':
                return
            self.canvas.itemconfig('bin',image=Bin.empty)
            self.canvas.moveto('bin', '',self.y-80)
            self.mode='far'
        else:
            if self.mode=='near':
                return
            self.canvas.itemconfig('bin', image=Bin.approaching)
            self.canvas.moveto('bin', '',self.y-81)
            self.mode='near'