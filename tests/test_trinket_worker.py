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
import time
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

    # Force a clean import so the eager boot in __init__.py actually runs -- and
    # put sys.modules back exactly as found afterwards. The package that comes
    # up in here is emscripten-flavoured (async sleep, raising widgets); leaving
    # it cached would hand it to every later `import vpython` in the session,
    # including whatever else the suite runs on darwin.
    saved = {k: v for k, v in sys.modules.items()
             if k == 'vpython' or k.startswith('vpython.')}
    for name in saved:
        del sys.modules[name]

    try:
        import vpython
        yield vpython, sent
    finally:
        for name in [m for m in list(sys.modules)
                     if m == 'vpython' or m.startswith('vpython.')]:
            del sys.modules[name]
        sys.modules.update(saved)


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


def test_rate_honours_the_render_cap(worker_env):
    """rate(1000) must pace at 1000 Hz but still render at most MAX_RENDERS/s.

    Upstream RateKeeper decouples the two (rate_control.py:153); without the
    same cap a tight rate(1000) loop floods the page with update packages.
    """
    vp, sent = worker_env
    from vpython import rate_control

    calls = 40
    before = len(sent)
    started = time.monotonic()

    async def burst():
        for _ in range(calls):
            await vp.rate(1000)

    asyncio.run(burst())
    elapsed = time.monotonic() - started
    flushes = len(sent) - before

    assert flushes < calls, 'no render cap: every rate() call flushed'
    # +1 for the flush on the very first call, +1 for scheduling slop.
    assert flushes <= elapsed * rate_control.MAX_RENDERS + 2


@pytest.mark.parametrize('bad', [0, -1])
def test_rate_rejects_values_below_one(worker_env, bad):
    """Parity with _RateKeeper2.__call__ -- rate(0) raises, it does not clamp."""
    vp, _ = worker_env
    with pytest.raises(ValueError, match='greater than or equal to 1'):
        vp.rate(bad)


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


def test_the_fixture_leaves_no_emscripten_build_cached():
    """Runs last on purpose: every test above used worker_env.

    If the emscripten-booted package were still in sys.modules, the next
    `import vpython` anywhere in the session -- on darwin, in some other test
    file -- would silently get async sleep, raising widgets and a transport
    talking to a fake `js`. Asserting the cache is clean is both the check and
    the guarantee that a later import rebuilds the real thing; actually
    importing vpython here is not an option, since on a desktop platform that
    starts the no_notebook http server and opens a browser tab.
    """
    leaked = sorted(m for m in sys.modules if m == 'vpython' or m.startswith('vpython.'))
    assert leaked == [], 'worker_env leaked modules into sys.modules: %s' % leaked
