"""
"""
__version__="1.0.0"
__copyright__="Copyright © 2026 Barnaby McCabe"
import os
def licensing_texts():
    try:
        print('COPYING',os.getcwd()+os.sep+'copying.txt')
        with open(os.getcwd()+os.sep+'copying.txt','r') as f:
            copying=f.read()
    except:
        copying='''
BUBBL is copyright © 2025,2026 Barnaby McCabe
BUBBL is released under the following license:
GNU GENERAL PUBLIC LICENSE version 3, 29th June 2007'''
    return ['''Licenses for parts of BUBBL source code are listed after the
main license.''',
            copying,
'''
Idlelib
=======
Parts of idlelib from idle-1.0.4 have been lifted and reused in the BUBBL IDE.

The modules 'delegator', 'percolator' and 'colorizer' were adapted for use in
the built-in Python editor. This code is licensed as follows:
    
    Copyright 2021-22 Devesh Sharma
    
    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
'''

]