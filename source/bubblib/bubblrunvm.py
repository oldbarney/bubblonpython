"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from bubblib.utils import log


class BubblRunVM:
    def __init__(self,mach):
        self.mach = mach
        self.diags = mach.diags
        self.next_key=1
        self.value_cache={}
        self.value_stack=[]
        self.next_key=1

    def cached_ref(self,*values):
        key=self.next_key
        self.next_key+=1
        self.value_cache[key]=values
        log(f'cacheing {values} under {key}')
        return key

    def delta(self, command):
        """
            command=["diag",diagname]  #for call/return instructions and UI 'goto' undoing
                    ["vardel",name]
                    ["varassign",name,val]
                    ["tablecreate",name,[fieldnames]]
                    ["tabledestroy",name]
                    ["tableinsert",name,index[,[fields]]]
                    ["tabledelete",name,index]
                    ["tableupdaterow",name,index,[fields]]
                    ["pagedelete",index]
                    ["reset"]   - remove undos
                    ["addtoclipboard",val]
                    ["page"]
        """
        log('delta command',command[0])
        diag=self.mach.diag
        cmd = command[0]
        p1 = command[1] if len(command) > 1 else None
        p2 = command[2] if len(command) > 2 else None
        p3 = command[3] if len(command) > 3 else None
        p4 = command[4] if len(command) > 4 else None

        # print("command[0]="+cmd)
        if cmd == "diag":
            self.mach.diag=self.mach.diags[p1]

        elif cmd == "varsassign":
            #print('DELTA varsassign',p1)
            #self.mach.diag.variables.clear()
            #print('DELTA varsassign part2')
            #self.mach.diag.variables.update(p1)
            dels=self.mach.diag.variables.keys()-p1.keys()
            for k in dels:
                self.mach.diag.variables.pop(k)
            self.mach.diag.variables.update(p1)
            #print('DELTA varsassigned done')
        elif cmd == "varassign":
            sv,vn=self.mach.vref(p1)
            if sv:
                try:
                    setattr(diag.variables[sv],vn,p2)
                except Exception as e:
                    log(f'Failed to assign to system varible {p1}: {e}',level=2)
            else:
                diag.variables[p1] = p2  # Here probably right, but could use copy??
        elif cmd == "vardel":
            try:
                del (diag.variables[p1])
            except:
                pass
        elif cmd == "explicit":
            try:
                exec(p1, self.mach.diag.variables)
            except Exception as e:
                log(f'explicit undo failed to execute\n{p1}\n{e}',level=2)
        elif cmd == "targetvarassign":
            self.mach.diags[p1].variables[p2]=p3
        elif cmd == "targetvardel":
            del self.mach.diags[p1].variables[p2]
        elif cmd == "pagedelete":
            log(f'bubblrunvm deleting item {p1} from {diag.mach.current_page}',level=2)
            self.mach.current_page.remove_output(int(p1))
        elif cmd == "pageinsert":
            self.mach.current_page.add_output_thing_from_markups(p2,index=int(p1))
        elif cmd == "uniterate":
            diag.variables[p1].uniterate()
        elif cmd == "tablecreate":
            self.mach.create_table(p1,p2,p3)
        elif cmd == "tablesort":
            self.mach.unsort_table(p1,p2)
        elif cmd == "tabledestroy":
            self.mach.destroy_table(p1,False)
        elif cmd==  "tableinsert":
            self.mach.insert_table_row(p1, p2, p3, False)
        elif cmd == "tabledelete":
            self.mach.remove_table_row(p1,p2)
        elif cmd == "tableupdate":
            self.mach.get_table(p1).ok_swap_fields(p2,p3)
        elif cmd == "page_select":
            diag.mach.select_page(p1,False)
        elif cmd == "page_destroy":
            diag.mach.close_page(p1)
        elif cmd == "page_update":
            diag.mach.pages[p1].update(p2)
        elif cmd == "create_page":
            log('delta create_page')
            diag.mach.select_page(False,p1,**p2)
        elif cmd == 'push':
            diag.mach.stack.append((p1,p2))
        elif cmd == 'pop':
            diag.mach.diag,diag.mach.node=diag.mach.stack.pop()
        elif cmd == 'goto':
            diag.mach.diag=p1
            diag.mach.node=p2
            diag.mach.link=p3
        elif cmd == 'page':
            diag.mach.page_undo()
        else:
            raise Exception("Unknown diag edit command: " + cmd)