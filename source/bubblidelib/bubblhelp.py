"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
from bubblib.bubbljson import GlobalDatabase
from bubblib.sysvars import OSVars,FileVars,NetworkVars,PageVars
from bubblib.bubblevent import BubblEvent


def help_text(version):
    return f"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<version><H2> Bubbl Help File</H2><h3>{version}</h3></version>
<html>
<head>
</head>
<Body>
<a href="#intro">Introduction<br/></a>
<a href="#os">Operating System<br/></a>
<a href="#file">File System<br /></a>
<a href="#page">The Display<br /></a>
<a href="#database">Database and Tables<br /></a>
<a href="#events">Events<br /></a>
<a href="#network">Networking<br /></a>
<a href="#bubbl">Under the hood<br /></a>

<hr />
<h3><a name="intro">Introduction<br/></a>
<p><pre>
Bubbl is an integrated development environment for Python.

At its simplest it provides a desktop on which python modules can be created and run.
An unusual feature of the Bubbl desktop is it allows a python module to be broken
up into separate chunks (or 'blocks') of code.  These blocks share the same namespace,
so can access each other's variables, imports etc.  They can also be linked together
and combined with other ready-made blocks to make a 'behaviour diagram' which in
essence is an app.

The global namespace remains unchanged between runs of the code-blocks, allowing
stepping through the blocks one at a time.  This allows a flexible and fast working
style.  When uncertain about a particular Python library module or detail, it is very
easy to 'suck it and see' without disturbing your work flow.  You can just create a
new block of source code in a different place on the desktop and try it out without
getting in the way of what you are working on.  The desktop supports persistent views
of variable values, free text for comments, web-links, images and other items,
allowing you to program with all relevant resources for your program close to hand.

Another unusual feature is the ability to 'step backwards' through code execution.
After a block has been run, hitting 'Back' will 'un-run' it, restoring any variables
assigned to their original values (or non-existence).  This can shorten the 
'run-to-breakpoint, test,[ modify, (compile,) run-from-beginning-to-breakpoint]' cycle,
as you don't have to go back to the beginning every time to re-test your modified code
-instead its 'step, test, [undo modify step]'. 

In addition to Python code blocks, there are ready-made 'blocks' which allow
straightforward access to the computer's resources such as keyboard and mouse, 
display, file system, OS, network etc. The ready-made blocks allow the behaviour
diagram to encapsulate all 'real-time' behaviour of the program without the need
for async and/or threading code.  The BUBBL IDE allows you to define your own
blocks (as behaviour diagrams in their own right), which can then be used in
other diagrams so that larger and more complex apps can be constructed.

Behaviour diagrams (BBSM's for 'Bubbl Behavioural State Machines') constitute
callable blocks with inputs and outputs, and one or more 'links' allowing control
flow to be organised as a network rather than with traditional 'structured' code.
It is much easier for a third party to understand code when presented this way, 
particularly as any comments or links to relevant documentation can be present
on the diagram.

</pre></p>

<h3><a name="os">Operating System<br/></a>
<p><pre>
{OSVars.__doc__}
</pre></p>
<hr />
<h3><a name="file">File System<br /></a>
<p><pre>
{FileVars.__doc__}
</pre></p>
<hr />
<h3><a name="page">The Display<br /></a>
<p><pre>
{PageVars.__doc__}
</pre></p>
<hr />
<h3><a name="database">Database and Tables<br /></a>
<p><pre>
{GlobalDatabase.__doc__}
</pre></p>
<hr />
<h3><a name="events">Events<br /></a>
<p><pre>
{BubblEvent.__doc__}
</pre></p>
<hr />
<h3><a name="network">Networking<br /></a>
<p><pre>
{NetworkVars.__doc__}
</pre></p>
<hr />
<h3><a name="bubbl">Under the hood<br /></a>
<p><pre>Under the Hood
BUBBL uses TKinter to deliver a variety of pre-configured user interface items.
It works co-operatively with the TKinter event loop to implement the IDE's
user interface and/or a BUBBL app user interface(s) seamlessly with no conflicts
or bottlnecks. A central 'user interface server' allows a BUBBL app to create
multiple instances of the BUBBL virtual machine running different applications
asynchronously.  These instances can communicate with each other reliably
through BUBBL's event system, and this allows the programmer to develop
independent and reusable modules without the need for  complex system
integration processes.
<h3><b>_mach</b> builtin variable</h3>
The variable _mach is present in all BUBBL namespaces/modules and refers to
the currently running BUBBL virtual machine. Useful attributes/methods are:
    _mach.ok_load_mach(name,init,diag='main',node=None)
        This method starts a new BUBBL machine with its own thread of execution.
        The machine can be communicated with from other machines via 'messages'
        (see below).  Returns false if the machine fails to load properly.
    _mach.message
        Writing a tuple of (name,object) to this attribute puts a 'Message'
        event into the named machine's event queue with the event attribute
        'value' referencing object    
    _mach.undoable
        This read only variable allows you to write Python code
        which is undoable depending on the running context (i.e.
        whether stepping etc)
    _mach.ui()
        This references the ui 'server' supporting the tkinter UI, drag
        and drop operations and the 'system clipboard'.
        It's field 'root' references the TKinter root window.
        
<h3><b>_Iset</b> built in class representing an ordered set of integers</h3>
    _Isets are similar to Python sets, but they only contain integers and are
        always ordered. They can be iterated and reverse iterated over, and
        they support 'undoable' iteration.
        They support union (| or +), intersection (& or *), disjunction
        (-) operations on, and can be constructed from, _Isets, ranges, integers
        and other iterators over integers. If initialised with a keyword
        parameter 'indexed=&lt;object&gt;' the field 'indexed' returns an iterator
        over the object's values indexed by the _Iset.
        The members of an _Iset can also be accessed directly by index. The
        operators &lt;&lt; and &gt;&gt; return _Isets of indexed values or 
        _Isets of value indices respectively
        
<h3><b>_eval</b> built in function for converting constant expessions into values</h3>
    This function does not evaluate expressions containing variables or
    operators, but it returns , e.g., [1,2,3] if passed the string "[1,2,3]"
            
<h3> Images - the BUBBLImage class</h3>
    The show-image block and _fs.image function create BUBBLImage instances.
    These are a container class for PIL images and have the following
    attributes:
    
    &lt;image&gt;.pil_image  References the contained PIL Image object
    &lt;image&gt;.to_base64  Returns a base64 encoding of the PIL Image object
    &lt;image&gt;.ok_save_to_file(filename) Returns True if the PIL Image object
        is successfully written to the file 'filename'
        
    BUBBLImage instances assigned to variables will be 'persistent' and
    saved with the BUBBL app's database (or source code if run from the
    BUBBL IDE) in the same way as other variables.  To avoid this behaviour
    (and therefore avoid, e.g., very large source-files) variable names
    should start with an underscore.
        E.g: Assuming the last block was a 'show-image' block, the assignment
                my_image=_pg[-1].image  #Access last item on page
             will store a reference to the image in the variable 'my_image'.
              
        On normal program exit, the variable's value (i.e. the BUBBLImage)
        will be saved with the program's source code or in its database and
        be restored when the program is next run. 
</pre></p>
<hr />

</Body>
"""
