import os


def __is_spyder():
    return any('SPYDER' in name for name in os.environ)


def _spyder_run_setting_is_correct():
    from spyder.config.main import CONF
    return CONF['run']['default/interpreter/dedicated']


def __checkisnotebook():
    """
    Check whether we are running in a notebook or not
    """
    try:
        if __is_spyder():
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
_in_spyder = __is_spyder()
