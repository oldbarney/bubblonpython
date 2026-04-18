"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import threading
import subprocess,shlex

from .bubblevent import OutputStreamEvent
from .signals import Signal
from .uiserver import ui


class StreamReader:
    def __init__(self,stream,process_id,mach,event_type):
        self.stream=stream
        self.process_id=process_id
        self.mach=mach
        self.event_type=event_type
        #self.line_ready.connect(listener)
        #print('Created StreamReader')
        self.kill_event=threading.Event()
        self.sr_exited=threading.Event()

    def run(self):
        self.running=True
        while not self.kill_event.is_set():
            try:
                line=self.stream.readline()
                if line!='':
                    self.mach.queue_event(OutputStreamEvent(self.event_type,self.process_id,line))
                    #self.bubbl_event.emit(OutputStreamEvent(self.event_type,self.process_id))
                else:
                    self.mach.log('end of file for stream reader',level=2)#+self.event_type+str(self.process_id))
                    break
            except Exception as e:
                print(f'Stream reader exception {e}')
                break
        self.running=False
        #print('streamreader exiting its thread')
        self.sr_exited.set()
        #QThread.currentThread().exit()

    def kill(self):
        self.kill_event.set()

class ExitMonitor:
    def __init__(self,process):
        #QObject.__init__(self,None)
        #print('Exit monitor __init__ called')
        self.process=process
        self.exited=Signal()

    def run(self):
        #print('Exit monitor running')
        self.process.wait()
        #print('Exit monitor finished waiting')
        self.exited.emit()
        #QThread.currentThread().exit(0)

class Process:  #Controller

    next_id=0


    def __init__(self,command,mach):#stdout_client,stderr_client,stdin_client,monitor):
        #QObject.__init__(self,None)
        #self.exited.connect(client.process_exited)
        #self.stdout_buffer=[]
        #self.stderr_buffer=[]
        self.pr_exited=Signal()
        self.mach=mach
        self.exit_code=-1
        self.running=0
        self.id_no=Process.next_id
        Process.next_id+=1
        #client.stdin_message.connect(self.receive_stdin)

        self.stdout_spec=subprocess.PIPE
        self.stderr_spec=subprocess.PIPE
        self.stdin_spec=subprocess.PIPE

        parts=shlex.split(command)
        #parts[0]=shutil.whic
        try:
            i=parts.index('1>')
            self.stdout_spec=open(parts.pop(i+1),"w")
            parts.pop(i)
        except:
            pass
        try:
            i=parts.index('2>')
            self.stderr_spec=open(parts.pop(i+1),"w")
            parts.pop(i)
        except:
            pass
        try:
            i=parts.index('>')
            self.stdout_spec=open(parts.pop(i+1),"w")
            self.stderr_spec=self.stdout_spec
            parts.pop(i)
        except:
            pass
        try:
            i=parts.index('1>>')
            self.stdout_spec=open(parts.pop(i+1),"a")
            parts.pop(i)
        except:
            pass
        try:
            i=parts.index('2>>')
            self.stderr_spec=open(parts.pop(i+1),"a")
            parts.pop(i)
        except:
            pass
        try:
            i=parts.index('>>')
            self.stdout_spec=open(parts.pop(i+1),"a")
            self.stderr_spec=self.stdout_spec
            parts.pop(i)
        except:
            pass
        try:
            i=parts.index('<')
            self.stdin_spec=parts.pop(i+1)
            parts.pop(i)
        except:
            pass
        try:
            i=parts.index('|')
            self.stdout_sped=parts.pop(i+1)
            parts.pop(i)
            self.stdin_spec=parts.pop(i-1)
        except:
            pass

        self.parts=parts
        self.pout=None
        self.pout_thread=None
        self.perr=None
        self.perr_thread=None

        self.stdout_monitor=None
        self.stderr_monitor=None
        self.process=None

    def run(self):
        #print('about to create subprocess')
        try:
            self.process=subprocess.Popen(self.parts,
                                          text=True,
                                          stdout=self.stdout_spec,
                                          stderr=self.stderr_spec,
                                          stdin=self.stdin_spec)
            self.running=1
        except Exception as e:
            print(f'Failed to run process: {e}')
            self.pr_exited.emit(-1)
            return
        #print('created subprocess')

        if self.stdout_spec==subprocess.PIPE:
            #print('creating stdout stream reader')
            #self.pout_thread=QThread()
            #self.pout_thread.finished.connect(self.pout_thread.deleteLater())
            self.pout=StreamReader(self.process.stdout,self.id_no,self.mach,'StdOut')#,'StdOut',self.client.id_no)
            self.pout_thread=threading.Thread(target=self.pout.run)
            self.pout_thread.start()

        else:
            self.pout=None
            self.pout_thread=None
        if self.stderr_spec==subprocess.PIPE:
            #self.perr_thread=QThread()
            #self.perr_thread.finished.connect(self.perr_thread.deleteLater())
            self.perr=StreamReader(self.process.stderr,self.id_no,self.mach,'StdErr')
            self.perr_thread=threading.Thread(target=self.perr.run)
            #self.run_stream_readers.connect(self.perr.run)
            self.perr_thread.start()

        else:
            self.perr=None
            self.perr_thread=None

        #print('telling streamreaders to run')

        #self.exit_monitor_thread=QThread()
        #self.exit_monitor_thread.finished.connect(self.exit_monitor_thread.deleteLater())
        self.exit_monitor=ExitMonitor(self.process)
        self.exit_monitor.exited.connect(self.process_exited)
        self.exit_monitor_thread=threading.Thread(target=self.exit_monitor.run)
        #self.run_stream_readers.connect(self.exit_monitor.run)
        #print('Starting exit monitor thread')
        self.exit_monitor_thread.start()
        #self.run_stream_readers.emit()
        #print('Process should be up and running now')

    def process_exited(self):
        #print('process exited')

        while self.pout or self.perr:
            if self.pout:
                if self.pout.sr_exited.wait(0.1):
                    self.pout=None
            if self.perr:
                if self.perr.sr_exited.wait(0.1):
                    self.perr=None
        try:
            self.stdout_spec.close()
        except:
            pass
        try:
            self.stderr_spec.close()
        except:
            pass
        self.exit_code=self.process.returncode
        self.running=0
        self.mach.log('Process.process_exited emitting pr_exited',level=2)
        self.pr_exited.emit(self.exit_code)
        #self.process.kill()
        #self.exited.emit()

    def receive_stdin(self,message):
        if self.stdin_spec==subprocess.PIPE:
            try:
                self.process.stdin.writelines([message])
            except Exception as e:
                self.mach.log('Unable to write to stdin process',e,level=2)

    def kill(self):
        if self.pout:
            self.pout.kill()
        if self.perr:
            self.perr.kill()
        if self.process is not None:
            self.process.kill()

