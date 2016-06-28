from ._version import get_versions
from .gs_version import glowscript_version
__version__ = get_versions()['version']
__gs_version__ = glowscript_version()
del get_versions
del glowscript_version

# Keep this import last to ensure that __version__ and __gs_version__ exist
# before importing vpython, which itself imports both of those.
from .vpython import *
