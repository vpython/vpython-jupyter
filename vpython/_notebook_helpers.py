import os


def __checkisnotebook():
    """
    Check whether we are running in a notebook or not
    """
    try:
        if any('SPYDER' in name for name in os.environ):
            return False    # Spyder detected so return False
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':  # Jupyter notebook or qtconsole?
            return True
        elif shell == 'TerminalInteractiveShell':  # Terminal running IPython?
            return False
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter


# IMPORTANT NOTE: this is evaluated ONCE the first time this is imported.
_isnotebook = __checkisnotebook()
