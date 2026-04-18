"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from .block import ExecutableBlock
from .bubbljson import toJSON, fromJSON
from .blockfactory import get_block, CallBlock

from .globaldefs import render_defaults
from .gutils import BUBBLImage
from .iset import Iset
from .presentation import interface_presentation

from .table import RawTable, AbstractRow
from .utils import log


def get_emptyDiagInit(): #Needs to be a function to create new instance
    return {"signature": {"params": ["#DDD"], "linknames": [],"hasloop":False, "start": 0, "loop": 0, "undoable": True}, "vars": {},
            "nodes": {}}

class ParasiticDict(dict):
    def __init__(self,host,undo_list):
        self.undo_list=undo_list
        self.host=host

    def __setitem__(self,key,value):
        if key.startswith('_'):
            self.host[key]=value
        elif key in self.host:
            self.undo_list.append(['varassign',key,self.host[key]])
            self.host[key]=value
        else:
            self.undo_list.append(['vardel',key])
            self.host[key]=value

    def __getitem__(self,key):
        return self.host[key]

    def _sethostitem(self,key,value):
        self.host[key]=value

    def __contains__(self,key):
        return key in self.host

class NodeHolder:

    def __init__(self, name, nodes_init,mach=None):
        self.name = name
        self.mach=mach
        self.nodes = {int(n): get_block(self, int(n), nodes_init[n]) for n in nodes_init}

    def get_json_for_nodes(self, selection: Iset == None, base=1):
        if selection == None:
            selection = Iset(self.nodes)
        #print(f'get_json_for_nodes:selection={selection}')
        json = toJSON({n: self.nodes[n].init for n in selection if n in self.nodes})  #cater for unundoably removed
        #print(f'intermediate json={json}')
        init = fromJSON(json)
        nodemap = {0: 0}
        next = base
        for n in init:
            nodemap[int(n)] = next
            next += 1
        #print(f'nodemap={nodemap}')
        for n in init:
            links = init[n]["links"]
            for ln, link in enumerate(links):
                try:
                    links[ln] = nodemap[link]
                except:
                    links[ln] = 0
        return toJSON({nodemap[int(n)]: init[n] for n in init})

    def severed_links_to(self, node_set: Iset):
        result = []
        for n in self.nodes:
            block = self.nodes[n]
            if n in node_set:
                for ln, link in enumerate(block.links):
                    if link not in node_set:
                        result.append((n, ln, link))
                        block.links[ln] = 0
            else:
                for ln, link in enumerate(block.links):
                    if link in node_set:
                        result.append((n, ln, link))
                        block.links[ln] = 0
        return result  # [(n,ln,oldlink),...]

    def delete_nodes(self, node_set):
        for n in node_set:
            del (self.nodes[n])

    def apply_links(self, link_list):
        for (n, ln, link) in link_list:
            self.nodes[n].links[ln] = link

def is_json_node_set(text):
    try:
        NodeHolder('_',fromJSON(text))
        return True
    except:
        return False

def bubbl_json_dragged(json,x,y):
    #print(f'json in >>{json}<<')
    init=fromJSON(json)
    dx=min(init[n]["pos"][0] for n in init)
    dy=min(init[n]["pos"][1] for n in init)
    for n in init:
        init[n]["pos"][0]+=int(1+x/render_defaults.grid-dx)
        init[n]["pos"][1]+=int(1+y/render_defaults.grid-dy)
    result=toJSON(init)
    #print(f'jsonout=>>{result}<<')
    return result

