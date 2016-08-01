import os

def glowscript_version():
    """
    Extract the Glowscript version from the javascript in the data directory.
    """

    this_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(this_dir, 'data')
    files = os.listdir(data_dir)
    
    gs_version = None
    for f in files:
        if f[:5] == 'glow.':
            gs_version = f[5:8]
            break

    if gs_version is None:
        raise RuntimeError("Could not determine glowscript version.")

    return gs_version
