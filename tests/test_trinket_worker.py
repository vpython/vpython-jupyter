"""CPython tests for the wasm-host transport patches.

A Web Worker gives vpython a JS host and a single thread: no Jupyter, no
servers, no ``time.sleep`` that anyone can afford. ``trinket_worker`` supplies
the pipe and rewrites vpython's blocking surface to match. These tests stand up
that world on plain CPython -- ``js``/``pyodide.ffi`` are fakes and
``sys.platform`` is forced to ``'emscripten'`` -- so importing the package boots
the *trinket* transport rather than ``no_notebook``'s threads and sockets.

Assertions deliberately run against the package namespace (``vpython.rate``,
``vpython.sleep``), i.e. exactly the names ``from vpython import *`` binds into
a student's program. That also pins the eager-boot ordering in ``__init__.py``:
if the transport booted after the star-imports, ``vpython.sleep`` would still be
the busy-spinning original and these tests would fail.
"""

import asyncio
import sys
import types

import pytest


DEFERRAL_SUFFIX = (" is not supported in the worker runtime yet — "
                   "run without the workerVPython flag to use it.")


@pytest.fixture()
def worker_env(monkeypatch):
    """Import vpython as it comes up inside the worker, with a fake host.

    Yields ``(vpython_module, sent)`` where ``sent`` collects every JSON string
    the transport handed to the host -- the boot flush lands there.
    """
    sent = []

    js = types.ModuleType('js')
    setattr(js, '__trinket_vpython_send', lambda s: sent.append(s))

    ffi = types.ModuleType('pyodide.ffi')
    ffi.create_proxy = lambda f: f
    pyodide_mod = types.ModuleType('pyodide')
    pyodide_mod.ffi = ffi

    monkeypatch.setitem(sys.modules, 'js', js)
    monkeypatch.setitem(sys.modules, 'pyodide', pyodide_mod)
    monkeypatch.setitem(sys.modules, 'pyodide.ffi', ffi)
    monkeypatch.setattr(sys, 'platform', 'emscripten')

    # Force a clean import so the eager boot in __init__.py actually runs;
    # monkeypatch restores whatever was in sys.modules afterwards.
    for name in [m for m in list(sys.modules) if m == 'vpython' or m.startswith('vpython.')]:
        monkeypatch.delitem(sys.modules, name)

    import vpython

    return vpython, sent


def test_transport_booted_and_sent_the_handshake(worker_env):
    """The eager boot must still stand up the transport, not just the patches."""
    vp, sent = worker_env
    assert sent, 'transport sent nothing to the host during boot'
    assert vp.baseObj.glow is not None


def test_rate_returns_a_coroutine(worker_env):
    vp, _ = worker_env
    c = vp.rate(30)
    assert asyncio.iscoroutine(c)
    asyncio.run(c)


def test_rate_flushes_updates_to_the_host(worker_env):
    """rate() is the pacing beat: awaiting one must push buffered work out."""
    vp, sent = worker_env
    before = len(sent)
    asyncio.run(vp.rate(60))
    assert len(sent) > before


def test_sleep_returns_a_coroutine(worker_env):
    vp, _ = worker_env
    c = vp.sleep(0.01)
    assert asyncio.iscoroutine(c)
    asyncio.run(c)


@pytest.mark.filterwarnings('ignore::pytest.PytestUnraisableExceptionWarning')
def test_pause_raises_with_the_message(worker_env):
    vp, _ = worker_env
    cv = object.__new__(vp.canvas)               # no full construction needed
    with pytest.raises(NotImplementedError, match="scene.pause"):
        vp.canvas.pause(cv)


@pytest.mark.filterwarnings('ignore::pytest.PytestUnraisableExceptionWarning')
def test_waitfor_raises_with_the_documented_text(worker_env):
    """Exact wording -- the Task 11 browser assertion matches on it."""
    vp, _ = worker_env
    cv = object.__new__(vp.canvas)
    with pytest.raises(NotImplementedError) as exc:
        vp.canvas.waitfor(cv, 'draw_complete')
    assert str(exc.value) == 'scene.waitfor' + DEFERRAL_SUFFIX


@pytest.mark.filterwarnings('ignore::pytest.PytestUnraisableExceptionWarning')
def test_widgets_raise(worker_env):
    vp, _ = worker_env
    with pytest.raises(NotImplementedError, match="widgets"):
        vp.button(text='go', bind=lambda: None)


# menu reads its own `choices` before delegating to controls.setup, so each
# widget gets the minimum kwargs that reach the shared code path.
WIDGETS = [
    ('button', {'text': 'go'}),
    ('checkbox', {'text': 'on'}),
    ('radio', {'text': 'pick'}),
    ('winput', {}),
    ('menu', {'choices': ['a', 'b']}),
    ('slider', {}),
]


@pytest.mark.filterwarnings('ignore::pytest.PytestUnraisableExceptionWarning')
@pytest.mark.parametrize('name,kwargs', WIDGETS, ids=[w[0] for w in WIDGETS])
def test_every_widget_class_defers(worker_env, name, kwargs):
    """All six share controls.setup, so one patch has to cover all six."""
    vp, _ = worker_env
    with pytest.raises(NotImplementedError, match="widgets"):
        getattr(vp, name)(bind=lambda: None, **kwargs)
