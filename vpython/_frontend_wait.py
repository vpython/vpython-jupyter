"""Bounded wait for the browser-side (glowcomm) frontend to connect.

Historically `import vpython` in a notebook busy-waited forever on the
websocket handshake. In any frontend that does not run vpython's injected
JavaScript — VS Code notebooks and Google Colab are the common ones — that
loop never exits and the kernel appears to hang (issue #281). A loud, prompt
error beats a silent forever.

Injected clock/sleep/environ keep this unit-testable without a kernel.
"""
import os
import time

DEFAULT_TIMEOUT = 30.0  # seconds; generous for slow nbextension first-runs
_POLL = 0.1


def _timeout_from(environ):
    raw = environ.get('VPYTHON_CONNECT_TIMEOUT')
    if raw:
        try:
            value = float(raw)
            if value > 0:
                return value
        except ValueError:
            pass
    return DEFAULT_TIMEOUT


def _environment_note(environ):
    if 'VSCODE_PID' in environ or 'VSCODE_CWD' in environ:
        return ("It looks like this kernel was started by VS Code. VS Code's "
                "notebook UI does not run vpython's frontend JavaScript, so "
                "VPython cannot display there yet.")
    if 'COLAB_RELEASE_TAG' in environ or 'COLAB_GPU' in environ:
        return ("It looks like this is Google Colab. Colab's output sandbox "
                "does not run vpython's frontend JavaScript, so VPython "
                "cannot display there yet.")
    return ("The notebook frontend never ran vpython's JavaScript. This "
            "happens in notebook UIs that do not support Jupyter "
            "nbextensions/labextensions.")


def wait_for_frontend(is_connected, environ=None, _time=time.time,
                      _sleep=time.sleep):
    """Poll `is_connected()` until true, or raise RuntimeError on timeout."""
    environ = os.environ if environ is None else environ
    timeout = _timeout_from(environ)
    deadline = _time() + timeout
    while not is_connected():
        if _time() >= deadline:
            raise RuntimeError(
                "no VPython frontend connected after {:.0f}s.\n{}\n"
                "VPython works in Jupyter Notebook and JupyterLab opened in a "
                "web browser. VS Code support is tracked at "
                "https://github.com/vpython/vpython-jupyter/issues/281 .\n"
                "(If your environment is just slow to start, raise the limit "
                "with the VPYTHON_CONNECT_TIMEOUT environment variable.)"
                .format(timeout, _environment_note(environ)))
        _sleep(_POLL)
