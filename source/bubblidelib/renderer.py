"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from bubblib.globaldefs import render_defaults
from bubblib.gutils import BubblFont
from bubblib.uiserver import ui


def render(canvas, x1, y1, width, height, tags, id_tag, shape, fill, outline, text_lines, font=None, text_colour=None, centre_text=False,grid=None):
    #if id_tag==154:
    #    print(f'RENDERING WITH 154 fill={fill} outline={outline} tags={tags} shape={shape} width={width} height={height} x1:{x1},y1:{y1}')
    #else:
    #    print(f'RENDERING fill={fill} outline={outline} tags={tags} shape={shape} width={width} height={height} x1:{x1},y1:{y1}')
    if grid is None:
        grid=render_defaults.grid
    x2=x1+width
    y2=y1+height
    if font is None:
        font=BubblFont()
    #print('renderfont is',font)

    #print('renderfont size','None' if font is None else font.point_size)
    if shape=='rect':
        canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline,
                                tags=tags + (f'o{id_tag}',), width=1)
        there=canvas.find_withtag(f'o{id_tag}')
        if not there:
            print('RENDER FAILED TO CREATE RECTANGLE')
        #canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline,
        #                        tags=tags + (f'o{id_tag}',), width=1)

        #if id_tag==154:
        #    canvas.create_rectangle(x1-10, y1-10, x2+10, y2+10, fill='#F00', tags=(f'o{id_tag}',),outline=outline,
        #                                 width=1)
        #    print('REALLY CREATED RECTANGLE for 154 with tags:',tags+(f'o{id_tag}',))
    elif shape=='round':
        r=render_defaults.gs_by2
        points=[x1,y1+r,x1+r/4,y1+r/2,x1+r/2,y1+r/4,x1+r,y1,
                x2-r,y1,x2-r/2,y1+r/4,x2-r/4,y1+r/2,x2,y1+r,
                x2,y2-r,x2-r/4,y2-r/2,x2-r/2,y2-r/4,x2-r,y2,
                x1+r,y2,x1+r/2,y2-r/4,x1+r/4,y2-r/2,x1,y2-r]
        canvas.create_polygon(points, fill=fill, outline='#000', tags=tags+(f'o{id_tag}',), width=1) #,activefill=self.highlight_fill)
    elif shape=='rhombus':
        g2=render_defaults.gs_div2
        points=[x1,y1+g2,x1+g2,y1+g2+g2,x1+g2+g2,y1+g2,x1+g2,y1]
        canvas.create_polygon(points, fill=fill, outline='#000', tags=tags+(f'o{id_tag}',))#,activefill=self.highlight_fill)
    if text_colour is not None:
        outline=text_colour
    if centre_text:
        #print('CENTRETEXT')
        for i,line in enumerate(text_lines):
            canvas.create_text(x1 + width // 2, y1 + render_defaults.gs_div2 + i * render_defaults.grid, text=line, fill=outline, anchor='center', tags=tags+(f't{id_tag}#{i}',), font=font.font)
    else:
        for i,line in enumerate(text_lines):
            canvas.create_text(x1 + 2, y1 + i * grid, text=line, fill=outline, anchor='nw', tags=tags+(f't{id_tag}#{i}',), font=font.font)

''' points = [x1+radius, y1,
          x1+radius, y1,
          x2-radius, y1,
          x2-radius, y1,
          x2, y1,
          x2, y1+radius,
          x2, y1+radius,
          x2, y2-radius,
          x2, y2-radius,
          x2, y2,
          x2-radius, y2,
          x2-radius, y2,
          x1+radius, y2,
          x1+radius, y2,
          x1, y2,
          x1, y2-radius,
          x1, y2-radius,
          x1, y1+radius,
          x1, y1+radius,
          x1, y1]
        points=[x+r,y, x+r,y, x2-r,y, x2-r,y, x2,y, x2,r+y, x2,r+y, x2,y2-r, x2,y2-r, x2,y2,
                x2-r,y2, x2-r,y2, x+r,y2, x+r,y2, x,y2, x,y2-r, x,y2-r, x,y+r, x,y+r, x,y]
        self.id_no=self.canvas.create_polygon(points,fill=self.fill_colour, outline='#000',tag=f'{self.nodeNo}',smooth=True)
'''