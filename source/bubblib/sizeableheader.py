"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import tkinter as tk

from bubblib.utils import log

if __name__=='__main__':
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .gutils import BubblFont

class ColumnSpec:
    def __init__(self,header,column_index,
                 width,
                 display_func=None,
                 sort_key_func=None,
                 range_right=False,
                 icon_func=None):
        self.width=width
        self.header=header
        self.column_index=column_index
        if display_func is None:
            display_func = lambda x:f'{x}'
        self.display_func=display_func
        if sort_key_func is None:
            sort_key_func=lambda x:x[column_index]
        self.sort_key_func=sort_key_func
        self.range_right=range_right
        self.icon_func=icon_func

    @staticmethod
    def get_header(index, heading, column_type, column_width):
        range_right= column_type in ('int', 'num', 'float')
        if range_right:

            if column_type== 'float':
                display_func=lambda x:f'{x:.3f}'
            else:
                display_func=lambda x:f'{x}'
            sort_func=lambda x:float(x)
        else:
            if column_type=='iset':
                display_func=lambda x:f'{x}'
                sort_func=lambda x:len(x)
            else:
                #print('COLUMNDISPLAYFU')
                display_func=lambda x:f'{x}'
                sort_func=lambda x:x[:1]+x.lower()
        return ColumnSpec(
            heading,
            column_index=index,
            width=column_width,
            range_right=range_right,
            display_func=display_func,
            sort_key_func=sort_func
        )


class SizeableHeader(tk.Frame):
    def __init__(self,parent,callback,column_specs,font=None):
        self.parent=parent
        self.callback=callback
        self.column_specs=column_specs
        tk.Frame.__init__(self,parent)
        if font is None:
            font=BubblFont(font)
        self.font=font
        self.mouse_state=('up',0)   #('onheader',i), ('onjoin',i)
        self.grid(row=0,column=0,sticky='nw')
        self.draw()
        #print('Sizeable Header has drawn')
        self.dragging=False
        self.mouse_over=None
        self.mouse_on=None
        for i in range(len(column_specs)):
            self.columnconfigure(i,weight=0)

    def clear(self):
        for child in self.winfo_children():
            child.destroy()

    def draw(self):
        self.clear()
        for i,column in enumerate(self.column_specs):
            canvas=tk.Canvas(self,width=column.width,height=self.font.line_space,
                             borderwidth=1,relief='solid')
            text=self.font.cropped(column.header,column.width)
            canvas.create_text(3,0,text=text,anchor='nw')
            canvas.grid(column=i,row=0,sticky='w')
            canvas.bind('<Motion>',lambda event,i=i:self.mouse_move(event,i))
            canvas.bind('<1>', lambda event,i=i:self.mouse_down(event,i))
            canvas.bind('<B1-ButtonRelease>', lambda event,i=i:self.mouse_up(event,i))
            canvas.bind('<Leave>', self.mouse_leave)
        #self.update_idletasks()


    @property
    def width(self):
        return int(self.winfo_children()[-1]['width'])+4 #really width of last child?

    @property
    def x_coords(self):
        return [child.winfo_x() for child in self.winfo_children()]
    @property
    def right_x_coords(self):
        rh=self.winfo_children()[-1]
        rrx=rh.winfo_x()+rh.winfo_width()
        return [child.winfo_x() for
                child in self.winfo_children()[1:]]+[rrx]


    @property
    def widths(self):
        return [spec.width for spec in self.column_specs] #child.winfo_width() for child in self.winfo_children()]

    def mouse_down(self,event,i):
        log('FileDialog mouse down',event.x,i)
        if self.mouse_over is not None:
            self.width0=self.column_specs[i].width #event.widget.winfo_width()
            self.x0=event.x
            self.dragging=True
        else:
            self.mouse_on=i

    def mouse_up(self,event,i):
        #log('mouse up',event.x,i)
        if self.dragging:
            self.dragging=False
            self.callback('resized',self.x_coords,self.widths)
        elif self.mouse_on is not None:
            log('FileDialog clicked')
            self.callback('clicked',self.mouse_on)

        #xs=self.x_coords()
        #for i in range(len(self.winfo_children())):
        #    children=[child for child in self.winfo_children()[:i+1]]
        #    print(xs[i],sum([int(child['width'])+4 for child in children]))

    def mouse_move(self,event,i):
        if self.dragging:
            neww=self.width0+event.x-self.x0
            if neww<10:
                neww=10
            self.winfo_children()[self.mouse_over].config(width=neww)
            self.column_specs[i].width=neww
            self.winfo_children()[self.mouse_over].delete('all')
            self.winfo_children()[self.mouse_over].create_text(3,0,
                text=self.font.cropped(self.column_specs[i].header,self.column_specs[i].width),anchor='nw')
            self.callback('resizing',self.x_coords,self.widths)
            return

        #print('mouse_move',event.x,i)
        #print('ww=',event.widget.winfo_width())
        if event.x>event.widget.winfo_width()-8:
            self.mouse_over=i
            event.widget.config(cursor='sb_h_double_arrow')
        else:
            self.mouse_over=None
            event.widget.config(cursor='arrow')

        #self.parent.update_idletasks()
        for x,w,column in zip(self.x_coords,self.widths,self.column_specs):
            column.width=w
            column.x=x

    def mouse_leave(self,event):
        #print('mouse_leave',event)
        self.mouse_on=None
        event.widget.config(cursor='arrow')

def main():
    root=tk.Tk()
    win=tk.Toplevel()
    def action(desc,index):
        print(desc,index)
    h=SizeableHeader(win,action,['A long header','Head 2','Hedder 3','a much much mcuh longer 4'])
    root.mainloop()
if __name__=='__main__':
    main()