class BubblDiag(NodeHolder):
    # This signal is invoked by the block param-editor vm

    def __init__(self, machine, name, init=None):
        if init == None:
            init = get_emptyDiagInit()
        NodeHolder.__init__(self, name, init['nodes'],mach=machine)
        for node in self.nodes.values():
            if node.snappable:
                node.position[0]=int(node.position[0])
                node.position[1]=int(node.position[1])

        self.sig = init['signature']
        # print_(f'init["node"]={init["nodes"]}')
        self.variables = init['vars'].copy()
        self.variables.update(machine.sys_vars)
        #self._undoable_vars=ParasiticDict(self.variables,machine.undo_list)
        #self._undoable_vars=self.variables
        self.params = self.sig['params']  #[0] is colour [1:] are parameters from caller: @prefix=>i/o
        self.undoable = self.sig['undoable']
        self.ensure_params_in_vars()

        if self.has_loop:
            self._links=[int(self.sig["start"]),int(self.sig["loop"])]
        else:
            self._links=[int(self.sig["start"])]

        try:
            self.interface_pos=self.sig["pos"]
        except:
            if self.links[0]!=0:
                p=self.nodes[self.links[0]].position
                self.interface_pos=[p[0],p[1]-10]
            else:
                self.interface_pos=[10,2]
        try:
            self.interface_size=self.sig["size"]
        except:
            self.interface_size=self.sig["size"]=[7,1]
        self.interface_size[1]=len(self.params)

        #print('About to create interface block')
        self.nodes[0]=InterfaceBlock(self)
        #print('interface node is ',toJSON(self.nodes[0].init))

    @property
    def has_loop(self):
        try:
            return self.sig['hasloop']
        except KeyError:
            return False

    @has_loop.setter
    def has_loop(self,value):
        changed=self.has_loop!=value
        self.sig['hasloop']=value
        #print('setting has_loop to',value,'chamged',changed)
        if changed:
            if value:
                self.links.append(0)
            else:
                self.links.pop()

    @property
    def links(self):
        return self._links

    def __str__(self):
        return f'BubblDiag:{self.name} with {len(self.nodes)} nodes'

    def compile_nodes(self):
        for node in self.nodes:
            if node and isinstance(self.nodes[node], ExecutableBlock):
                #print('ABOUT TO COMPILE ',node,self.nodes[node].type_name)
                try:
                    self.nodes[node].compile_code()
                except Exception as e:
                    self.nodes[node].code=self.nodes[node].code_text()
                    self.nodes[node].undoable_code = self.nodes[node
                            ].undoable_code_text()

    def normal_variable_names(self,include_params=False):

        return [vn for vn in self.variables
                if (
                    (vn !="") and
                    (not vn.startswith('_')) and
                    (include_params or
                       (not vn in self.params[1:]) and
                       (not ('@'+vn) in self.params[1:])) and
                    (   isinstance(self.variables[vn],(
                        int,
                        float,
                        complex,
                        str,
                        list,
                        tuple,
                        range,
                        dict,
                        Iset,
                        AbstractRow,
                        BUBBLImage)) # or   todo include local table variables here?
                        #(  isinstance(self.variables[vn],RawTable) and
                        #  (self.variables[vn] not in self.mach._sys_tables() and
                        #   self.variables[vn].name
                        #   )
                        #)
                    )
                ) ]
    def get_init(self):
        self.sig['pos']=self.nodes[0].position
        self.sig['size'][1]=len(self.params)
        self.sig['start']=self.links[0]
        try:
            self.sig['loop']=self.links[1]
        except:
            self.sig['loop']=0
        return {'signature': self.sig,
                'vars': {vn:self.variables[vn] for vn in self.normal_variable_names()},
                'nodes': {n: self.nodes[n].init for n in self.nodes if n},
                }

    def ensure_params_in_vars(self):
        for pn in self.params[1:]:
            pn = pn[1:] if pn.startswith('@') else pn
            if pn not in self.variables:
                self.variables[pn] = ''

    def par_val(self, index):
        return self.variables[self.params[index]]

    def nodes_using_block(self, used_diag):
        return Iset(node for node in self.nodes
                      if isinstance(self.nodes[node], CallBlock) and self.nodes[node].target_name == used_diag.name)

    def uses(self):  # Could return set, but blocks may need individually adjusting to new signature(s)
        return [self.nodes[node].target_name for node in self.nodes if isinstance(self.nodes[node], CallBlock)]

class InterfaceBlock(ExecutableBlock):
    """Diagram Interface
    This block defines how the current diagram is usable as
    a block in other diagrams.

    The diagram can have one or more of its local variables used
    as input or input/output parameters. These are initialised on
    entry to the diagram and values can optionally be written to
    the caller's variable(s) on exiting the diagram (or 'returning
    from the call').

    This block also defines what named output links the block
    has and can optionally enable a 'loop' input, allowing the
    diagram to behave with separate initialisation and
    repeating code.

    The diagram can also be optimised for speed by deselecting the
    'undoable' option.  This prevents the BUBBL vm from generating
    back-tracking data as it runs.
    """
    def __init__(self,diag):
        #print('CREATING INTERFACEBLOCK for',diag.name)
        presentation=interface_presentation
        init=fromJSON(toJSON(presentation['default_init']))
        #"default_init": {"params": [], "type": "INTERFACE", "size": [5, 1], "pos": [0, 0], "links": [0]},
        init['pos']=diag.interface_pos
        init['size'][1]=len(diag.params)
        #init['size']=diag.interface_size
        #init['size'][1]=len(diag.params)
        self.diag=diag  #ugly fix to trick edit executable block editor with 'virtual' block
        #init['params']=self.get_params()[0]
        #params,linknames=self.get_params()
        init['params']=diag.params
        #print('interfaceblock params is ',params)
        ExecutableBlock.__init__(self,diag, 0, init, presentation)

    def get_params(self):
        result=[self.diag.params[0]]
        result.append('1' if self.diag.has_loop else '0')
        result.append('1' if self.diag.undoable else '0')
        result+=self.diag.params[1:]
        return result,list(self.diag.sig['linknames'])

    def put_params(self,params,link_names):
        self.diag.params.clear()
        self.diag.params.append(params[0])
        self.diag.has_loop = params[1]=='1'
        self.diag.undoable = params[2]=='1'
        if self.diag.undoable!=self.diag.sig['undoable']:
            self.diag.sig['undoable']=self.diag.undoable
            self.diag.compile_nodes()
        for param in params[3:]:
            self.diag.params.append(param)
        self.diag.ensure_params_in_vars()
        self.diag.sig['linknames'][:]=link_names

    @property
    def links(self):
        return self.diag.links
