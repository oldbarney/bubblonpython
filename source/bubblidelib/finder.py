"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import os

from bubblib.basebubblapp import BaseBUBBLApp
from bubblib.bubbljson import fromJSON
from bubblib.bubblmach import BBSM
from bubblib.globaldefs import ExState
from bubblib.utils import log

class Finder:
    def __init__(self,x,y,ide,settings):
        self.bubblIDE=ide
        init=BBSM.sys_init()
        #init=ide.bubbl_app.sys_mach.get_init()

        #with open("bubblib"+os.sep+"bubblutils.pbub","r") as f:
        #    init=fromJSON(f.read())
        #    init = init['machines']['main']

        self.mach=BBSM(self,'finder',init,external_db=False)
        self.mach.history=ide.mach.history
        self.mach.machine_state_changed.connect(self.mach_state_changed)
        self.mach.diags['find'].variables['settings']=settings
        self.mach.diags['find'].variables['target']=ide.mach
        self.mach.diags['find'].variables['x']=x
        self.mach.diags['find'].variables['y']=y

        log('going to ',self.mach.diags['finder'].links[0])
        #print('sending goto')
        self.mach.command('goto','finder',self.mach.diags['finder'].links[0])
        #print('goto sent')
        self.mach.command('run')

    def handle_page_event(self,*_args):
        pass

    def mach_state_changed(self):
        log('finder mach_state_changed',repr(self.mach.state))
        #print('finder mach_state_changed', repr(self.mach.state))

        #if self.mach.state == ExState.stopped_on_node:
        #    log('diag',self.mach.diag.name,self.mach.node,self.mach.link)
        #    #print('FINDER STOPPED ON NODE',f'diag:{self.mach.diag.name} node:{self.mach.node} link:{self.mach.link}',
        #    #       self.mach.diag.nodes[self.mach.node].type_name)
        #    #print('')

        if self.mach.state == ExState.exited: #in (ExState.stopped_on_node,ExState.stopped_on_link):
            result=self.mach.diags['finder'].variables['result']
            log('result',result,'finder stopped on link')
            if result=='done':
                self.mach.machine_state_changed.disconnect(self.mach_state_changed)
                self.bubblIDE.found(None,None,None)
                self.kill()
            else:
                log('REALLY FOUND')
                #print('REALLY FOUND')
                finds=self.mach.diags['find'].variables['finds']
                log('REALLY FOUND finds',finds)
                #print('REALLY FOUND finds', finds)

                diag=self.mach.diags['find'].variables['diag']
                log('REALLY FOUND diag',diag)
                settings=dict(self.mach.diags['find'].variables['settings'])
                log('REALLY FOUND',diag,finds,settings)
                #print('REALLY FOUND all', diag, finds, settings)

                self.bubblIDE.found(diag,finds,settings)
                #print('Found now looping')
                self.mach.command('goto','finder',
                                  self.mach.diags['finder'].links[1],
                                  no_signal=True)
                #print('Found after goto',self.mach.state)
                self.mach.command('run')
                #print('after Found after goto run', self.mach.state)

        #else:
        #    print('Finder state',repr(self.mach.state))

    def kill(self):
        if self.mach is None:
            return
        self.mach.command('kill')
        log('Finder machine told to die')
        return

class Importer:
    def __init__(self,ide,path):
        self.bubblIDE=ide
        init=BBSM.sys_init()
        self.mach=BBSM(self,'importer',init,external_db=False)
        self.mach.history=ide.mach.history
        self.mach.machine_state_changed.connect(self.mach_state_changed)
        self.mach.diags['importrunner'].variables['path']=path

        log('going to ',self.mach.diags['importrunner'].links[0])
        self.mach.command('goto','importrunner',self.mach.diags['importrunner'].links[0])
        self.mach.command('run')

    def handle_page_event(self,*_args):
        pass

    def mach_state_changed(self):
        log('importer mach_state_changed',repr(self.mach.state))
        #if self.mach.state == ExState.stopped_on_node:
        #    log('diag',self.mach.diag.name,self.mach.node,self.mach.link)

        if self.mach.state == ExState.exited: #stopped_on_link:
            result=self.mach.diags['importrunner'].variables['result']
            log('result',result,'importrunner stopped on link')
            if result=='Ok':
                log('IMPORTED')
                init=self.mach.diags['importrunner'].variables['init']
                self.bubblIDE.imported(init)
            self.mach.machine_state_changed.disconnect(self.mach_state_changed)
            self.kill()

    @staticmethod
    def get_pbub_from_file(filename):
        return BaseBUBBLApp.get_pbub_from_file(filename)

    def kill(self):
        if self.mach is None:
            return
        self.mach.command('kill')
        log('Importer machine told to die')
        return


