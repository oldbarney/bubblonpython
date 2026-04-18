"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import os
from collections import deque
from datetime import datetime
from io import StringIO

log_level_map={1:'Debug',
               2:'Info',
               3:'Warning',
               4:'Error',
               5:'Runtime Error',
               6:'Fatal'}

def get_log_level(level_str):
    try:
        return ['Debug','Info','Warning',
                'Error','Runtime error','Fatal'].index(level_str)+1
    except:
        return 1


class MyStringIO(StringIO):
    def __init__(self,changed_func=None):
        StringIO.__init__(self)
        self.changed_func=changed_func

    def write(self,s,/):
        result = super().write(s)
        if self.changed_func is not None:
            self.changed_func(s)
        return result

    def refresh(self,value):
        self.truncate(0)
        self.seek(0)
        cfsave=self.changed_func
        self.changed_func=None
        self.write(value)
        self.changed_func=cfsave


class StringLogger(MyStringIO):
    def __init__(self,changed_func=None,level=1):
        MyStringIO.__init__(self,changed_func=changed_func)
        self.level=level

    def log(self,*args,level=1,**kwargs):
        if level>=self.level:
            line=f'{log_level_map[level]}:'
            line+=f'{datetime.now().strftime("%Y %b %d %H:%S.%f")[:-3]} '
            line+=f'{" ".join(str(arg) for arg in args)}'
            self.write(line)
            self.write('\n')


class PrintLogger:
    def __init__(self,level=1):
        self.level=level
    def log(self,*args,level=1,**kwargs):
        if level>=self.level:
            line=f'{log_level_map[level]}:'
            line+=f'{datetime.now().strftime("%Y %b %d %H:%S.%f")[:-3]} '
            line+=f'{" ".join(str(arg) for arg in args)}'
            print(line)

class Logger:
    DEBUG=1
    INFO=2
    WARNING=3
    ERROR=4
    RUNTIME_ERROR=5
    FATAL=6

    def __init__(self,
                 log_folder=None,
                 nlogs=5,
                 level=5,
                 max_file_size_kb=100):
        self.nlogs=nlogs
        self.max_file_size_kb=max_file_size_kb
        if log_folder is None:
            log_folder=os.getcwd() + os.sep+'logs'+os.sep
        self.log_folder=log_folder
        self.file=f'{self.log_folder}log.txt'
        self.level=level
        if not os.path.isdir(log_folder):
            os.makedirs(log_folder)
        if not os.path.isfile(self.file):
            self.bump_log_file()


    def log(self,*args,level=DEBUG,**kwargs):
        if level>=self.level:
            line=f'{log_level_map[level]}:'
            line+=f'{datetime.now().strftime("%Y %b %d %H:%S.%f")[:-3]} '
            line+=f'{" ".join(str(arg) for arg in args)}\n'
            with open(self.file,'a') as f:
                f.write(line)
            if os.stat(self.file).st_size>=self.max_file_size_kb*1024:
                self.bump_log_file()

    def bump_log_file(self):
        if os.path.isfile(self.log_folder+f'log{self.nlogs}.txt'):
            os.remove(self.log_folder+f'log{self.nlogs}.txt')
        for n in range(self.nlogs-1,0,-1):
            if os.path.isfile(f'{self.log_folder}log{n}.txt'):
                os.rename(f'{self.log_folder}log{n}.txt',
                          f'{self.log_folder}log{n+1}.txt')
        if os.path.isfile(f'{self.log_folder}log.txt'):
            os.rename(f'{self.log_folder}log.txt',
                          f'{self.log_folder}log{n+1}.txt')

        with open(self.file,"w") as f:
            f.write('--- Log file started '+
                    datetime.now().strftime("%Y_%m_%d_%H_%M_%S")+
                    ' ---\n')

class QueueLogger:
    def __init__(self,level=1,max_len=10000):
        self.queue=deque(maxlen=max_len)
        self.level=level

    def log(self,*args,level=1,**kwargs):
        try:
            if level>=self.level:
                line=f'{log_level_map[level]}:'
                line+=f'{datetime.now().strftime("%Y %b %d %H:%S.%f")[:-3]} '
                line+=f'{" ".join(str(arg) for arg in args)}'
                self.queue.append(line)
        except Exception as e:
            print('QUEUELOGGER EXCEPTION',e)

class RuntimeException:
    def __init__(self,mach,mess,line_no=None,code_text=None):
        self.error_message=mess
        self.line_no=line_no
        self.diag=mach.diag.name
        self.node=mach.node
        print('RUNTIME EXCEPTION',self.diag,list(mach.diags[self.diag].nodes),self.node)
        block=mach.diags[self.diag].nodes[self.node]
        self.type_name=block.type_name
        self.params='\n'.join(str(param) for param in block.params)
        self.links=block.links
        self.code=code_text

    def __str__(self):
        result=f"""RuntimeException: {self.error_message} in {self.diag} node:{self.node} type:{self.type_name}
params:[{self.params}
]
"""
        if self.line_no is not None and self.code is not None:
            code=self.code.split('\n')
            before='\n'.join(code[:self.line_no-1])
            during='\n'.join(code[self.line_no-1:self.line_no])
            after='\n'.join(code[self.line_no:])
            result+=f"""
================= Code =================
{before}
---------------error-line---------------------
{during}
---------------error-line-end-----------------
{after}
================End of Code============="""
        return result
