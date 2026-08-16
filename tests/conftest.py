"""Make the in-tree ``vpython`` package importable regardless of cwd.

The repo root is prepended (not appended) so these tests always exercise the
working tree rather than any copy of vpython installed in site-packages.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
