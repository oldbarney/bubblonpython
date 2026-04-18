"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from bubblib.bubbldiag import BubblDiag, NodeHolder
from bubblib.bubbljson import fromJSON
from bubblib.block import ExecutableBlock
from bubblib.globaldefs import render_defaults, contains_snaps, executable_types
from bubblib.blockfactory import get_block, CallBlock
from bubblib.iset import Iset
from bubblib.utils import log


class Link_spec:
    def __init__(self, node: int, linkNo: int):
        self.node = node
        self.linkNo = linkNo

class DiagEdVM:

    def __init__(self,ide):
        self.ide=ide
        self.mach = mach= ide.mach
        self.diags = mach.diags
        self.undos=[]

    def make_new_diag(self,name,undoable=True):
        diag=BubblDiag(self.mach,name)
        if undoable:
            self.add_undo(['delete_diag',diag])
        self.mach.diags[name]=diag

        log('new_diag in diageditorvm')
        #name=
        #new_diag=

    def reset(self, diag):
        self.undos =[]   #contains lists with ['command',...]

    def mark(self):
        self.add_undo("milestone")

    def delete_diag(self,diag_name,undoable=True):
        if undoable:
            self.add_undo(['insert_diag',self.diags[diag_name]])
        self.diags.pop(diag_name)
        self.ide.diag_deleted(diag_name)

    def rename_diag(self,diag,new_name,undoable=True):
        old_name=diag.name
        if undoable:
            self.add_undo(['rename_diag',diag,old_name])

        diag.name=new_name
        for diag in self.diags.values():
            calls=[node for node in diag.nodes.values()
                    if node.type_name=='CALL' and
                       node.params[0]==old_name]
            for call in calls:
                call.target_name=call.params[0]=new_name

        self.diags[new_name]=self.diags.pop(old_name)
        self.ide.diag_name_changed(old_name,new_name)

    def do_import(self,diag_dict):
        def renamed(dn):
            nn=dn+'_'
            while nn in self.diags or nn in diag_dict:
                nn+='_'
            for diag in diag_dict.values():
                calls=[node for node in diag['nodes'].values()
                       if node['type']=='CALL' and
                       node['params'][0]==dn ]
                for call in calls:
                    call['params'][0]=nn
            return nn

        dn_map={}

        for d in diag_dict:
            if d in self.diags:
                nn=renamed(d)
                dn_map[d]=nn
            else:
                dn_map[d]=d
        self.mark()
        for dn in diag_dict:
            diag = BubblDiag(self.mach, dn_map[dn], diag_dict[dn])
            self.mach.diags[dn_map[dn]]=diag
            self.add_undo(['delete_diag',diag])

        for dn in diag_dict:
            self.mach.diags[dn_map[dn]].compile_nodes()
        self.ide.refresh_factory()

    def make_link(self, diag, node_no, link_no, target, undoable):
        #print(f'makeLink diag:{diag} node:{node} link:{link} target:{target}')
        if undoable:
            self.add_undo(["link", diag, node_no, link_no, diag.nodes[node_no].links[link_no]])
        diag.nodes[node_no].links[link_no] = target
        try:
            diag.nodes[node_no].compile_code()
        except Exception as e:
            log('Failed to compile',e,level=2)

    def translate_nodes(self, diag, nodes: Iset, dx, dy, undoable):
        #print('translating nodes',nodes,'by',dx,dy)
        for n in nodes:
            p=diag.nodes[n].position
            p[0] += dx
            if round(p[0]*render_defaults.grid)%render_defaults.grid==0:
                p[0]=round(p[0])
            p[1] += dy
            if round(p[1]*render_defaults.grid)%render_defaults.grid==0:
                p[1]=round(p[1])
        if undoable:
            #print('undoably translated')
            if self.undos!=[]:
                last=self.undos[-1]  #combine with previous translations
                if last[0]=='translate' and last[1]==diag and last[2]==nodes:
                    dx-=last[3]
                    dy-=last[4]
                    self.undos.pop(-1)
            self.add_undo(["translate",diag, Iset(nodes), -dx, -dy])
        #diag.nodes_moved.emit(Iset(nodes))

    def copy_blocks(self,diag,destdiag,nodes,undoable):

        #returns the new node numbers of copied blocks
        newnodesjson=diag.get_json_for_nodes(nodes)
        #print(f'copye_blocks newnodesJSON={newnodesjson}')
        newnos=self.get_append_node_nos(destdiag,len(nodes))
        self.add_blocks_from_json(destdiag,newnodesjson,newnos,undoable,[0,0])  #also emits signal with new diag name and block numbers

    def copy_blocks_and_position(self,diag,destdiag,nodes,pos,undoable):
        #print('copying blocks and positioning ')
        if not nodes:
            return
        sx=min(diag.nodes[n].position[0] for n in nodes)
        sy=min(diag.nodes[n].position[1] for n in nodes)
        dx=pos[0]-sx
        dy=pos[1]-sy
        #print(f'dx={dx} dy={dy}')
        newnodesjson=diag.get_json_for_nodes(nodes)
        #print(f'copye_blocks newnodesJSON={newnodesjson}')
        newnos=self.get_append_node_nos(destdiag,len(nodes))
        self.add_blocks_from_json(destdiag,newnodesjson,newnos,undoable,[dx,dy])  #also emits signal with new diag name and block numbers
        #self.translate_nodes(destdiag,newnos,dx,dy,undoable)

    def sever_links_to(self,diag,nodes,undoable):
        linkdeltas=diag.severed_links_to(nodes)
        changed_links=Iset(n for (n,_,_) in linkdeltas)
        if undoable:
            for (n,l,link) in linkdeltas:
                self.add_undo(['link',diag,n,l,link])

    def move_blocks(self,diag,destdiag,nodes,dest_node_nos,undoable):
        self.sever_links_to(diag,nodes,undoable)
        '''for n in nodes:
            print(f'checking node {n}')
            for b in diag.nodes:
                if b not in nodes:
                    if n in diag.nodes[b].links:
                        raise Exception(f'Failed to Sever links from {b} to {n}')
        '''
        newnodesJSON=diag.get_json_for_nodes(nodes)
        #print(f'move_blocks newnodesJSON={newnodesJSON}')
        if dest_node_nos is None:
            dest_node_nos=self.get_append_node_nos(destdiag,len(nodes))
        self.add_blocks_from_json(destdiag,newnodesJSON,dest_node_nos,False,[0,0])
        if undoable:
            self.add_undo(['move',destdiag,diag,dest_node_nos,nodes])
            try:
                if diag.sig["start"] in nodes:
                    self.add_undo(['setstart',diag,diag.links[0]])
            except:
                pass
        self.destroy_blocks(diag,nodes)

    def set_start(self,diag,node,undoable):
        if not isinstance(diag, BubblDiag):
            return
        if undoable:
            self.add_undo(['setstart',diag,diag.sig["start"]])
        diag.links[0]=node

    def get_append_node_nos(self,diag,count):
        if len(diag.nodes) == 0:
            base = 0
        else:
            base = max(int(n) for n in diag.nodes)
        return Iset(range(base+1,base+count+1))

    def get_normalised_init_from_json(self,json):
        init = fromJSON(json)
        if len(init)>0: #normalise positions of nodes
            left=min(init[n]["pos"][0]-(init[n]["size"][0]//2 if init[n]["type"] in executable_types else 0) for n in init)
            top=min(init[n]["pos"][1] for n in init)
            for ni in init.values():
                ni["pos"][0]-=left
                ni["pos"][1]-=top
        return init

    def add_blocks_from_json(self,diag,json,newnos,undoable,offset):
        #print('json',json)
        #print(f'adding blocks from json={json}','offset[1]=',offset[1])
        #init = bubbljson.fromJSON(json)
        if undoable:
            init=self.get_normalised_init_from_json(json)
        else:
            init = fromJSON(json)

        if newnos==None:
            newnos=self.get_append_node_nos(diag,len(init))
        #print(f'newNos={newnos}')
        nodemap={0:0}
        for i,n in enumerate(init):
            nodemap[int(n)]=newnos[i]
        #print(f'add_blocks_from_json nodemap={nodemap}')
        do_snap=contains_snaps(init)
        if undoable:
            #print(f'adding undo destroy {newnos}')
            self.add_undo(["destroy",diag,newnos])
        for ns in init:
            #print(f'ns={ns}')
            newnodeinit=init[ns]
            links=init[ns]["links"]
            for i in range(len(links)):
                links[i]=nodemap[links[i]]
            newn=nodemap[int(ns)]
            #block
            diag.nodes[newn]=get_block(diag, newn, newnodeinit)
            #print('got block')
            if isinstance(diag, BubblDiag) and isinstance(diag.nodes[newn], ExecutableBlock):
                try:
                    diag.nodes[newn].compile_code()
                except:
                    diag.nodes[newn].code=diag.nodes[newn].code_text()
                    diag.nodes[newn].undoable_code=diag.nodes[newn].undoable_code_text()

        #print(f'added_blocks_from_json emitting nodesInserted:{diag.name},{newnos}')

        if do_snap:
            dix = round(offset[0]/render_defaults.grid)
            diy = round(offset[1]/render_defaults.grid)
            if dix or diy:
                self.translate_nodes(diag,newnos, dix, diy,undoable=undoable)
        else:
            self.translate_nodes(diag,newnos,offset[0]/render_defaults.grid,offset[1]/render_defaults.grid,undoable=undoable)
    '''
    def new_block(self, diag, block_type, variant, undoable):  # returns No. of block
        if len(diag.nodes) == 0:
            next = 1
        else:
            next = max(int(n) for n in diag.nodes) + 1

        if undoable:
            self.add_undo(["destroyblock", diag, next])
        if variant == None:
            diag.nodes[next] = blockFactory[block_type](diag,next,None)
        else:
            diag.nodes[next] = blockFactory[block_type](diag,next,variant)

        self.nodesInserted.emit(diag.name, Iset(next))
        # print("NEWBLOCK",next)
        return next
    '''

    def destroy_blocks(self, diag, nodes):
        #print(f'diageeditorvm destroying blocks {nodes}in diag:{diag.name}')
        diag.death_row=Iset(nodes)

        try:
            if diag.links[0] in nodes:
                diag.links[0]=0
        except:
            pass

        for node in nodes:
            try:
                del diag.nodes[node]
            except KeyError:
                log('no node to destroy',node)

    def change_block_size(self,diag,node,w,h,undoable):
        block=diag.nodes[node]
        if undoable:
            self.add_undo(["change_block_size",diag,node,block.dim[0],block.dim[1]])
        diag.nodes[node].dim[0]=w
        diag.nodes[node].dim[1]=h
        #print('change block size')

    def update_calls_to_diag(self,target,undoable=False):
        target_length=len(target.params)
        for diag in self.mach.diags.values():
            for node in diag.nodes.values():
                #print('NODE',node)
                if isinstance(node,CallBlock):
                    #print('NODE',node.target_name,target.name)
                    if node.target_name==target.name:
                        #print('MODIFYING',target.params,node.params)
                        if len(node.params)!=target_length:
                            #BlockEditor.edit_block_params(node,['group'])
                            while len(node.params)<target_length:
                                #BlockEditor.edit_block_params(node,['ins',len(node.params),''])
                                node.params.append('')
                            while len(node.params)>target_length:
                                #BlockEditor.edit_block_params(node,['del',len(node.params)-1,''])
                                node.params.pop(-1)
                            #BlockEditor.edit_block_params(node,['endgroup'])

    def _delta(self, command, undoable=False):
        """
            command=["move",diag,destdiag,{nodes}]
                    ["copy",diag,destdiag,{nodes}]  src_nodes->clipboard
                    ["link",diag,src_node,src_link,dest_node]
                    ["translate",diag,nodes:intset,dx,dy]
                    ["upd",diag,node,node-object]
                    ["sigins",diag,ins,name]
                    ["sigassign",diag,ind,name]
                    ["sigdel",diag,ind]

                    ["vardel",diag,name]
                    ["varassign",diag,name,val]

                    ["tablecreate",diag,name,[fieldnames]]
                    ["tabledestroy",diag,name]
                    ["tableinsert",diag,name,index[,[fields]]]
                    ["tabledelete",diag,name,index]
                    ["tableupdaterow",diag,name,index,[fields]]

                    ["newblock",diag,block_id,variant]
                    ["destroyblock",diag,blockNo]
        """
        #print(f'command:{command}')



        cmd = command[0]
        diag = command[1] if len(command) > 1 else None
        p1 = command[2] if len(command) > 2 else None
        p2 = command[3] if len(command) > 3 else None
        p3 = command[4] if len(command) > 4 else None
        p4 = command[5] if len(command) > 5 else None

        # print("command[0]="+cmd)
        if cmd == "link":
            self.make_link(diag, p1, p2, p3, undoable)

        elif cmd == "varassign":
            if undoable:
                if p1 in diag.variables:
                    self.add_undo(["vardel",diag,p1])
                else:
                    self.add_undo(["varassign",diag,p1, diag.variables[p1]])
            diag.variables[p1] = p2  # Here probably right, but could use copy??
        elif cmd == "vardel":
            if undoable:
                self.add_undo(["varassign",diag, p1, diag.variables[p1]])
            del (diag.variables[p1])
        elif cmd == "translate":
            self.translate_nodes(diag, p1, p2, p3, undoable)
        elif cmd == "destroy":
            self.destroy_blocks(diag, p1)
        elif cmd == "copy":
            self.copy_blocks(diag,p1,p2,undoable)
            #[copy,diag,destdiag,nodeset]
        elif cmd == "move":
            self.move_blocks(diag,p1,p2,p3,undoable)
        elif cmd == "change_block_size":
            self.change_block_size(diag,p1,p2,p3,undoable)
        elif cmd == "setstart":
            self.set_start(diag,p1,undoable)
        elif cmd =='rename_diag':
            self.rename_diag(diag,p1,undoable)
        elif cmd =='delete_diag':
            self.delete_diag(diag.name,undoable)
        elif cmd=='insert_diag':
            self.diags[diag.name]=diag
        else:
            raise Exception("Unknown diag edit command: " + cmd)

    def undo(self):  #undoes to last milestone
        while True:
            try:
                c = self.undos.pop()
                if c=='milestone':
                    return
                self._delta(c)
            except IndexError:
                return

    def add_undo(self,command):
        #if command[0]!='translate':
        #   log('UNDOABLE',command)
        self.undos.append(command)