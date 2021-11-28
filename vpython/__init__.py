from ._version import get_versions
from .gs_version import glowscript_version
__version__ = get_versions()['version']
__gs_version__ = glowscript_version()
del get_versions
del glowscript_version

# Keep the remaining imports later to  ensure that __version__ and
#  __gs_version__ exist before importing vpython, which itself imports
# both of those.

from ._notebook_helpers import __is_spyder

from .vpython import canvas

# Need to initialize canvas before user does anything and before
# importing GSprint
scene = canvas()

from .vpython import *
from .shapespaths import *
from ._vector_import_helper import *
from .rate_control import rate
from .gsprint import GSprint

# gsprint and vpython are showing up in the
# namespace, so delete them
del gsprint, vpython

# cyvector may be in the namespace. Get rid of it
try:
    del cyvector
except NameError:
    pass

# import for backwards compatibility
from math import *
from numpy import arange
from random import random

if __is_spyder():
    from ._notebook_helpers import _warn_if_spyder_settings_wrong
    _warn_if_spyder_settings_wrong()
