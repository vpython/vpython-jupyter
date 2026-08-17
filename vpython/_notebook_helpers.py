import os
import sys


def __is_spyder():
    return any('SPYDER' in name for name in os.environ)
        
def __is_idle():
    return 'idlelib' in sys.modules
    
def __is_PyCharm():
    return "PYCHARM_HOSTED" in os.environ

def __is_vscode():
    return 'TERM_PROGRAM' in os.environ.keys() and os.environ['TERM_PROGRAM'] == 'vscode'

def __is_spyder_or_similar_IDE():
    return __is_idle() or __is_spyder() or __is_PyCharm()

def _spyder_run_setting_is_correct():
    try:
        # This is the spyder 3 location
        from spyder.config.main import CONF
    except ImportError:
        # CONF moved in spyder 4
        from spyder.config.manager import CONF

    # Use this instead of accessing like a dictionary so that a
    # default value can be supplied if the setting is missing.
    return CONF.get('run', 'default/interpreter/dedicated', False)


def _warn_if_spyder_settings_wrong():
    from spyder import __version__
    from packaging import version
    pre_4 = version.parse(__version__) < version.parse('4.0.0')
    # It looks like spyder 4 works fine without this setting, perhaps
    # related to the change that they run files in an empty namespace
    # instead of the namespace of the current console.
    if not _spyder_run_setting_is_correct() and pre_4:
        print('\x1b[1;31m**** Please set spyder preference Run to '
              '"Execute in a dedicated console" for the best '
              'vpython experience. ****\x1b[0m')


def _undo_vpython_import_in_spyder():
    for modname, module in list(sys.modules.items()):
        if modname.startswith('vpython'):
            del sys.modules[modname]


def _is_colab(environ=None):
    """Google Colab kernel? (its shell class is 'Shell', not
    ZMQInteractiveShell, so the notebook check below misses it)."""
    environ = os.environ if environ is None else environ
    if 'COLAB_RELEASE_TAG' in environ or 'COLAB_GPU' in environ:
        return True
    return 'google.colab' in sys.modules


def __checkisnotebook():
    """
    Check whether we are running in a notebook or not
    """
    try:
        if __is_spyder():
            return False    # Spyder detected so return False
        if _is_colab():
            return True     # notebook-style pacing/flush behavior applies
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
_in_spyder_or_similar_IDE = __is_spyder_or_similar_IDE()


def _use_ws_frontend(environ=None):
    """Should this notebook kernel speak the whole protocol over the
    websocket (VS Code style) instead of Comm + nbextension JS?

    VS Code notebooks never run vpython's injected JavaScript and give
    third-party renderers no Comm access, so they get the websocket-only
    frontend automatically. VPYTHON_FRONTEND overrides in both directions:
    'ws' forces it on (other renderer hosts, testing), anything else set
    ('jupyter', 'classic', ...) forces it off even under VS Code.
    """
    environ = os.environ if environ is None else environ
    override = environ.get('VPYTHON_FRONTEND')
    if override:
        return override.strip().lower() == 'ws'
    return 'VSCODE_PID' in environ or 'VSCODE_CWD' in environ


def _use_colab_frontend(environ=None):
    """Comm-only frontend for Google Colab: output frames run our JS and
    Colab shims Jupyter comms into them (google.colab.kernel.comms), but no
    websocket can reach the kernel VM (the port proxy rejects programmatic
    fetch/ws from the sandboxed output iframe — probed 2026-08).
    VPYTHON_FRONTEND='colab' forces it on; any other value forces it off.
    """
    environ = os.environ if environ is None else environ
    override = environ.get('VPYTHON_FRONTEND')
    if override:
        return override.strip().lower() == 'colab'
    return _is_colab(environ)
