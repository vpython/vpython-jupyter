from ._version import get_versions
from .gs_version import glowscript_version
__version__ = get_versions()['version']
__gs_version__ = glowscript_version()
del get_versions
del glowscript_version

# Keep this import last to ensure that __version__ and __gs_version__ exist
# before importing vpython, which itself imports both of those.

def __checkisnotebook(): # returns True if running in Jupyter notebook
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':  # Jupyter notebook or qtconsole?
            return True
        elif shell == 'TerminalInteractiveShell':  # Terminal running IPython?
            return False
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter
_isnotebook = __checkisnotebook()

import platform
__p = platform.python_version()
__ispython3 = (__p[0] == '3')
__require_notebook = (not __ispython3) or (__p[2] < '5') # Python 2.7 or 3.4 require Jupyter notebook

if __require_notebook and (not _isnotebook):
        s = "The non-notebook version of vpython requires Python 3.5 or later."
        s += "\nvpython does work on Python 2.7 and 3.4 in the Jupyter notebook environment."
        raise Exception(s)

if _isnotebook:
    from .with_notebook import *
else:
    from .no_notebook import *

