# bubblonpython
Bubbl Unique Bulding Block Layer on Python:  Apps as executable diagrams on an 'active paper' worktop
-----------------------------------------------------------------------------------------------------
BUBBL on Python is a GUI program development environment using a 'desktop' 
metaphor on which diagrams are created and then 'run' as apps.

There are unique features of the development environment such as: stepping a
program backwards to find bugs; freely placing images, web-links, graphics, 
live-views of variables and expressions and other 'active' items within the
code;  allowing multiple 'snippets' of code runnable with a click to 'try it 
and see' without having to edit and then re-edit source code.

The diagrams are a hybrid of flow-charts and state-diagrams and consist of
linked-together blocks which define how the program behaves. There are built-
in blocks which make it easy to access all the computer's resources (e.g. 
screen, keyboard, mouse, file system, images, network etc.) without having to
memorize 'library' calls. The programmer can also define new blocks, including
'raw Python' blocks which can access anything from the Python universe.

Applications made with BUBBL can be distributed as a simple python module plus
a zip file of the BUBBL libraries.

Installation Instructions
=========================
The following instructions assume Python version 3.8.10 or later is installed
on the target machine, and that typing 'python' at the command prompt starts
that version of Python.

The file bubbl.zip should be unzipped to the folder where BUBBL will be installed
(the 'installation folder').

On Linux (and possibly other platforms) BUBBL should be run in a Python
virtual environment to avoid clashing with system tools.

To create a virtual environment do the following:
1. Create a folder to store the virtual environment.
     Note: This is not where you will create programs, but where Python
           scripts will find the installed modules and libraries.
           For more information see:
                https://docs.python.org/3/library/venv.html
2. On Windows, open 'command prompt', on Linux open a terminal.
3. Enter "python -m venv  _path-to-v-env_"
        where _path-to-v-env_ is the path of the folder
4. Activate the virtual environment (this has to be done every
        time BUBBL is run from the command line)
   
   On Windows enter "_path-to-v-env_\Scripts\activate"
   
   On Linux enter "source _path-to-v-env_/bin/activate"
   
      Note: The virtual environment can be deactivated by
            entering "_deactivate_"

Note: Before installing BUBBL on Linux Mint or Ubuntu, install the
    python3-tk package (e.g. by entering: _sudo apt install python3-tk_
    in a terminal).

With the virtual environment activated (if necessary) navigate to the 
installation folder and  enter _python bubbl.py_. This will start the BUBBL
IDE after successfully completing the installation process.

If any additional requirements are necessary, run the above command again
when they have been met.

Getting Started
---------------
Bubbl on Python comes with some example apps which can be run, edited and
otherwise played with. These include:
  A Jigsaw maker
  A Sudoku Solver
  'Planet of the Pompeys' game
  An Oware player
  An alarm clock
  An AI face detector

Other information
-----------------
Applications can be run within the IDE giving access to all the features
such as live variable views and stepping or stepping backwards etc. or
they can be run as standalone Python scripts.

Standalone programs should be saved with a '.py' extension and need to
have a copy (or zipped copy) of 'bubblib' folder in the same folder. 
The bubblib folder can be found in bubblib.zip which is in bubbl.zip



