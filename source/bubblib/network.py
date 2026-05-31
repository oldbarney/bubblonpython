"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import socket
import selectors
import threading
import time
from collections import deque

from bubblib.logger import Logger
from bubblib.utils import runtime_log as log


#socket.socket(socket.AF_INET,socket.SOCK_STREAM).send(b'')
#from bubblib.sysvars import SysVars
class TCPConnection:
    def __init__(self,sock,address='',host='',port=0):
        self.sock=sock
        self.host=host
        self.address=address
        self.port=port

        self.client_receiver=None
        self.tx_queue=deque()
        self.data=b''
        self.rxbuf=b''
        self._closed=threading.Event()
        self.tx_ready=threading.Event()
        self.data_ready=threading.Event()
        self.tx_thread=threading.Thread(target=self.monitor_tx,daemon=True)
        self.tx_thread.start()

    def register_receiver(self, receiver):
        #handler is function(string)
        self.client_receiver=receiver

    def send(self,data):
        if not data:
            self._closed.set()
            return
        self.tx_queue.append(data.encode())
        self.data_ready.set()

    def monitor_tx(self):
        state='notx'
        while not self._closed.is_set():
            if state=='notx':
                self.tx_ready.wait(0.1)
                if self.tx_ready.is_set():
                    state='tx'
            elif state=='tx':
                self.data_ready.wait(0.1)
                if self.data_ready.is_set():
                    self.data_ready.clear()
                    while self.tx_queue:
                        self.data+=self.tx_queue.popleft()
                    if self.data:
                        self.tx_ready.clear()
                        sent=self.sock.send(self.data)
                        self.data=self.data[sent:]
                    if self.data:
                        self.data_ready.set()
                    self.state='notx'


    def enable_send(self):
        #log('enable_send')
        self.tx_ready.set()

    def receive(self,data):
        #log('TCPConnection received',data)
        if self.client_receiver is None: #echo
            self.send(b'hello from server:'+data)
        else:
            for i in range(len(data)):
                if data[i]==10 or data[i]==13:
                    mess=(self.rxbuf+data[:i]).decode()
                    self.rxbuf=data[i+1:]
                    if self.rxbuf and data[i+1]==13 and data[i+2]==10:
                        self.rxbuf=self.rxbuf[1:]
                    #log('TCPConnection sending to client',mess)
                    #log('TCPConnection remaining',self.rxbuf)
                    self.client_receiver(mess)

                    break
            else:
                self.rxbuf+=data

    def close(self):
        self._closed.set()
        self.tx_thread.join()

