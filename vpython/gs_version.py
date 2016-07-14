from __future__ import print_function

import os
from glob import glob
import re


def glowscript_version():
    """
    Extract the Glowscript version from the javascript in the data directory.
    """
    data_name = 'data'

    this_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(this_dir, data_name)

    glowscript_file = glob(os.path.join(data_dir, 'glow.*.min.js'))

    glowscript_name = glowscript_file[0]

    # Use the non-greedy form of "+" below to ensure we get the shortest
    # possible match.
    result = re.search('glow\.(.+?)\.min\.js', glowscript_name)
    if result:
        gs_version = result.group(1)
    else:
        raise RuntimeError("Could not determine glowscript version.")

    return gs_version
