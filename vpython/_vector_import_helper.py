import platform

try:
    if platform.python_implementation() == 'PyPy':
        from .vector import *    # use pure python vector for PyPy
    else:
        from .cyvector import *
        v = vector(0,0,0)
except:
    from .vector import *

# Remove platform from the namespace now that we are done with it
del platform

# synonyms in GlowScript
vec = vector