class TCPServer:
    def __init__(self,host,server_port,client_handler):#False):
        self.sel = selectors.DefaultSelector()
        self.client_handler=client_handler
        if host=='localhost':
            host = socket.gethostname() #'localhost'
        self.host=host
        self.port=server_port
        self.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lsock.bind((host, server_port))
        self.lsock.listen()
        #log(f"Listening on {(host, server_port)}")
        self.lsock.setblocking(False)
        self.sel.register(self.lsock, selectors.EVENT_READ, data=None)

        self._closed=threading.Event()

        self.thr=threading.Thread(target=self.run,daemon=True)
        self.thr.start()

    def run(self):
        try:
            while not self._closed.is_set():
                events = self.sel.select(timeout=0.1)
                if events==[]:
                    continue
                for key, mask in events:
                    if key.data is None:
                        conn=self.accept_wrapper(key.fileobj)
                        self.client_handler._put(conn)
                    else:
                        self.service_connection(key, mask)
        except Exception as e:
            log("TCPServer exception:",e,level=Logger.INFO)
        self.sel.close()
        self.lsock.close()

    def _close(self):
        log('TCP server starting close procedure')
        self._closed.set()
        self.thr.join()
        self.client_handler._delete(self)

    def accept_wrapper(self,sock):
        conn, addr = sock.accept()  # Should be ready to read
        #log(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = TCPConnection(conn,address=addr[0],host=self.host,port=addr[1])
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(conn, events, data=data)
        return data

    def service_connection(self,key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            mess = sock.recv(1024)  # Should be ready to read
            if mess:
                data.receive(mess)
            else:
                #log(f"Closing connection to {data}")
                self.sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            data.enable_send()

    @property
    def closed(self):
        return not self._closed.is_set()

    @closed.setter
    def closed(self,value):
        if value:
            self._close()



class TCPClient:
    def __init__(self):
        self.sel = selectors.DefaultSelector()
        self.closed=threading.Event()
        self.thr=threading.Thread(target=self.run,daemon=True)
        self.thr.start()

    def get_connection(self, remote_host, port, client_handler=None):
        server_addr = (remote_host, port)
        log("Starting connection to",server_addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(server_addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = TCPConnection(sock, address=remote_host,
                             host=socket.gethostname(),
                             port=port)
        data.register_receiver(client_handler)
        self.sel.register(sock, events, data=data)
        return data

    def run(self):
        try:
            while not self.closed.is_set():
                events = self.sel.select(timeout=0.1)
                if events==[]:
                    continue
                for key, mask in events:
                    self.service_connection(key, mask)
        except Exception as e:
            log("TCPClient Exception",e,level=Logger.INFO)
        log('TCPClient closing')
        self.sel.close()

    def service_connection(self,key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            mess = sock.recv(1024)
            if mess:
                data.receive(mess)
            else:
                log("Closing connection to",data)
                self.sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            #log('service connection write')
            data.enable_send()

    def _close(self):
        self._closed.set()
        self.thr.join()

class UDPServer:
    def __init__(self,host,server_port,client_handler,binary=False):
        self.binary=binary
        self.client_handler=client_handler
        if host=='localhost':
            host = socket.gethostname() #'localhost'
        self.host=host
        self.client=None
        self.port=server_port
        self.lsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.lsock.bind((host, server_port))
        self.lsock.setblocking(False)
        self._closed=threading.Event()
        self.sel=selectors.DefaultSelector()
        self.sel.register(self.lsock, selectors.EVENT_READ, data=self)
        self.thr=threading.Thread(target=self.run,daemon=True)
        self.thr.start()

    def run(self):
        try:
            while not self._closed.is_set():
                events = self.sel.select(timeout=0.1)
                if events==[]:
                    continue
                for key, mask in events:
                    if mask & selectors.EVENT_READ:
                        data, addr = self.lsock.recvfrom(1024)
                        if self.client is None: #bind to first conenction
                            self.client=addr
                        #log('UDP Server rx',self.client,addr)
                        if addr==self.client:  #dont care about the port
                            if self.binary:
                                mess=data
                            else:
                                mess = data.decode()
                            #log('UDP server mess=',mess)
                            self.client_handler(mess)
                        else:
                            log('Rejecting additional clients',level=Logger.INFO)
        except Exception as e:
            log(f'UDPServer Exception:{e}',level=Logger.INFO)

    @property
    def send(self,data):
        return None
    @send.setter
    def send(self,message):
        if not self.binary:
            message=f'{message}'.encode()
        if self.client is None:
            log('Cannot send to non-existent client',level=Logger.INFO)
            return
        if message is not None: #Sends on an arbitrary port
            self.lsock.sendto(message[:1024],self.client)

    @property
    def closed(self):
        return self._closed.is_set()
    @closed.setter
    def closed(self,value):
        if value:
            self._closed.set()
    def _close(self):
        log('starting UDP Server closing procedure')
        self._closed.set()
        self.thr.join()
        self.client_handler._delete(self)

class UDPClient:
    def __init__(self, remote_host, port, client_handler,binary=False):
        self.address=(remote_host,port)
        self.client_handler=client_handler
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)

        self._closed=threading.Event()
        #self.rx_process = multiprocessing.Process(target=self.run)
        #self.rx_process.start()
        self.sel=selectors.DefaultSelector()
        self.sel.register(self.sock, selectors.EVENT_READ, data=self)

        self.thr=threading.Thread(target=self.run,daemon=True)
        self.thr.start()

    @property
    def send(self,data):
        return None
    @send.setter
    def send(self,message):
        if message is not None:
            if not self.binary:
                message=message.encode()
            self.sock.sendto(message[:1024],self.address)

    def run(self):
        try:
            while not self._closed.is_set():
                events = self.sel.select(timeout=0.1)
                if events==[]:
                    continue
                for key, mask in events:
                    if mask & selectors.EVENT_READ:
                        data, addr = self.sock.recvfrom(1024)
                        if addr==self.address:
                            if self.binary:
                                mess=data
                            else:
                                mess = data.decode().rstrip()
                            self.client_handler(mess)
                        else:
                            log(self.address,'Rejecting message from',addr ,level=Logger.INFO)
        except Exception as e:
           log(f'UDPClient Exception:{e}',level=Logger.INFO)
        log('UDPClient closing')

    def _close(self):
        self._closed.set()
        self.thr.join()

    @property
    def closed(self):
        return self._closed.is_set()
    @closed.setter
    def closed(self,value):
        if value:
            self._close()


def main():
    """
    client_manager=TCPClient()

    time.sleep(2)
    client=client_manager.get_connection('localhost',65432,lambda x:log(x))
    log('Connection is',client)
    log('Sending message in 2')
    time.sleep(2)
    client.send('Hello just the once\n')
    log('sent message')
    log('closing in 2')
    time.sleep(2)
    log('closing')
    #client.send('Hello again\n')
    #server.closed.wait(20)
    #server.closed.set()
    client.send(None)
    client_manager._close()
    """
    client=UDPClient('127.0.0.1',65432,lambda x:log('main test udprx',x))
    log('Connection is',client)
    log('Sending message in 2')
    time.sleep(2)
    client.send='Hello just the once\n'
    log('sent message')
    log('closing in 20')
    time.sleep(20)
    log('closing')
    #client.send('Hello again\n')
    #server.closed.wait(20)
    #server.closed.set()
    client.closed=True

if __name__=='__main__':
    main()