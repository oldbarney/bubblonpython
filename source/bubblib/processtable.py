"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import subprocess
from .table import RawTable
from .utils import runtime_log



class ProcessTableRow:  #controller
    def __init__(self,process_manager):
        self._field_names=["Command","Id","Ended","Exitcode","Out","Err","In"]
        self._pm=process_manager
        #print('finished creating processtablerow')

    def __getitem__(self,item):
        #print(f'getting item:{item}')
        try:
            return getattr(self,item)
        except:
            try:
                return getattr(self,self._field_names[item-1])
            except:
                return None
    @property
    def Command(self):
        return self._pm.command
    @property
    def Id(self):
        return self._pm.process.id_no
    @property
    def Ended(self):
        return 0 if self._pm.process.running else 1
    @property
    def Exitcode(self):
        return self._pm.exit_code

    @property
    def Out(self):
        if self._pm.stdout_spec!=subprocess.PIPE:
            return self._pm.process.stdout_spec
        else:
            return 'PIPE'
    @property
    def Err(self):
        if self._pm.stderr_spec!=subprocess.PIPE:
            return self._pm.process.stderr_spec
        else:
            return 'PIPE'
    @property
    def In(self):
        if self._pm.stdin_spec!=subprocess.PIPE:
            return self._pm.stdinfile
        return None
    @In.setter
    def In(self,message:str):
        self._pm.stdin_message.emit(message)

    def __str__(self):
        try:
            return ','.join([self.Command,str(self.Id),str(self.Ended),str(self.Exitcode),'','',''])
        except Exception as e:
            self._pm.log('ProcessTable rowstring error',e,level=2)
            return self.Command


class ProcessTable(RawTable):
    def __init__(self):
        RawTable.__init__(self,'Process',["Command:str","Id:int","Ended:int","Exitcode:int","Out","Err","In"])
        self._data=[]

    def add_process(self,process):
        self._data.append(ProcessTableRow(process))

    def get_row(self,index):
        #return self.data[index-1]
        try:
            entry=self._data[index]
            return entry
        except:
            return None

    def remove_process_by_id(self,process_id):
        for i,row in enumerate(self._data):
            if row.Id==process_id:
                self._data.pop(i)
                break
        else:
            print('Somehow media play process is missing')


    def insert_row(self,index,row):
        pass
    def replace_row(self,index,row):
        pass
    def remove_row(self,index,_undoable=False):
        try:
            self._data.pop(index)._pm.process.kill()
        except Exception as e:
            runtime_log('Failed to kill process No:',index,e,level=2)

    def __len__(self):
        return len(self._data)

    def ok_swap_fields(self,row,values:dict):
        #return a list of previous values for field updates
        #print(f'ok_swap_fields row:{row}, values:{values}')
        row=self.get_row(row)
        if 'In' in values:
            row.In=values['In']
            values['In']=''
        return True