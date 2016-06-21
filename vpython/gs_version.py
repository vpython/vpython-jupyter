from __future__ import print_function

import os
import re


def glowscript_version():
    """
    Extract the Glowscript version from the javascript in the data directory.
    """
    data_name = 'data'
    glowscript_name = 'glow.2.1.min.js'
    this_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(this_dir, data_name)

    with open(os.path.join(data_dir, glowscript_name)) as f:
        contents = f.read()

    # Use the non-greedy form of "+" below to ensure we get the shortest
    # possible match.
    result = re.search('var glowscript=\{version:"(.+?)"\}', contents)
    if result:
        gs_version = result.group(1)
    else:
        raise RuntimeError("Could not determine glowscript version.")

    return gs_version
