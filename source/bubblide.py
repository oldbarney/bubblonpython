import io
import shutil
import json
import tkinter as tk
import webbrowser
import zipfile
from collections import deque
from io import StringIO
from threading import Event
from tkinter import messagebox, colorchooser

import sys
import os
version='3.0.1 alpha'

if os.path.dirname(os.path.abspath(__file__)).endswith('bubblib.zip'):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) )
else:
    sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+
                    os.sep+'bubblib.zip')
from bubblib.licensing import licensing_texts

from bubblib.bubblrunvmtools import unscrambled_exception
from bubblidelib.pythoneditor import PythonEditor

from bubblib.historymanager import HistoryTable
from bubblib.table import Table

from bubblidelib.homebuilder import create_home
from bubblib.logger import Logger, get_log_level, log_level_map, MyStringIO, \
    StringLogger
from bubblib.utils import now, log, set_logger_func, set_log_level,print_
print_('BUBBLIDE sys.path[0]',sys.path[0])
from bubblidelib.textviewer import TextViewer, PythonExceptionViewer

from bubblib.filedialog import get_file_dialog
from bubblib.modaldialogs import AskUserDialog
from bubblib.simplebubblapp import app_string
from bubblib.basebubblapp import BaseBUBBLApp
from bubblidelib.finder import Finder, Importer

home=os.path.dirname(os.path.abspath(sys.argv[0]))+os.sep+'bubblide.cfg'
if not os.path.isfile(home):
    create_home(home[:-12])
_config_file = home

_default_config = {'recent': [],
           'state_map': {},
           'tkinterfiledialog': False,
           'loglevel': 2,
           'ideloglevel': 2,
           'history': [],
           'debugtostdout': False
           }

try:
    with open(_config_file, 'r') as f:
        _config = json.loads(f.read())
        if 'history' not in _config:
            _config['history']=[]
        for key,value in _default_config.items():
            if key not in _config:
                _config[key]=value
        log('config loaded',level=Logger.DEBUG)
except:
    log('failed to load config, setting defaults',level=Logger.INFO)
    _config = _default_config

from bubblib.acknowledgements import acknowledgement_text
from bubblib.gutils import icon
from bubblib.inputbox import InputBox
from bubblidelib.blockeditor import BlockEditor
from bubblib.bubblapp import BUBBLApp, newAppInit
from bubblidelib.bubblconsole import Console
from bubblib.bubbldiag import BubblDiag, NodeHolder
from bubblidelib.bubbldiageditor import BubblDiagEditor
from bubblidelib.diageditorvm import DiagEdVM
from bubblib.editorframe import EditorWindow, Minimised
from bubblib.globaldefs import ExState, DiagEditorState, scale_view, \
    render_defaults
from bubblib.mywidgets import RuntimeErrorDialog
from bubblib.popupchoice import PopupChoice
from bubblidelib.dialog import popup_line_settings,  popup_config_editor
from bubblib.uiserver import ui
from bubblib.bubbljson import toJSON
from bubblidelib import bubblhelp
from bubblib.utils import log


