# -*- coding: utf-8 -*

import sys

if sys.version > '3':
    PY3 = True
    print("\r\nVersion:" + sys.version)
    from .mBot_py3 import *
else:
    PY3 = False
    print("\r\nVersion:" + sys.version)
    from .mBot_py2 import *