count=0
class ProcessManager:
    def __init__(self,command,mach,process_table=None,event_name='ProcExit'):
        self.stdin_message=Signal(str)
        self.command=command
        self.mach=mach
        self.process=Process(command,mach)
        self.process.pr_exited.connect(self.process_exited)
        self.stdin_message.connect(self.process.receive_stdin)
        self.exit_code=-1
        self.worker_thread=threading.Thread(target=self.process.run)
        #self.operate.connect(self.process.run_process())
        self.worker_thread.start()
        self.process_table=process_table
        self.event_name=event_name
        #self.operate.emit()

    def process_exited(self,exit_code=None):
        global count
        if exit_code is None:
            self.exit_code=self.process.exit_code
        else:
            self.exit_code=exit_code
        self.mach.log('joining process worker thread')
        self.worker_thread.join()
        self.mach.log(f'About to emit bubbl {self.event_name} event',count,self.process.id_no)
        count+=1
        if self.process_table is not None:
            ui.root.after_idle(self.process_table.remove_process_by_id,self.process.id_no)
        self.mach.queue_event(OutputStreamEvent(self.event_name,self.process.id_no,self.exit_code)) #self.event_type,self.process_id))

class SynchProcess:
    def __init__(self,command,mach,exit_event):
        self.command=command
        self.mach=mach
        self.exit_event=exit_event
        self.process=Process(command,mach)
        self.process.pr_exited.connect(self.process_exited)
        self.exit_code=-1
        self.worker_thread=threading.Thread(target=self.process.run)
        #self.operate.connect(self.process.run_process())
        self.worker_thread.start()
        #self.operate.emit()

    def kill(self):
        self.process.kill()

    def process_exited(self,exit_code=None):
        if exit_code is None:
            self.exit_code=self.process.exit_code
        else:
            self.exit_code=exit_code
        self.mach.log('joining process worker thread')
        self.worker_thread.join()
        self.exit_event.set()
