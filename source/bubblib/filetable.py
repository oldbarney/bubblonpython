"""Defines FileTable class
FileTable allows access to the details of the contents
of a folder as a table where each row (record) in the
table contains information about a file or sub-folder.
Used by the system variables _fs.files and _fs.folder
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import os
import zipfile
from datetime import datetime
from .table import  RawTable


class FileTable(RawTable):
    def __init__(self):
        super().__init__('Folder',["Name:str","Ext:str","Dir:int","Size:int","Time:float"])
        self.path=os.getcwd()+os.sep
        self.path_in_zip=None
        self._data=[]
        self.update(self.path)

    def update(self,path):
        #print('FILETABLE UPDATING',path)
        self.path=path
        split_path = (path[:-1]+'/').split(',')
        if len(split_path) == 1:
            self._data=[item for item in os.scandir(path)]
            self.path_in_zip=None
        else:
            zfn,self.path_in_zip=split_path
            if not zipfile.is_zipfile(zfn):
                self._data=[]
                return
            #print('FILE',zfn,'exists',os.path.isfile(zfn))
            with zipfile.ZipFile(zfn, 'r') as f:
                #print('fn',fn)
                #print([entry.filename for entry in f.infolist()])
                self._data=[entry for entry in f.infolist()
                           if entry.filename.startswith(self.path_in_zip)
                              and entry.filename!=self.path_in_zip]

    def get_row(self,index):
        #return self.data[index-1]
        entry = self._data[index]
        if self.path_in_zip is None:
            stat=entry.stat()
            name=entry.name
            try:
                time = stat.st_birthtime  # windows only
            except AttributeError:
                time = stat.st_ctime
            is_dir=int(entry.is_dir())
            size=stat.st_size
        else:
            name = entry.filename[len(self.path_in_zip):]
            is_dir = 1 if entry.is_dir else 0
            size = entry.file_size
            y, m, d, h, min, sec = entry.date_time
            time = datetime(y, m, d, h, min, sec, 0).timestamp()
        ext = name.split('.')
        if len(ext) == 1:
            ext = ''
        else:
            ext = '.' + ext[-1]
        return self.Row([name,ext,is_dir,size,time])

    def insert_row(self,index,row):
        pass
    def replace_row(self,index,row):
        pass
    def remove_row(self,index,_undoable=False):
        pass
    def __len__(self):
        return len(self._data)