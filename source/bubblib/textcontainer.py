"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from .gutils import BubblFont
from .utils import split_html, bold_attr, italic_attr, sub_attr, super_attr, log

EMPTY_TEXT_BLOCK_TEXT='-start typing-'

class BlockOfText:
    '''
    Handles the following html tags:
    <b>
    <i>
    <sub>
    <super>
    <br />
    '''

    def __init__(self, text, font="Courier,10", colour='#000', highlight_colour='#F40', fill=None, cache=None):
        # print('Block of Text INITING WITH FONT',font)
        self.fonts = {}
        #print('Font passed to block of text is ',font)
        self._font = BubblFont(font)
        #print('Block of text initialising font from',font)
        #print('blockoftext font=',self.font)
        self.cache = cache
        self._curs = 0
        self._mark = 0
        self.lines = []
        self.attributes = []
        self.marks = []
        self.text_in = text
        self.html = text
        self.colour = colour
        self.highlight_colour = highlight_colour
        self.highlighted=False
        self.marked_colour = '#80C'
        self.active_colour = self.colour
        self.fill = fill
        self.cursor_state = -1  # off -1..1 invisible 2 to 4 visible
        self.editing = False
        self.get_font_and_yoff(0)

    @property
    def font(self):
        #print('returning BLockOfTextBaseClass font')
        return self._font

    @font.setter
    def font(self, name):
        self._font = BubblFont(name)

    @property
    def line_space(self):
        # print(self.fonts[0])
        return self.font.line_space

    def get_chunks(self, line, attribs, mark=None, marklen=0):
        if line == '':
            return []
        attribs = [int(c, 16) for c in attribs]
        if len(line) != len(attribs):
            raise Exception("line not same length as attribes in get_chunks")
        if mark != None and marklen:
            for i in range(mark, mark + marklen):
                attribs[i] |= 16  # indicate highlight
        result = []
        last = 0
        c = attribs[0]
        for ind in range(1, len(line)):
            if attribs[ind] != c:
                # print(f'chunk_boundary ind={ind} text={line[last:ind]}, current_attr={c} chunkAttr={attribs[ind]}')
                result.append((line[last:ind], c))
                last = ind
                c = attribs[ind]
        result.append((line[last:], c))
        return result

    def max_cursor(self):
        return len(self.editable_text[0])

    @property
    def html(self):
        return '<br />'.join([self.line_to_html(line, attribs) for (line, attribs) in zip(self.lines, self.attributes)])

    @html.setter
    def html(self, text):
        self.lines, self.attributes = split_html(text)
        self.check_marked()

    @property
    def plain_text(self):
        return '\n'.join(self.lines)

    @plain_text.setter
    def plain_text(self, text):
        self.lines = text.split('\n')
        self.attributes = ['0' * len(line) for line in self.lines]

    def line_to_html(self, line, attributes):
        chunks = self.get_chunks(line, attributes)
        bold = False
        italic = False
        sup = False
        sub = False
        result = ''
        for (s, at) in chunks:
            nb = bool(at & bold_attr)
            ni = bool(at & italic_attr)
            nsub = bool(at & sub_attr)
            nsup = bool(at & super_attr)
            if nb != bold:
                result += ('<b>' if nb else '</b>')
                bold = nb
            if ni != italic:
                result += ('<i>' if ni else '</i>')
                italic = ni
            if nsub != sub:
                result += ('<sub>' if nsub else '</sub>')
                sub = nsub
            if nsup != sup:
                result += ('<super>' if nsup else '</super>')
                sup = nsup
            result += s
        if sup:
            result += '</super>'
        if sub:
            result += '</sub>'
        if italic:
            result += '</i>'
        if bold:
            result += '</b>'
        return result

    @property
    def editable_text(self):
        return '\r'.join(self.lines), '\r'.join(self.attributes)

    @editable_text.setter
    def editable_text(self, textattr):
        text, attribs = textattr
        if attribs != None:
            self.lines = text.split('\r')
            self.attributes = attribs.split('\r')
        else:
            lines, attributes = split_html(text)
            self.lines = lines
            self.attributes = attributes
        self.check_marked()
        # print(f'editable assigned to {self.lines}, {self.attributes}')

    def replace_ta(self, index, length, text, attributes=None):
        log(f'replace_ta({text},{attributes})')
        s, a = self.editable_text
        if attributes == None:
            if index == 0:
                atb = '0'
            else:
                atb = a[index - 1]
                if atb == '\r':
                    atb = '0'
            attributes = atb * len(text)

        # print('in s='+s.replace("\r","<br />")+', a='+a.replace("\r","<br />")+f' text={text} attr={attributes}')
        rs = s[index:index + length]
        ra = a[index:index + length]
        s = s[:index] + text + s[index + length:]
        a = a[:index] + attributes + a[index + length:]
        # print(f'out s='+s.replace("\r","<br />")+', ='+a.replace("\r","<br />"))
        self.editable_text = (s, a)
        return rs, ra

    def get_font_and_yoff(self, attrib):
        '''
bold_attr=0x01
italic_attr=0x02
sub_attr=0x04
super_attr=0x08
mark_attr=0x10
'''
        #print('font attribs=',attrib)
        try:
            return self.fonts[attrib]
        except:
            pass

        italic = ',i' if attrib & italic_attr else ''
        bold = ',b' if attrib & bold_attr else ''
        yoff = 0
        if attrib & super_attr:
            size = (2*self.font.point_size) // 3
            yoff = 0 #-self.font.point_size // 6
        elif attrib & sub_attr:
            size = (2*self.font.point_size) // 3
            yoff = (3*self.font.point_size)// 4
        else:
            size = self.font.point_size

        nfref = f'{self.font.family},{size}{italic}{bold}'
        #print('nfref is',nfref)
        font = BubblFont(nfref)
        result = font, yoff
        self.fonts[attrib] = result
        return result

    def draw(self, xorg, yorg, canvas, tag):
        # Render to canvas and return canvas cursor coordinates
        # print('BlockOfText drawing starting with ',str(self.font))
        canvas.delete(tag)
        if self.is_empty():
            canvas.create_text(xorg,yorg,text=EMPTY_TEXT_BLOCK_TEXT,fill='#BBB',tag=tag,anchor='nw',font=self.font.font)
            return xorg,yorg,xorg,yorg+self.line_space
        y = yorg
        for line, attrs, mark in zip(self.lines, self.attributes, self.marks):
            # print(f'drawing line:{line}')
            x = xorg
            for (s, at) in self.get_chunks(line, attrs, mark=mark[0], marklen=mark[1]):
                font, yoff = self.get_font_and_yoff(at)
                #print('Some of B lockOfText font',str(font))

                adv = font.font.measure(s)
                # print('yoff',yoff)
                if at & 0x10:
                    colour = self.marked_colour
                else:
                    colour = self.highlight_colour if self.highlighted else self.colour
                # print('c',self.colour,'hc',self.highlight_colour)
                canvas.create_text(x, y + yoff, text=s, tag=tag, font=font.font, fill=colour, anchor='nw',
                                   tags=(tag, 'widget'))
                x += adv
            y += self.line_space

        r, c = self.ind_to_rc(self.curs)
        xo, yo = self.rc_to_xy(r, c)
        return xorg + xo, yorg + yo, xorg + xo, yorg + yo + self.line_space

    def get_max_width(self):
        res = 1
        for line, attrs in zip(self.lines, self.attributes):
            if len(line) != len(attrs):
                raise Exception("len line is not same as len attrs in get_max_width")
            x = 0
            for (s, at) in self.get_chunks(line, attrs):
                font, yoff = self.get_font_and_yoff(at)
                x += font.font.measure(s)
            res = res if res > x else x
        return res

    def rc_to_xy(self, row, col):
        y = row * self.line_space
        chunks = self.get_chunks(self.lines[row], self.attributes[row])
        x = 0
        for (s, at) in chunks:
            font, yoff = self.get_font_and_yoff(at)
            if col > len(s):
                col -= len(s)
                x += font.font.measure(s)
            else:
                x += font.font.measure(s[:col])
                return x, y
        return x, y

    def ind_to_rc(self, ind):
        row = 0
        #print(f'debug: lines={self.lines} ind={ind}')
        #print(f'debug: attrs={self.attributes} ind={ind}')

        while row < len(self.lines) and ind > len(self.lines[row]):
            ind -= len(self.lines[row]) + 1
            row += 1
        return row, ind

    @property
    def curs(self):
        return self._curs

    @curs.setter
    def curs(self, ind):
        # does not allow cursor to be set beyond end of text
        # creates at most one new row
        if isinstance(ind, tuple):  # set cursor and mark
            while self.ind_to_rc(ind[0])[0] > len(self.lines):
                ind[0] -= 1
            while self.ind_to_rc(ind[1])[0] > len(self.lines):
                ind[1] -= 1
            if self._curs != ind[0] or self._mark != ind[1]:
                self._curs = ind[0]
                self._mark = ind[1]
            self.check_marked()

        else:  # set cursor and mark to same value
            while self.ind_to_rc(ind)[0] > len(self.lines):
                ind -= 1
            if self._curs != ind or self._mark != ind:
                self._curs = ind
                self._mark = ind
                # if self.ind_to_rc(ind)[0] == len(self.lines):
                #    self.lines.append('')
                #    self.attributes.append('')
                self.check_marked()

    @property
    def mark(self):
        return self._mark

    @mark.setter
    def mark(self, value):
        if self._mark != value:
            self._mark = value
            self.check_marked()

    def check_marked(self):
        # print(f'curs={self._curs} mark={self._mark}')
        self.marks = [(None, 0)] * len(self.lines)
        if self._mark == self._curs:
            return
        '''
        first,second= ordered(self._mark, self._curs)
        ar, ac = self.ind_to_rc(first)
        br, bc = self.ind_to_rc(second)
        '''
        if self._mark > self._curs:
            ar, ac = self.ind_to_rc(self._curs)
            br, bc = self.ind_to_rc(self._mark)
        else:
            ar, ac = self.ind_to_rc(self._mark)
            br, bc = self.ind_to_rc(self._curs)
        if br >= len(self.lines):
            br = len(self.lines) - 1
            bc = len(self.lines[br])
        if ar == br:
            self.marks[ar] = (ac, bc - ac)
            self.report_chunks()
            return
        self.marks[ar] = (ac, len(self.lines[ar]) - ac)
        for r in range(ar + 1, br):
            self.marks[r] = (0, len(self.lines[r]))
        self.marks[br] = (0, bc)
        self.report_chunks()

    def report_chunks(self):
        all = [self.get_chunks(line, atts, mark=marks[0], marklen=marks[1]) for line, atts, marks in
               zip(self.lines, self.attributes, self.marks)]
        log(f'checkmarked:{all}')

    def rc_to_ind(self, row, col):
        ind = 0
        res = 0
        while ind < row:
            res += len(self.lines[ind]) + 1
            ind += 1
        return res + col

    def xy_to_rc(self, xoff, yoff):
        row = round((yoff - self.line_space / 2) / self.line_space)
        row = row if row >= 0 else 0
        row = row if row < len(self.lines) else len(self.lines) - 1
        log(f'xy_to_rc yoff={yoff} row={row} nlines={len(self.lines)}')
        chunks = self.get_chunks(self.lines[row], self.attributes[row])
        c = 0
        for (s, at) in chunks:
            font, yoff = self.get_font_and_yoff(at)
            adv = font.font.measure(s)
            if adv > xoff + self.line_space / 5:
                for i in range(1, len(s)):
                    if font.font.measure(s[:i]) > xoff + self.line_space / 5:
                        log(f'c={c + i - 1}')
                        return row, c + i - 1
                return row, c + len(s) - 1
            xoff -= adv
            c += len(s)
        log(f'c={c}')
        return row, c

    def is_empty(self):
        return self.editable_text[0] == '' or self.editable_text[0].isspace()