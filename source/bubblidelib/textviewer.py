"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import tkinter as tk

class AutoScrollbar(tk.Scrollbar):

    # Defining set method with all
    # its parameter
    def set(self, low, high):
        if float(low) <= 0.0 and float(high) >= 1.0:
           # Using grid_remove
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        tk.Scrollbar.set(self, low, high)


class TextViewer:
    def __init__(self,data,title='Logs',x=200,y=200,width=640,height=480,closer=None):
        self.data=data

        self.window=tk.Toplevel()
        self.window.title(title)
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        self.closer=closer

        self.window.geometry(f'{width}x{height}+{x}+{y}')
        self.window.grid_columnconfigure(0,weight=1)
        self.window.grid_columnconfigure(1,weight=0)
        self.window.grid_rowconfigure(0,weight=1)
        self.window.grid_rowconfigure(1,weight=0)

        self.vsb = AutoScrollbar(self.window, orient=tk.VERTICAL)
        self.vsb.grid(row=0, column=1, sticky='ns')

        self.text = tk.Text(self.window,background='#FFF',wrap='none',yscrollcommand=self.vsb.set)
        self.vsb.config(command=self.text.yview)

        self.text.insert('1.0',''.join(f'{el}\n' for el in data))
        self.text.edit_reset()
        self.text.mark_set("insert", f'{len(data)}.0')

        self.text.grid(row=0,column=0,sticky='nsew')
        button_frame=tk.Frame(self.window)
        button_frame.grid(row=1,column=0,sticky='esw')
        for c in range(2):
            button_frame.columnconfigure(c,weight=0)
        button_frame.rowconfigure(0,weight=0)
        tk.Button(button_frame,text='Close',
                  command=self.close_window
                 ).grid(row=0,column=0,sticky='w')
        tk.Button(button_frame,text='Clear',
                  command=lambda:self.clear_data()
                 ).grid(row=0,column=1,sticky='w')

    def refresh_contents(self,data):
        self.text.delete('1.0', 'end')
        self.text.insert('1.0',''.join(f'{el}\n' for el in data))
        self.text.edit_reset()
        self.text.mark_set("insert", f'{len(data)}.0')

    def clear_data(self):
        self.data.clear()
        self.text.delete('1.0','end')

    def append(self,value):
        self.text.insert('end -1 chars',value)
        self.text.mark_set("insert", 'end -1 chars')

    def contents(self):
        return self.text.get('1.0','end')

    def close_window(self):
        self.data.clear()
        for el in self.contents().split('\n'):
            self.data.append(el)
        self.window.destroy()
        if self.closer is not None:
            self.closer()

class PythonExceptionViewer:
    def __init__(self,url_callback,title='Python Exception (most recent exception last)',
                 x=200,y=200,width=640,height=480,closer=None):
        self.url_callback=url_callback
        self.window=tk.Toplevel()
        self.window.title(title)
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        self.closer=closer

        self.window.geometry(f'{width}x{height}+{x}+{y}')
        self.window.grid_columnconfigure(0,weight=1)
        self.window.grid_columnconfigure(1,weight=0)
        self.window.grid_rowconfigure(0,weight=1)
        self.window.grid_rowconfigure(1,weight=0)

        self.vsb = AutoScrollbar(self.window, orient=tk.VERTICAL)
        self.vsb.grid(row=0, column=1, sticky='ns')

        self.text = tk.Text(self.window,background='#FFF',wrap='none',yscrollcommand=self.vsb.set)
        self.vsb.config(command=self.text.yview)
        self.text.edit_reset()
        self.text.mark_set("insert", f'end-1c')

        self.text.grid(row=0,column=0,sticky='nsew')
        self.frame_index=0
        self.nlines=0
        button_frame=tk.Frame(self.window)
        button_frame.grid(row=1,column=0,sticky='esw')
        for c in range(2):
            button_frame.columnconfigure(c,weight=0)
        button_frame.rowconfigure(0,weight=0)
        tk.Button(button_frame,text='Close',
                  command=lambda:self.window.destroy()
                 ).grid(row=0,column=0,sticky='w')

    def nlines(self):
        res=self.text.index('end')
        return int(res.split('.')[0])

    def add_line(self,text,url_start=None,url_length=0):
        self.nlines+=1
        if url_start is not None:
            tag_id=f'url_tag{self.frame_index}'
            self.text.insert('end', f'{text}\n',)
            self.text.tag_add(tag_id,f'{self.nlines}.{url_start}',
                                      f'{self.nlines}.{url_start+url_length}')
            #                  f'end -1 lines +{url_start}c',
            #                  f'end -1 lines +{url_start+url_length}c')
            #self.text.tag_add(tag_id,'1.0','5.end')
            self.text.tag_configure(tag_id,foreground='#A0A')
            self.text.tag_bind(tag_id,'<B1-ButtonRelease>',
                               (lambda _event,ind=self.frame_index:
                                    self.url_callback(ind)))
            self.text.tag_bind(tag_id, '<Enter>',
                               lambda _event:self.text.config(cursor='hand1')
                              )
            self.text.tag_bind(tag_id, '<Leave>',
                               lambda _event: self.text.config(cursor='arrow')
                               )
            self.text.tag_bind(tag_id, '<Enter>',
                               lambda _event:
                                    self.text.tag_configure(
                                        tag_id,
                                        foreground='#F0F'),
                               add=True
                               )
            self.text.tag_bind(tag_id, '<Leave>',
                               lambda _event:
                                    self.text.tag_configure(
                                        tag_id,
                                        foreground='#A0A'),
                               add=True
                               )

            self.frame_index += 1
        else:
            self.text.insert('end', f'{text}\n')

        self.text.mark_set("insert", 'end')

    def refresh_contents(self,data):
        self.text.delete('1.0', 'end')
        self.text.insert('1.0','\n'.join(data))
        self.text.edit_reset()
        self.text.mark_set("insert", f'{len(data)}.0')

    def clear_data(self):
        self.data.clear()
        self.text.delete('1.0','end')

    def close_window(self):
        self.window.destroy()
        if self.closer is not None:
            self.closer()
