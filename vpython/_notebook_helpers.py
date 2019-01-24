import os
import sys


def __is_spyder():
    return any('SPYDER' in name for name in os.environ)


def _spyder_run_setting_is_correct():
    from spyder.config.main import CONF
    return CONF['run']['default/interpreter/dedicated']


def _warn_if_spyder_settings_wrong():
    if not _spyder_run_setting_is_correct():
        print('\x1b[1;31m**** Please set spyder preference Run to '
              '"Execute in a dedicated console" for the best '
              'vpython experience. ****\x1b[0m')


def _undo_vpython_import_in_spyder():
    for modname, module in list(sys.modules.items()):
        if modname.startswith('vpython'):
            del sys.modules[modname]


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
