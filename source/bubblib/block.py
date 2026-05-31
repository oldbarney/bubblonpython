"""block defines Block and ExecutableBlock classes
Block is the base class for all built-in blocks.
Everything that can be shown on the BUBBL desktop
or Diagram is derived from Block.
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"

class Block():  #todo could store editing history in block
    def __init__(self, diag, no, init, presentation):
        self.diag = diag
        self.no = no
        if init==None:
            init=presentation["default_init"]
        self.init = init
        self.presentation = presentation
        self.type_name = init["type"]
        self.params = init["params"]
        self._links = init["links"]
        #print('links is',self.links)
        self.snappable=False

        self.position = init["pos"]
        #print('assigned position to block from',init)
        self.dim = init["size"]

    @property
    def links(self):
        return self._links


class ExecutableBlock(Block):
    def __init__(self, diag, no, init, presentation):
        '''
        :param init: initialisation dictionary from source file
        :param executionMode:  singular, modal, asynch
        :param codeText:
        :param undoCodeText:
        :param auxCodeText:
        '''

        #print(f'Executable block init:diag={diag.name},\nno={no},\ninit={init},\npres={presentation}')
        super().__init__(diag, no, init, presentation)
        self.snappable=True
        self.code = None
        self.undoable_code = None
        self.auxcode = None
        self.undoable_auxcode = None

    def dontcompileCode(self):
        #print(f'not compiling :{self.no}')
        self.code = self.code_text()
        #print(f'code to compile is {self.code}')
        self.undoable_code = self.undoable_code_text()
        #print(f'undoable code to compile is {self.undoable_code}')
        self.auxcode = self.auxcode_text()
        self.undoable_auxcode = self.undoable_auxcode_text()
        if self.type_name== 'FOR':
            loops=[n for n in self.diag.nodes if self.diag.nodes[n].type_name == 'LOOP' and self.diag.nodes[n].links[0] == self.no]
            for loop in loops:
                self.diag.nodes[loop].compile_code()

        #print(f'didntt compile :{self.no}')

    def code_text(self):
        return ''

    def undoable_code_text(self):
        return ''

    def auxcode_text(self):
        return ''

    def undoable_auxcode_text(self):
        return ''

    def compile_code(self):
        if self.diag.undoable:
            self.undoable_code = self.code = compile(self.undoable_code_text(),
                '_UBLOCK_',
                #f'diag_code:{self.diag.name} node {self.no}',
                                                     'exec')
        else:
            self.code = compile(self.code_text(),'_BLOCK_','exec')
            self.undoable_code = compile(self.undoable_code_text(),'_UBLOCK_','exec')

        #self.dontcompileCode()
        if self.type_name== 'FOR':
            if self.diag.undoable:
                self.undoable_auxcode =self.auxcode = compile(
                    self.undoable_auxcode_text(),'_UAUX_BLOCK_','exec')
                    #f'diag_auxcode:{self.diag.name} node {self.no}', 'exec')
            else:
                self.auxcode= compile(self.auxcode_text(),'_AUX_BLOCK_','exec')

                    #f'diag_auxcode:{self.diag.name} node {self.no}', 'exec')
                self.undoable_auxcode = compile(self.undoable_auxcode_text(),'_UAUX_BLOCK_','exec')
                    #f'diag_auxcode:{self.diag.name} node {self.no}', 'exec')
            loops=[n for n in self.diag.nodes
                   if self.diag.nodes[n].type_name == 'LOOP' and
                        self.diag.nodes[n].links[0] == self.no]
            for loop in loops:
                try:  #todo Not sure why this try-except is here
                    self.diag.nodes[loop].compile_code()
                except:
                    self.diag.nodes[loop].code=self.diag.nodes[loop].code_text()
                    self.diag.nodes[loop].undoable_code=self.diag.nodes[loop].undoable_code_text()
        else:
            self.auxcode = None
            self.undoable_auxcode = None


    def exec(self):
        exec(self.code, self.diag.variables)

    def exec_undoable(self):
        exec(self.undoable_code,self.diag.variables)

    def exec_undoably(self):
        exec(self.code,self.diag.variables)

    def get_exec_code_text(self):
        if self.diag.undoable:
            return self.undoable_code_text()
        else:
            return self.code_text()