class IDE:#(UIClient):
    def __init__(self):
        self.runtime_log_viewer=None
        self.stdout_viewer=None
        self.log_viewer = None
        self.initial_stdout = sys.stdout
        self.debug_to_stdout=False
        sys.stdout=self.captured_stdout = MyStringIO(self.update_stdout_viewer)
        self.ide_log = StringLogger(changed_func=self.update_ide_log_viewer)

        set_logger_func(self.ide_log.log)  # this does nothing yet ! -here todo 'log' calls utils.logger_func
        # lambda *args,**kwargs:ui.fast_call(
        #                self.logger.log,*args,**kwargs))

        log('creating desktop', level=Logger.DEBUG)
        self.stacking_order = []
        self._diag_clipboard=NodeHolder('_clipboard', {})
        self._deleted=NodeHolder('_deleted', {})

        ui.root.after_idle(self.create_desktop)
        ui.run()
        #UIClient.__init__(self,
        #                  start_delay=1,
        #                  init_func=self.create_desktop,
        #                  ui_master=True)

        # scale_view('tiny')


    def create_desktop(self):

        self.console = None
        self.diag_editors = {}
        self.mach = None
        self.edvm = None
        self.mach_state = ExState.quiescent
        # self.mouse_moved_event=EventMonitor(self.mouse_moved)
        self.desktop_window = tk.Toplevel(ui.root, width=800, height=600)
        self.desktop_window.title(f'BUBBL On Python V{version}')
        self.desktop_window.option_add('*tearOff', False)
        self.desktop_window.protocol("WM_DELETE_WINDOW", self.exit)
        menubar = tk.Menu(self.desktop_window)
        self.file_menu = tk.Menu(menubar)

        menubar.add_cascade(menu=self.file_menu, label='File')
        self.file_menu.add_command(label='New',
                                   image=icon('new'), compound=tk.LEFT,
                                   command=self.new_app)

        self.file_menu.add_command(label='Open',
                                   image=icon('open'), compound=tk.LEFT,
                                   command=self.load)
        self.file_menu.add_command(label='Open Recent',
                                   image=icon('open'), compound=tk.LEFT,
                                   command=self.recent)
        self.file_menu.add_command(label='Save',
                                   image=icon('save'), compound=tk.LEFT,
                                   command=self.save)
        self.file_menu.add_command(label='Save-as',
                                   image=icon('saveas'), compound=tk.LEFT,
                                   command=self.save_as)
        self.file_menu.add_command(label='Archive/Milestone',
                                   image=icon('files'), compound=tk.LEFT,
                                   command=self.archive)
        self.file_menu.add_command(label='Import',
                                   image=icon('ins'),compound=tk.LEFT,
                                   command=self.import_bubbl)
        self.file_menu.add_command(label='Deploy',
                                   image=icon('fileexec'), compound=tk.LEFT,
                                   command=self.deploy)
        self.file_menu.add_command(label='Exit without saving',
                                   image=icon('exit'), compound=tk.LEFT,
                                   command=self.exit_without_saving)
        self.file_menu.add_command(label='Exit',
                                   image=icon('exit'), compound=tk.LEFT,
                                   command=self.save_and_exit)
        # Milestone, Restore
        #
        self.edit_menu = tk.Menu(menubar)
        menubar.add_cascade(menu=self.edit_menu, label='Edit')
        self.edit_menu.add_command(label='Undo',
                                   image=icon('undo'), compound=tk.LEFT,
                                   command=self.undo)
        self.edit_menu.add_command(label='Cut',
                                   image=icon('cut'), compound=tk.LEFT,
                                   command=self.cut)
        self.edit_menu.add_command(label='Copy',
                                   image=icon('copy'), compound=tk.LEFT,
                                   command=self.copy)
        self.edit_menu.add_command(label='Paste',
                                   image=icon('paste'), compound=tk.LEFT,
                                   command=self.paste)
        self.edit_menu.add_command(label='Delete',
                                   image=icon('del'), compound=tk.LEFT,
                                   command=self.delete)
        self.edit_menu.add_command(label='Search/Replace',
                                   image=icon('find'), compound=tk.LEFT,
                                   command=self.find)
        self.edit_menu.add_command(label='Edit Configuration',
                                   image=icon('settings'), compound=tk.LEFT,
                                   command=self.edit_config)
        # Configuration

        self.block_menu = tk.Menu(menubar)
        menubar.add_cascade(menu=self.block_menu, label='Block')
        # self.block_menu.add_command(label='Edit block',image=icon('edit'),compound=tk.LEFT,command=self.open_editor,self))
        self.block_menu.add_command(
            label='Edit block', image=icon('edit'), compound=tk.LEFT,
            command=self.open_editor)
        self.block_menu.add_command(
            label='New block', image=icon('create'), compound=tk.LEFT,
            command=self.new_diag)

        self.block_menu.add_command(
            label='Rename block', image=icon('pencil'), compound=tk.LEFT,
            command=self.rename_diag)
        self.block_menu.add_command(
            label='Delete block', image=icon('delete'), compound=tk.LEFT,
            command=self.delete_diag)

        # Rename, Delete, Clone
        self.view_menu = tk.Menu(menubar)
        menubar.add_cascade(menu=self.view_menu, label='View')
        self.view_menu.add_command(
            label='Cascade editor windows', image=icon('cascade'),
            compound=tk.LEFT,
            command=self.cascade)
        self.view_menu.add_command(
            label='Close all editors', image=icon('del'), compound=tk.LEFT,
            command=self.close_editors)

        self.view_menu.add_command(
            label='Select editor window', image=icon('output'),
            compound=tk.LEFT, command=self.select_editor_window)

        self.view_menu.add_command(
            label="View print output (STDOUT)", image=icon('logs'),
            compound=tk.LEFT, command=self.view_stdout)

        self.view_menu.add_command(
            label='View run-time logs', image=icon('logs'), compound=tk.LEFT,
            command=self.view_runtime_logs)

        self.view_menu.add_command(
            label='View IDE logs', image=icon('logs'), compound=tk.LEFT,
            command=self.view_logs)

        # Tile,Cascade,Close_all,Select
        self.help_menu = tk.Menu(menubar)

        menubar.add_cascade(menu=self.help_menu, label='Help')

        self.help_menu.add_command(label='System',
                                   command=lambda:self.help('system'))
        self.help_menu.add_command(label='Credits',
                                   command=lambda:self.help('credits'))
        self.help_menu.add_command(label='Licensing',
                                   command=lambda:self.help('licensing'))
        self.help_menu.add_command(label='About',
                                   command=lambda:self.help('about'))
        #self.help_menu.add_command(label='func',command=lambda:func(self.mach.diags['main'].variables))

        self.desktop_window['menu'] = menubar
        self.desktop_window.columnconfigure(0, weight=1)
        self.desktop_window.rowconfigure(0, weight=1)

        self.bubbl_app = None
        self.console = None

        self.filename = ''

        self.load_config()

        self.restore_ide_state()
        self.desktop.canvas.bind('<Configure>', self.place_console, add=True)
        self.desktop.canvas.bind('<Configure>', self.place_minimised, add=True)
        self.console.bind('<Configure>', self.place_console)
        self.console.bind('<Configure>', self.place_minimised, add=True)
        self.update_console()
        self.place_console()
        self.backup_timer = ui.timer(self.backup)
        self.backed_up_text = None
        self.backup_timer.start(60000, repeat=True)
        self.find_settings = {'find': '', 'replace': None, 'whole': False,
                              'scope': 'All blocks', 'matches': 0,
                              'cased': True}
        self.finder = None
        self.pen_colour = '#009'
        self.shape_fill = ''
        self.pen_settings = {'width': '2', 'ends': 'Round', 'joins': 'Round'}
        self.python_exception_viewer=None

    def view_stdout(self):
        if self.stdout_viewer is None:
            x = ui.mx()
            y = ui.my()
            queue = deque(self.captured_stdout.getvalue().splitlines())
            self.stdout_viewer = TextViewer(queue, x=x, y=y,
                                         title='Output',
                                         closer=self.close_stdout_viewer)

    def close_stdout_viewer(self):
        self.captured_stdout.refresh('\n'.join(self.stdout_viewer.data))
        self.stdout_viewer = None

    def update_stdout_viewer(self, value):
        self.initial_stdout.write(value)
        if self.stdout_viewer is not None:
            self.desktop_window.after_idle(self.stdout_viewer.append,value)

    def update_ide_log_viewer(self, value):
        if self.debug_to_stdout:
            self.captured_stdout.write(value)
        if self.log_viewer is not None:
            self.desktop_window.after_idle(self.log_viewer.append, value)

    def view_runtime_logs(self):
        x=ui.mx()
        y=ui.my()

        self.runtime_log_viewer=TextViewer(self.mach.logger.queue,x=x,y=y,
                                   title='Runtime logs',
                                   closer=self.close_runtime_log_viewer)

    def view_logs(self):
        x = ui.mx()
        y = ui.my()
        queue=deque(self.ide_log.getvalue().splitlines())
        self.log_viewer = TextViewer(queue, x=x, y=y,
                                     title='IDE logs',
                                     closer=self.close_log_viewer)

    def close_log_viewer(self):
        self.ide_log.truncate(0)
        self.ide_log.write(self.log_viewer.contents())
        self.log_viewer=None

    def close_runtime_log_viewer(self):
        self.runtime_log_viewer=None

    def refresh_runtime_log(self):
        if self.runtime_log_viewer is not None:
            self.runtime_log_viewer.refresh_contents(self.mach.logger.queue)

    def help(self,key):
        if key=='system':
            text=bubblhelp.help_text('Version 3.0 alpha')
            with open('_tmp.html','w') as f:
                f.write(text)
            webbrowser.open('_tmp.html')
        elif key=='licensing':
            TextViewer('\n\n'.join(licensing_texts()).split('\n'),ui.mx(),ui.my())
        elif key=='about':
            TextViewer([f'BUBBL Version {version}',
                        'Copyright © 2006 Barnaby McCabe',
                        'email: oldbarney@hotmail.com'],
                       ui.mx(),ui.my())
        else:
            log('HELP',key,level=Logger.INFO)

    def line_ends(self):
        return self.pen_settings['ends'].lower()

    def line_width(self):
        try:
            return int(self.pen_settings['width'])
        except:
            return 1

    def line_joins(self):
        return {'Round': 'round',
                'Mitre': 'miter',
                'Bevel': 'bevel'}[self.pen_settings['joins']]

    def choose_pen_colour(self, canvas):
        result = colorchooser.askcolor(
            self.pen_colour,
            parent=canvas,
            title='Colour for graphics drawing')
        if result[0] is None:
            return
        self.pen_colour = result[1]

    def choose_shape_fill_colour(self, canvas):
        result = colorchooser.askcolor(
            self.pen_colour,
            parent=canvas,
            title='Fill for graphics shapes')
        if result[0] is None:
            return
        self.shape_fill = result[1]

    def choose_pen_settings(self, canvas):
        popup_line_settings(ui.mx(), ui.my(),
            lambda values,canvas=canvas:
                self.settings_edited(canvas,values),
            self.pen_settings)

    def settings_edited(self,canvas, values):
        canvas['cursor']='pencil'
        if values is None:
            return
        self.pen_settings.update(values)

    def edit_config(self):
        self.config_values = {
            'scale': render_defaults.size,
            'tkinterfiledialog': self.mach.config[('tkinterfiledialog',True)],
            'loglevel':log_level_map[self.mach.config[('loglevel',2)]],
            'ideloglevel':log_level_map[self.mach.config[('ideloglevel',2)]],
            'debugtostdout':self.config['debugtostdout']}
        popup_config_editor(ui.mx(), ui.my(), self.config_edited,
                            self.config_values)  # BUBBL

    def config_edited(self, values):
        if values is None:
            return
        #log('ABOUT TO REFRESH CONFIG-4')
        scale_view(values['scale'])
        #log('ABOUT TO REFRESH CONFIG-3')
        #print('EDITED CONFIG VALUES',values)
        self.config['tkinterfiledialog'] = values['tkinterfiledialog']
        level=get_log_level(values['loglevel'])
        idelevel=get_log_level(values['ideloglevel'])
        set_log_level(idelevel)
        self.ide_log.level=idelevel
        set_log_level(level,runtime=True)
        self.config['loglevel'] = level
        self.config['ideloglevel'] = idelevel
        self.mach.logger.level=level
        #log('ABOUT TO REFRESH CONFIG-2')
        self.mach.config['tkinterfiledialog']=values['tkinterfiledialog']
        self.mach.config['loglevel']=level
        self.mach.config['ideloglevel']=idelevel
        self.config['debugtostdout']=values['debugtostdout']
        self.debug_to_stdout=values['debugtostdout']
        #log('ABOUT TO REFRESH CONFIG-1')
        #print('loglevel set to ',level)
        set_log_level(level,runtime=True)
        self.get_current_editor().redraw(do_all=True)

    def import_bubbl(self):
        Importer(self,home)

    def imported(self,init):
        self.edvm.do_import(init)

    def handle_python_syntax_error(self,message,diag_name,node_no,line_no,col_no):
        #print('Handling python syntax error',message,diag_name,node_no,line_no,col_no)

        self.console.do_tell_machine('edit')
        self.select_editor_for_editing(diag_name)

        if diag_name == 'main':
            ed = self.desktop
        else:
            ed = self.diag_editors[diag_name]

        def edit(choice):
            if choice!=0:
                return
            pres=ed.presenters[node_no]
            pres.edit(ui.mx(), ui.my(), on_top=True, line_no=line_no, col_no=col_no)

        PopupChoice(ed.window,
                    None,
                    None,
                    ['Edit block','Ignore'],
                     title=f'Python syntax error:{message}',
                                        client_handler=edit)

    def handle_python_block_exception(self,
                                      diag_name,
                                      node_no,
                                      python_exception):
        error,stacked=unscrambled_exception(python_exception,diag_name,node_no)
        #print('ERROR',error)
        #for (key,lines,ln,cn,cl) in stacked:
        #    print('KEY:',key)
        #    print('lines------------')
        #    print(lines)
        #    print('endlines----------')
        #    print(f'Line:{ln} Col:{cn} length:{cl}')
        #    print("======================")

        def callback(index):
            key, lines, ln, cn, cl=stacked[index]
            if key in ('_BLOCK_','_UBLOCK_',
                              '_AUX_BLOCK_',
                              '_UAUX_BLOCK_'):
                self.console.do_tell_machine('edit')
                if diag_name == 'main':
                    pres = self.desktop.presenters[node_no]
                else:
                    pres = self.diag_editors[diag_name].presenters[node_no]
                self.select_editor_for_editing(diag_name)
                pres.edit(ui.mx(), ui.my(),on_top=True,line_no=ln,col_no=cn)
            else:
                def end_edit(result):
                    if result:
                        pass

                #for p in sys.path:
                #    if key.startswith(p):
                #        ro=True
                #        break
                #else:
                #    ro=False
                if any (key.startswith(prefix) for prefix in
                        ('bubblib/',
                         'bubblib'+os.sep,
                         'bubblidelib/',
                         'bubblidelib'+os.sep)
                        ):
                    key='source'+os.sep+key
                    if not os.path.isfile(key):
                        messagebox.showinfo('Sorry!','BUBBL source code not available')
                        return
                PythonEditor(self.desktop_window,
                             end_edit,
                             filename=key,
                             index=f'{ln}.{cn}',
                             read_only=True)

            #print(stacked[index][0])

        if self.python_exception_viewer is not None:
            self.python_exception_viewer.close_window()

        def closer():
            self.python_exception_viewer=None
        self.python_exception_viewer=viewer=PythonExceptionViewer(
                callback,
                error,
                closer=closer)
        for (key,lines,ln,cn,cl) in stacked:
            lines=lines.split('\n')
            #print('about to add lines')
            if key in ('_BLOCK_','_UBLOCK_',
                              '_AUX_BLOCK_',
                              '_UAUX_BLOCK_'):
                viewer.add_line(f'Diag:{diag_name} block:{node_no} line:{ln}',0,100)
            else:
                viewer.add_line(lines[0],lines[0].index(key),len(key))
            for line in lines[1:]:
                viewer.add_line(line)
            viewer.add_line('')


        #for frame in summary_frames:
        #    text=repr(frame).split('\n')
        #    viewer.add_line(text[0],0,len(text))
        #    for line in text[1:]:
        #        viewer.add_line(line)

    def find(self):
        log('FINDING')
        if self.finder is None:
            self.finder = Finder(ui.mx(), ui.my(), self, self.find_settings)

    def found(self, diag_name, finds, settings):
        #print('BUBBLIDE found',diag_name,finds,settings)

        if finds is None:
            self.desktop.highlight_finds(None, None)
            for ed in self.diag_editors.values():
                ed.highlight_finds(None, None)
            self.finder=None
            return
        self.settings = dict(settings)
        finds = finds[diag_name]
        if diag_name == 'main':
            self.desktop.highlight_finds(finds, self.settings)
        else:
            self.select_or_open_editor(diag_name, 200, 200)
            self.diag_editors[diag_name].highlight_finds(finds, self.settings)

    def archive(self):
        if not self.filename:
            self.save_as()
            return
        fn=self.filename+'.zip'
        if os.path.isfile(fn):
            zf=zipfile.ZipFile(fn,"a")
        else:
            zf=zipfile.ZipFile(fn,"w")
        arcname=self.filename.replace('\\','/').split('/')[-1]+'_'+now()
        self.save()
        zf.write(self.filename,
                 compress_type=zipfile.ZIP_DEFLATED,
                 arcname=arcname)
        zf.close()

    def backup_filename(self):
        return self.filename + '.bak0'

    def backup_backup_filename(self):
        return self.filename + '.bak1'

    def backup(self):
        # log('checking backup')
        if not self.filename:
            return
        text = self.program_text(python=self.filename.endswith('.py'))
        if self.backed_up_text == text:
            return True
        log('backing up')
        errors = []

        if os.path.isfile(self.backup_backup_filename()):
            if os.path.isfile(self.backup_filename()):
                try:
                    os.remove(self.backup_backup_filename())
                except Exception as e:
                    errors.append((f'Failed to remove backup' +
                                   f'{self.backup_backup_filename()}:{e}'))
        try:
            os.rename(self.backup_filename(), self.backup_backup_filename())
        except Exception as e:
            errors.append((f'Failed to rename '
                           + self.backup_filename() + ' to '
                           + f'{self.backup_backup_filename()}:{e}'))

        try:
            self.write_text_to_file(text, self.backup_filename())
            self.backed_up_text = text
            try:
                os.remove(self.backup_backup_filename())
            except:
                pass
        except Exception as e:
            errors.append(f'Failed to backup to {self.backup_filename()}: {e}')
            messagebox.showerror('Backup', '\n'.join(errors),
                                 parent=self.desktop.canvas)

    def cascade(self):
        x = 150
        y = 100
        for ed in self.stacking_order:
            log('cascading', ed)
            self.diag_editors[ed].window._norm_geom = (x, y, 640, 480)
            x += 50
            y += 30
            self.diag_editors[ed].window.unminimise(reposition=True)

    def close_editors(self):
        for ed in reversed(self.stacking_order):
            self.delete_editor(ed, do_reselect=False)
        self.select_editor_for_editing('main')

    def select_editor_window(self):
        # log(f'Popup select_editor_window')
        choices = list(self.diag_editors)
        colours = [self.mach.diags[diag].params[0] for diag in choices]
        self.diag_chooser = PopupChoice(
            self.desktop_window, None, None, choices, colours=colours, title='',
            client_handler=lambda index, choices=choices:
            self.open_diag_editor_by_choice(index, choices))

    def get_current_editor(self):
        if self.desktop.current:
            return self.desktop
        for ed in self.diag_editors.values():
            if ed.current:
                # log('current editor is',ed.diag.name)
                return ed
        else:
            return None

    def deploy(self):#/Single app
        def callback(result):
            #log('deploycalledback', f'>{result}<')
            if result is None:
                return

            log(f'Deploying {self.filename} to {result}')
            if (sys.path[0].endswith(os.sep+'bubblib.zip')
                  and os.path.isfile(sys.path[0])):
                shutil.copy(sys.path[0],result)
            elif (sys.path[2].endswith(os.sep+'bubblib')
                    and os.path.isdir(sys.path[2])):
                with zipfile.PyZipFile(result + 'bubblib.zip', mode='w',
                                   compression=zipfile.ZIP_STORED) as zipped:
                    zipped.writepy(sys.path[2])
            else:
                messagebox.showerror('Deployment failed',
                                     f'Unable to copy BUBBL library to {result}.',
                                     parent=self.desktop.canvas)
                return

            text = self.program_text(python=True)
            filename=self.filename.split(os.sep)[-1]
            if filename.endswith('pbub'):
                filename=f'{filename[:-4]}py'

            try:
                self.write_text_to_file(text, result+filename)
                messagebox.showinfo('Deployment',f'Successfully deployed app to\n{result+filename}')
            except Exception as e:
                messagebox.showerror('Save',
                                     f'Failed to save {filename} {e}',
                                     parent=self.desktop.canvas)

        get_file_dialog(default=self.filename,
                        callback=callback,
                        saveas=True,
                        directory=True,
                        use_tkinter=self.config['tkinterfiledialog'])

    def undo(self):
        ed = self.get_current_editor()
        if ed is not None:
            ed.undo()

    def cut(self):
        log('cut')
        ed = self.get_current_editor()
        if ed is not None:
            ed.cut()

    def copy(self):
        ed = self.get_current_editor()
        if ed is not None:
            ed.copy()

    def paste(self):
        ed = self.get_current_editor()
        if ed is not None:
            ed.paste()

    def delete(self):
        ed = self.get_current_editor()
        if ed is not None:
            ed.delete()

    def replace_console(self):
        if self.console is not None:
            self.desktop.canvas.delete('console')
            self.console.tell_machine.disconnect(self.console_action)
            del self.console
        self.console = Console(self.desktop_window)
        self.console.tell_machine.connect(self.console_action)
        self.desktop.add_widget_to_canvas(self.console, 0, 0,'console')
        self.desktop.canvas.bind('<Configure>', self.place_console, add=True)
        self.console.bind('<Configure>', self.place_console)
        self.update_console()
        # ui.root.after(20,self.place_console)

    def machine_state_changed(self):
        # log('IDE machine_state_changed')
        #ui.root.after_idle(self.safe_machine_state_changed)
        self.safe_machine_state_changed()
        self.handle_runtime_error()

    def update_console(self):
        # log('updating console')
        # log(['main']+self.stacking_order)
        if self.console is not None:
            self.console.cache_editor_list(self.stacking_order)

    def is_stacked(self, diag):  # Must not be called if machine not stopped
        s = list(self.mach.stack)
        for (d, n) in s:
            if d == diag:
                return True
        return False

    def safe_machine_state_changed(self):
        # log('SAFE MACHINE STATE CHANGED')
        self.mach_state = state = self.mach.state
        if state==ExState.stopped_on_node:
            log(f'STOPPED ON NODE diag:{self.mach.diag.name} node:{self.mach.node}')
        elif state==ExState.stopped_on_link:
            log(f'STOPPED ON LINK diag:{self.mach.diag.name} node:{self.mach.last_node} link:{self.mach.link}')

        for e in self.diag_editors.values():
            e.set_visible_state()

        self.desktop.set_visible_state()

        if self.mach_state in (ExState.stopped_on_node,
                               ExState.stopped_on_link,
                               ExState.quiescent):
            self.mach.event_queue.clear()
            call_stack = []
            for (diag, _node) in reversed(self.mach.stack):
                call_stack.append((diag.name, diag.sig["params"][0]))
        else:
            call_stack = None
        self.console.update_buttons(state, call_stack)

        if state in (ExState.quiescent,
                     ExState.active):
            return

        if state == ExState.stopped_on_node:
            diag_name = self.mach.diag.name
            if diag_name != 'main':
                if diag_name not in self.diag_editors:
                    self.get_new_diag_editor(
                        diag_name, 120, 120, 640, 480,
                        initial_state=DiagEditorState.activated)
                    self.diag_editors[diag_name].set_visible_state()
                self.move_editor_to_top(self.diag_editors[diag_name])

        elif state in (ExState.stopped_on_link,
                       ExState.exited):
            diag_name = self.mach.diag.name

            if diag_name == 'main':
                self.desktop.set_visible_state()
                return
            if diag_name not in self.diag_editors:
                self.get_new_diag_editor(
                    diag_name, 120, 120, 640, 480,
                    initial_state=DiagEditorState.activated)
                self.diag_editors[diag_name].set_visible_state()
            self.move_editor_to_top(self.diag_editors[diag_name])

    def exit(self):
        ui.root.after_idle(BlockEditor.close_all)
        log('all block editors closed')
        if self.ok_check_saved():
            self.save_config()
            self.do_exit()

    def save_and_exit(self):
        ui.root.after_idle(BlockEditor.close_all)
        self.save()
        self.save_config()
        self.do_exit()

    def close_machine(self):
        for e in list(self.diag_editors):
            self.delete_editor(e, do_reselect=False)

        if self.finder is not None:
            self.finder.kill()

        self.mach.close_all_pages()
        self.mach.cleanup_dialog()
        self.mach.command('kill')
        self.mach.app.sys_mach.command('kill')

    def do_exit(self):
        log('Program exiting')
        self.close_machine()
        log('IDE indicated it is exiting')
        if os.path.isfile(self.backup_filename()):
            ltime = os.path.getmtime(self.filename)
            os.utime(self.backup_filename(), (ltime, ltime))
        ui.root.after_idle(ui.close)
        #self.exited.set()

    # @Slot(ExecutionState)
    def console_action(self, *action):
        # if action=='edit':
        #   self.
        if action[0] in ('run', 'undoablerun', 'step', 'back',
                         'back_to_breakpoint'):
            if self.desktop.current:
                self.desktop.visible_state = DiagEditorState.restricted_editing
            else:
                for editor in self.diag_editors.values():
                    if editor.current:
                        editor.visible_state = DiagEditorState.restricted_editing
                        break
                        # editor.deactivate_text_editor()
                        # editor.deactivate_flasher()
        self.mach.command(*action)

    def place_console(self, *_args):
        try:
            x = self.desktop.canvas.winfo_width() - self.console.winfo_width()
            y = self.desktop.canvas.winfo_height() - self.console.winfo_height()
            self.desktop.canvas.moveto('console', x, y)
            self.desktop.canvas.tag_raise('console')
        except:
            log('console not identified yet')

    def place_minimised(self, event):
        minimised = [name for name in self.diag_editors
                     if self.diag_editors[name].window.minimised]
        self.minimised_editors.update_state(minimised)
        y = (self.desktop.canvas.winfo_height() -
             self.minimised_editors.winfo_height())
        self.desktop.canvas.moveto('minimised', 0, y)

    def view_license(self):
        tk.messagebox.showinfo("Licensing/Acknowledgements",
                               acknowledgement_text,
                               parent=self.desktop.canvas)

    def load_config(self):
        self.config = _config
        table=Table('history',['key','value'])
        for k,v in _config['history']:
            table.insert_row(-1,[k,v])
        self.history=HistoryTable(table)
        self.debug_to_stdout=self.config['debugtostdout']

    def restore_ide_state(self):
        log('restoring ide state')
        # log(self.config)
        if self.config['recent']:
            self.load_file(self.config['recent'][0], replace_console=True)
        if self.bubbl_app is None:
            self.new_app()
        self.select_editor_for_editing('main')
        set_log_level(self.config['ideloglevel'])
        set_log_level(self.config['loglevel'],runtime=True)

    def save_config(self):
        if self.filename != '':
            log('saving config', self.filename)
            if not 'state_map' in self.config:
                self.config['state_map'] = {}
            machs_config = {}
            for mach_name in self.bubbl_app.machs:
                # log('processing', mach_name)
                # mach = self.bubbl_app.machs[mach_name]
                if mach_name!='main':
                    continue

                machs_config[mach_name] = {'editors':
                                               [[name, self.diag_editors[
                                                   name].get_window_details()]
                                                for name in self.stacking_order]
                                           }
                self.config['state_map'][self.filename.replace('\\','/')] = machs_config
                self.config['history']=[row.get_list() for row in self.history.table]

        try:
            with open(_config_file, 'w') as f:
                f.write(toJSON(self.config))
        except Exception as e:
            log(f'failed to save config {e}',level=Logger.INFO)

    def load(self):
        if not self.ok_check_saved():
            return

        def callback(result):
            if result is None:
                return
            self.load_file(result, replace_console=True)
            log('file result is ', result)

        log('IDE CONFIG IS', list(self.config))

        get_file_dialog(default=self.filename,
                        callback=callback,
                        history=self.config['recent'],
                        filter='Bubbl Python programs:*.py,Bubbl programs:*.pbub',
                        use_tkinter=self.config['tkinterfiledialog'])

    def load_file(self, filename, replace_console=False):
        # log('loading file')
        filename = os.path.abspath(filename)
        back0 = filename + '.bak0'
        back1 = filename + '.bak1'

        wk_filename = filename
        if os.path.isfile(filename):
            if os.path.isfile(back0):
                if os.path.getmtime(filename) < os.path.getmtime(back0):
                    result = messagebox.askyesnocancel(
                        message=f'''Program exited without saving
Restore from backup?''',
                        title='Exited without saving',
                        icon='question', parent=self.desktop_window)
                    if result is True:
                        wk_filename = back0
            elif os.path.isfile(back1):
                if os.path.getmtime(filename) < os.path.getmtime(back1):
                    result = messagebox.askyesnocancel(
                        message=f'''Program exited without saving
Restore from backup?''',
                        title='Exited without saving',
                        icon='question', parent=self.desktop_window)
                    if result is True:
                        wk_filename = back1
        else:
            if os.path.isfile(back0):
                wk_filename = back0
            elif os.path.isfile(back1):
                wk_filename = back1
            else:
                return
        try:
            init = BaseBUBBLApp.get_pbub_from_file(wk_filename)
            # with open(wk_filename, 'r') as f:
            #    data = f.read()
            # init = get_pbub(data)
            if self.bubbl_app is not None:  # todo check if app is 'new'
                self.close_machine()
        except Exception as e:
            log(f'Failed to load {filename}:{e}',level=Logger.INFO)
            return
        if wk_filename != filename:
            try:
                shutil.copy(wk_filename, filename)
                os.remove(wk_filename)
            except Exception as e:
                messagebox.showerror('Restore source file',
                                     f'Failed to save to {filename}: {e}',
                                     parent=self.desktop.canvas)
        self.filename = filename

        log('loaded', filename)
        if filename in self.config['recent']:
            self.config['recent'].remove(filename)
        self.config['recent'].insert(0, filename)
        if filename in self.config['state_map']:
            mach_cfgs = self.config['state_map'][filename]
            self.load_app(init, mach_cfgs=mach_cfgs,
                          create_new_console=replace_console)
        else:
            self.load_app(init, create_new_console=replace_console)
        self.update_console()

    def ok_check_saved(self):
        # Return True if
        if self.bubbl_app is None:
            return True
        sapp = toJSON(self.bubbl_app.get_init())
        self.save_config()

        if sapp == self.initial_init:
            return True
        result = messagebox.askyesnocancel(
            message=f'Save changes to {self.filename}',
            title='Program exit',
            icon='question',
            parent=self.desktop_window)
        if result is None:
            return False
        if result:
            return self.ok_saved()
        return True

    def load_app(self, init, mach_cfgs=None, create_new_console=False):
        if mach_cfgs is None:
            mach_cfgs = {'main': {'editors': []}}
        # log(f'Loading app from', init)

        try:
            self.bubbl_app = BUBBLApp(self,init, filename=self.filename)
        except Exception as e:
            log(f'Failed to load app:{e}',level=Logger.INFO)
            self.bubbl_app = BUBBLApp(self,newAppInit, filename=None)
            mach_cfgs = {'main': {'editors': []}}
            create_new_console = True
        self.desktop_window.title(f'BUBBL On Python V{version}    File:{self.filename}')

        try:
            self.initial_init = toJSON(self.bubbl_app.get_init())
        except Exception as e:
            print_('CANNOT GET INITIAL INIT from ',self.bubbl_app.get_init())

        for mach_name in mach_cfgs:
            editors = mach_cfgs[mach_name]['editors']
            # log('editors is', editors)

            if mach_name == 'main':
                self.mach = self.bubbl_app.machs['main']
                self.edvm = DiagEdVM(self)
                self.mach.machine_state_changed.connect(
                    self.machine_state_changed
                )
                self.mach.runtime_error_handler = self.handle_runtime_error
                #print('MAKING NEW DESKTOP')
                self.desktop = BubblDiagEditor(self, self.desktop_window,
                                               self.mach.diags['main'], 800,
                                               600)
                self.replace_console()
                self.minimised_editors = Minimised(self.desktop_window,
                                                   self.unminimise_editor)
                self.desktop.add_widget_to_canvas(
                    self.minimised_editors, 0, 0,'minimised')
                for [diag_name, geom] in editors:
                    try:
                        if geom[3] < 0:  # minimised
                            geom[3] = -geom[3]
                            minimised = True
                        else:
                            minimised = False
                        geom = tuple(geom)
                        self.get_new_diag_editor(diag_name, *geom)
                        if minimised:
                            self.minimise_editor(diag_name)
                            self.diag_editors[diag_name].window._norm_geom = \
                                tuple(geom)
                            self.place_minimised(None)
                    except Exception as e:
                        log('unable to create new diag editor', e,
                            level=Logger.INFO)
                        try:
                            self.get_new_diag_editor(diag_name, 30, 30, 640,
                                                     480)
                        except Exception as e:
                            log(f'Unable to create editor {diag_name}', e,
                                  level=Logger.INFO)

                self.select_editor_for_editing('main')
                if create_new_console:
                    self.replace_console()
                #log('Checking structure')
                for diag in self.mach.diags.values():
                    self.edvm.update_calls_to_diag(diag)
                #log('Checked')
        self.place_minimised(None)
        self.place_console()
        # todo here add multi machine interface

    def add_machine(self, name, init):
        pass

    def diag_name_changed(self,old_name,new_name):
        self.update_diag_name_change(old_name,new_name)
        self.refresh_factory()

    def diag_deleted(self,name):
        try:
            self.delete_editor(name)
        except:
            pass
        self.refresh_factory()


    def select_machine(self, mach_name, editors):
        if self.desktop is not None:
            self.close_machine()

        self.mach = self.bubbl_app.machs[mach_name]
        self.edvm = DiagEdVM(self)
        self.mach.machine_state_changed.connect(
            self.machine_state_changed
        )
        self.desktop = BubblDiagEditor(self, self.desktop_window,
                                       self.mach.diags['main'], 800, 600)
        self.replace_console()
        self.minimised_editors = Minimised(self.desktop_window,
                                           self.unminimise_editor)
        self.desktop.add_widget_to_canvas(self.minimised_editors, 0, 0)
        for [diag_name, geom] in editors:
            try:
                if geom[3] < 0:  # minimised
                    geom[3] = -geom[3]
                    minimised = True
                else:
                    minimised = False
                geom = tuple(geom)
                self.get_new_diag_editor(diag_name, *geom)
                if minimised:
                    self.minimise_editor(diag_name)
                    self.diag_editors[diag_name].window._norm_geom = tuple(geom)
                    self.place_minimised(None)
            except Exception as e:
                log('unable to create new diag editor', e,
                      level=Logger.INFO)
                try:
                    self.get_new_diag_editor(diag_name, 30, 30, 640, 480)
                except Exception as e:
                    log(f'Unable to create editor {diag_name}', e,
                          level=Logger.INFO)

        self.select_editor_for_editing('main')
        self.replace_console()
        log('Checking structure')
        for diag in self.mach.diags.values():
            self.edvm.update_calls_to_diag(diag)
        log('Checked')
        self.place_minimised(None)
        self.place_console()

    def program_text(self, python=False):
        text = toJSON(self.bubbl_app.get_init())
        if python:
            return (app_string(text))
        return text

    def write_text_to_file(self, text, filename):
        with open(filename, 'w') as f:
            f.write(text)

    def ok_saved(self):
        python = self.filename.endswith('.py')
        text = self.program_text(python=python)
        try:
            log('ok_saved running')
            self.write_text_to_file(text, self.filename)
            self.initial_init = text
            self.desktop_window.title(f'BUBBL On Python V{version}     File:{self.filename}')
            self.bubbl_app.machs['main'].save_data_to_db()
            try:
                os.remove(self.backup_backup_filename())
            except:
                pass
            try:
                os.remove(self.backup_filename())
            except:
               pass
            return True
        except Exception as e:
            messagebox.showerror('Save', f'Failed to save {self.filename} {e}',
                                 parent=self.desktop.canvas)
            return False

    def save(self):
        if not self.filename:
            self.save_as()
        else:
            self.ok_saved()
        return 'break'

    def save_as(self):
        # dial = filedialog.SaveFileDialog(self.desktop_window)
        # filename = filedialog.asksaveasfilename()

        def callback(result):
            log('saveascalledback', f'>{result}<')
            if result is None:
                return
            if os.path.isfile(result):
                log('CHECKING O/W')

                def callback(result):
                    if result == 'Ok':
                        log('SAVING')
                        self.filename = f.name
                        self.ok_saved()

                AskUserDialog(callback, ui.mx(), ui.my(),
                              'File exists, overwrite?', [])
                return
            log('SAVING')
            self.filename = result
            try:
                self.config['recent'].remove(result)
            except:
                pass
            self.config['recent'].insert(0,self.filename)
            self.ok_saved()

        get_file_dialog(default=self.filename,
                        callback=callback,
                        saveas=True,
                        history=self.config['recent'],
                        filter='Bubbl Python programs:*.py,Bubbl programs:*.pbub',
                        use_tkinter=self.config['tkinterfiledialog'])
        return 'break'

    def snapshot(self):
        log('snapshot')

    def restore(self):
        log('restore')

    def recent(self):
        log('RECENT')
        recent_files = list(self.config['recent'])
        PopupChoice(self.desktop_window,
                    None, None,
                    recent_files,
                    title='',
                    client_handler=lambda index,
                                          choices=recent_files: self.load_recent(
                        index, choices))

    def load_recent(self, index, choices):
        if index is None:
            return
        if self.ok_check_saved():
            self.load_file(choices[index], replace_console=True)

    def exit_without_saving(self):
        log('exit without saving')
        if messagebox.askyesnocancel(title='Exit without saving',
                                     message='Are you sure ?',
                                     icon='question',
                                     parent=self.desktop_window):
            self.do_exit()

    def new_app(self):
        log('new app')
        if self.filename:
            if not self.ok_check_saved():
                return
        self.filename=''
        self.load_app(newAppInit, create_new_console=True)
        self.update_console()

    def delete_diag(self):
        mach = self.bubbl_app.machs["main"]
        choices = [diag_name for diag_name in mach.diags if diag_name != 'main']
        colours = [mach.diags[name].params[0] for name in choices]

        def do_delete(index):
            if index is None:
                return
            to_del = choices[index]
            if to_del in self.diag_editors:
                messagebox.showerror(
                    f'{to_del} editor is open',
                    f'Editor must be closed before {to_del} can be deleted')
                return
            nref = 0
            for diag in mach.diags.values():
                for node in diag.nodes.values():
                    if node.type_name == 'CALL' and node.params[0] == to_del:
                        nref += 1
            if nref > 0:
                messagebox.showerror(
                    'Block in use',
                    f"Cannot delete '{to_del}' as it is used in " +
                    ("another block." if nref == 1 else "other blocks.") +
                    '\nAll references to it must be deleted before it can '
                    'itself be deleted.',
                    parent=self.desktop.canvas)
                return
            self.edvm.mark()
            self.edvm.delete_diag(to_del, True)

        self.diag_chooser = PopupChoice(self.desktop_window,
                                        None, None, choices,
                                        colours=colours, title='',
                                        client_handler=do_delete)

    def rename_diag(self):
        mach = self.bubbl_app.machs["main"]
        choices = [diag_name for diag_name in mach.diags if diag_name != 'main']
        colours = [mach.diags[name].params[0] for name in choices]

        def choose_block_to_rename(index):
            if index is None:
                return
            old_name = choices[index]

            def do_rename(command, index):
                self.box.close_window()
                if command == 'ok':
                    new_name = self.new_diag_name.get()
                    if new_name in choices:
                        messagebox.showerror('Renaming block',
                                             new_name + ' already exists',
                                             parent=self.desktop.canvas)
                        return
                    if (not new_name.replace('_', '').isalnum()
                            or new_name[0] in '0123456789'):
                        messagebox.showerror('Renaming block',
                                             'Diag name must only contain'
                                             ' letters, digits and'
                                             ' underscores and must not start with'
                                             'a digit.',
                                             parent=self.desktop.canvas)
                        return
                    self.do_rename_diag(old_name, new_name)

            self.new_diag_name = tk.StringVar(value=old_name)
            self.box = InputBox(
                self.desktop_window, ui.mx(), ui.my(),
                {'title': 'New block name', 'style': '',
                 'rows': [
                     [{'type': 'label', 'text': 'New name'},
                      {'type': 'input', 'weight':1,'var': self.new_diag_name,
                       'contexts': []}
                      ]
                 ]
                 },
                do_rename,
                tkinter_file_dialog=self.config['tkinterfiledialog'],
                history=self.history
            )
            #self.box.main_frame.bind('<<inputboxbutton>>', do_rename)

        self.diag_chooser = PopupChoice(self.desktop_window,
                                        None, None, choices,
                                        colours=colours, title='',
                                        client_handler=choose_block_to_rename)

    def do_rename_diag(self, old_name, new_name):
        self.edvm.mark()
        self.edvm.rename_diag(self.mach.diags[old_name], new_name, True)

    def update_diag_name_change(self, old_name, new_name):
        if old_name in self.diag_editors:
            self.diag_editors[new_name] = self.diag_editors.pop(old_name)
            self.diag_editors[new_name].window.title['text'] = new_name
            if old_name in self.stacking_order:
                self.stacking_order[
                    self.stacking_order.index(old_name)] = new_name
        self.desktop.redraw_calls(new_name)
        for ed in self.diag_editors.values():
            ed.redraw_calls(new_name)

    def refresh_factory(self):
        self.get_current_editor().factory.refresh()

    def new_diag(self):
        log(f'Popup new_diag @ {"where"}')

        self.new_diag_name = tk.StringVar(value='')

        self.box = InputBox(self.desktop_window, 200, 200,
                            {'title': 'New block name', 'style': '',
                             'rows': [[{'type': 'label',
                                        'text': 'New name'},
                                       {'type': 'input',
                                        'weight':1,
                                        'var': self.new_diag_name,
                                        'contexts': []}]
                                      ]
                             },
                            self.create_new_diag,
                            tkinter_file_dialog=self.config[
                                'tkinterfiledialog'],
                            history=self.history)

    def create_new_diag(self,command, index):
        if command in ('esc', 'ok'):
            self.box.win.destroy()

        log('button pressed is ', command, index)
        if command != 'ok':
            return
        ndname = self.new_diag_name.get()
        if ndname == '':
            return
        log('new diag name =' + ndname)

        mach = self.bubbl_app.machs["main"]
        if ndname in mach.diags:
            messagebox.showerror('Create new block',
                                 f'{ndname} already exists!',
                                 parent=self.desktop.canvas)
            return
        if (not ndname.replace('_', '').isalnum()
                or ndname[0] in '0123456789'):
            messagebox.showerror('Create new block',
                                 'Diag name must only contain'
                                 ' letters, digits and'
                                 ' underscores and must not start with'
                                 'a digit.',
                                 parent=self.desktop.canvas)
            return

        mach.diags[ndname] = BubblDiag(mach, ndname)
        self.get_new_diag_editor(ndname, 150, 150, 800, 600)
        self.select_editor_for_editing(ndname)

    def handle_runtime_error(self):
        error = self.mach.runtime_exception
        if error is None:
            return
        self.mach.runtime_exception = None
        def callback(action,error=error):
            #print('RUNTIME ERROR CALLBACK',action)
            if action == 'edinst':
                self.console.do_tell_machine('edit')
                if error.diag == 'main':
                    pres = self.desktop.presenters[error.node]
                else:
                    pres = self.diag_editors[error.diag].presenters[error.node]
                self.select_editor_for_editing(error.diag)
                pres.edit(ui.mx(), ui.my(),on_top=True)

        RuntimeErrorDialog(str(error),callback)

    def get_new_diag_editor(self, name, x, y, width, height,
                            initial_state=DiagEditorState.disabled,
                            contents=None):
        window = EditorWindow(self.desktop.canvas, name,
                              client_handler=self.editor_handler)
        # window.canvas=self.desktop.canvas
        editor = BubblDiagEditor(self, window, self.mach.diags[name], width,
                                 height,
                                 initial_state=initial_state, contents=contents)
        # log('editor made has geom',editor.get_window_details())
        cid = self.desktop.canvas.create_window(x, y,
                                                window=window.frame,
                                                anchor='nw')
        editor.window.uid = cid
        # log('New Editor Window Client is',window.client_canvas())

        # log('editor coords on desktop canvas is',
        # self.desktop.canvas.coords(cid))
        self.diag_editors[name] = editor
        self.stacking_order.append(name)
        if initial_state == DiagEditorState.editing:
            self.select_editor_for_editing(name)

            # self.desktop.deselect()
            # for name in self.stacking_order[:-1]:
            #    self.diag_editors[name].deselect()
            # editor.select()
        self.update_console()

    def select_or_open_editor(self, name, x, y):
        if name != 'main' and name not in self.diag_editors:
            self.get_new_diag_editor(name, x, y, 800, 600,
                                     initial_state=DiagEditorState.editing)
        else:
            self.select_editor_for_editing(name)

    def select_editor_for_editing(self, name):
        # if self.mach_state!=ExecutionState.quiescent:
        #    if not messagebox.askyesnocancel(
        #            title='Program running',
        #            message='Do want to stop the program ?',
        #            icon='question', parent=self.desktop_window):
        #        return
        #    self.console.tell_machine.emit('edit')
        if name == 'main':
            for ed in self.diag_editors.values():
                #print('DESELECTING TO SELECT DESKTOP')
                ed.deselect()
            self.desktop.select()

            self.mach.current_editor = self.desktop
            return
        self.desktop.deselect()

        if self.stacking_order[-1:] != [name]:
            try:
                self.move_editor_to_top(self.diag_editors[name])
            except KeyError:
                pass
        for edn in self.stacking_order[:-1]:
            #print('DESELECTING TO SELECT',name)
            self.diag_editors[edn].deselect()
        self.diag_editors[name].select()
        self.mach.current_editor = self.diag_editors[name]

    def open_editor(self):
        log(f'Popup open_editor @ {"where"}')
        mach = self.bubbl_app.machs["main"]
        choices = [diag_name for diag_name in mach.diags]
        colours = [diag.params[0] for diag in mach.diags.values()]
        self.diag_chooser = PopupChoice(
            self.desktop_window, None, None,
            choices, colours=colours, title='',
            client_handler=lambda index,
            choices=choices: self.open_diag_editor_by_choice(
            index, choices))
        # ed=c.choice()

    def open_diag_editor_by_choice(self, index, diag_names):
        """
        log('button text is ',button_text)
        if button_text!='Ok':
            return
        dname=self.open_editor_name.get()
        """
        self.diag_chooser = None
        if index is None:
            return
        diag_name = diag_names[index]
        if diag_name == 'main':
            self.select_editor_for_editing('main')
            return
        if diag_name not in self.diag_editors:
            self.get_new_diag_editor(diag_name, 120, 120, 640, 480,
                                     initial_state=DiagEditorState.editing)
        self.select_editor_for_editing(diag_name)

    def check_editor_is_open(self):
        # log('bubblidelib checking editor is open')
        if self.mach.state in (ExState.stopped_on_node,
                               ExState.stopped_on_link):
            diag_name = self.mach.diag.name
            if diag_name == 'main':
                self.select_editor_for_editing('main')
                return
            # log('editor name =' + diag_name)
            if diag_name in self.diag_editors:
                self.select_editor_for_editing(diag_name)
            else:
                self.get_new_diag_editor(
                    diag_name,
                    120, 120, 640, 480,
                    initial_state=DiagEditorState.activated)
                self.select_editor_for_editing(diag_name)

    def editor_handler(self, command, name):
        if command == 'close':
            log(f'bubblmach acknowledging editor is closed', name)
            self.delete_editor(name)
        elif command == 'minimise':
            self.minimise_editor(name)
            self.place_minimised(None)
        elif command == 'maximise':
            self.maximise_editor(name)
        else:
            log('editor_handler not handling', command,level=Logger.INFO)

    def maximise_editor(self, name):
        editor = self.diag_editors[name]
        editor.window.maximise()

    def minimise_editor(self, name):
        editor = self.diag_editors[name]
        editor.window.minimise()
        self.place_minimised(None)

    def unminimise_editor(self, name):
        log('restore editor')
        editor = self.diag_editors[name]
        editor.window.unminimise()
        self.place_minimised(None)

    def delete_editor(self, name, do_reselect=True):
        editor = self.diag_editors[name]
        self.desktop.canvas.delete(editor.uid)
        del (self.diag_editors[name])
        self.stacking_order.remove(editor.name)
        if do_reselect:
            if len(self.stacking_order):
                self.select_editor_for_editing(self.stacking_order[-1])
            else:
                self.select_editor_for_editing('main')
        self.update_console()

    def move_editor_to_top(self, editor):
        name = editor.name
        # if name!=main:
        #    editor.window.canvas.lift(editor.uid)
        # return

        # editor.window.frame.lift()
        # return
        if self.stacking_order[-1:] == [name]:
            return
        log('Attempting to raise editor', name)
        geom = editor.window.geometry()

        log('raising editor', geom)
        # self.delete_editor(name)
        state = self.diag_editors[name].visible_state
        del (self.diag_editors[name])
        self.stacking_order.remove(name)

        self.get_new_diag_editor(name, *geom, initial_state=state,
                                 contents=editor.presenters)
        self.desktop.canvas.delete(editor.uid)

    def update_call_block_presenters(self, block):
        for ed in [self.desktop] + list(self.diag_editors.values()):
            redraw = False
            for p in list(ed.presenters):
                pres = ed.presenters[p]
                if pres.node.type_name == 'CALL':
                    if pres.node.target_name == block.name:
                        log('REMOVING from ', ed.diag.name,
                              'CALL to', block.name)
                        ed.canvas.delete(pres.uid)
                        del ed.presenters[p]
                        redraw = True
            if redraw:
                ed.redraw()

    def handle_user_page_event(self,item,event):
        if not self.get_current_editor().ready_for_user_page_editing:
            return
        if item is not None:
            if item._creator is None:
                return
            diag_name,node=item._creator
            if self.get_current_editor().diag.name!=diag_name:
                return
        else:
            node=None

        #print('IDE handling',diag_name,node,page,event_type,x,y)
        editor=self.get_current_editor()
        editor.handle_user_page_event(node,item,event)

def main():
    ide = IDE()
    ui.run()
    # tk.Canvas().create_text(

    # )


if __name__ == '__main__':
    main()
