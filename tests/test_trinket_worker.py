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


# --- pacing: rate(N) must deliver N iterations/second, work included ---------
#
# A flat ``asyncio.sleep(1/maxRate)`` sleeps the whole period on top of whatever
# the student's loop body cost, so rate(60) with 10 ms of physics runs at ~37 Hz.
# Upstream subtracts the measured user-code time (_RateKeeper2.__call__'s
# ``userTime``) from the delay; these assert the same property on the worker's
# fixed-timestep version of it.
#
# Wall-clock assertions are deliberately loose: they pin the DIRECTION and rough
# magnitude, because CI timing is noisy and asyncio.sleep only ever overshoots.


def _spin(seconds):
    """Burn CPU without yielding — synchronous user code, as a student writes it.

    ``asyncio.sleep`` would be a yield point, which is exactly what these tests
    must not hand the loop for free.
    """
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        pass


def test_rate_paces_at_the_target_with_negligible_user_code(worker_env):
    """No regression: an empty loop at rate(N) still takes ~iterations/N."""
    vp, _ = worker_env
    iterations, target = 10, 50
    ideal = iterations / target                  # 0.20 s

    async def loop():
        for _ in range(iterations):
            await vp.rate(target)

    started = time.monotonic()
    asyncio.run(loop())
    elapsed = time.monotonic() - started

    # Lower bound is one period short of ideal: the first call has no previous
    # return to measure a remainder from and so only yields (see _async_rate).
    assert elapsed > ideal * 0.7, 'rate(%d) did not pace at all' % target
    assert elapsed < ideal * 1.6, 'rate(%d) paced far slower than target' % target


def test_rate_subtracts_user_code_time_from_the_period(worker_env):
    """THE FIX: work inside the period must not be added on top of it.

    rate(50) is a 20 ms period; with 10 ms of user code per iteration the loop
    must still take ~20 ms per iteration, not 30. Ten iterations: 0.2 s, not 0.3.
    """
    vp, _ = worker_env
    iterations, target, work = 10, 50, 0.010
    ideal = iterations / target                          # 0.20 s — work absorbed
    flat = iterations * (1.0 / target + work)            # 0.30 s — work added on

    async def loop():
        for _ in range(iterations):
            await vp.rate(target)
            _spin(work)

    started = time.monotonic()
    asyncio.run(loop())
    elapsed = time.monotonic() - started

    assert elapsed < (ideal + flat) / 2, (
        'rate(%d) with %.0f ms of user code took %.3f s for %d iterations; '
        'flat-sleep behaviour is ~%.3f s, compensated is ~%.3f s'
        % (target, work * 1000, elapsed, iterations, flat, ideal))
    # The other side of it, or "compensation" that just stopped sleeping whenever
    # the body did any work at all would pass the assertion above. Subtracting
    # the body's cost must not turn rate(N) into a free-running loop.
    assert elapsed > ideal * 0.7, (
        'rate(%d) with user code ran at %.1f Hz — it stopped pacing rather than '
        'compensating' % (target, iterations / elapsed))


def test_rate_still_yields_when_user_code_overruns_the_period(worker_env):
    """Safety: over-period work must not turn rate() into a non-yielding return.

    In a worker the host delivers browser events by CALLING the transport's
    dispatch, which only gets a turn when the running coroutine gives one up. A
    rate() that returns without awaiting therefore freezes the scene — no events
    dispatched, no flush — while the program runs flat out. (Stop survives it:
    that is worker.terminate() on the page side and needs nothing from this
    thread. Which makes the symptom subtler, not milder.)
    """
    vp, _ = worker_env
    calls = 5
    bystander_runs = []

    async def bystander():
        while True:
            bystander_runs.append(time.monotonic())
            await asyncio.sleep(0)

    async def loop():
        task = asyncio.ensure_future(bystander())
        await asyncio.sleep(0)                   # let it reach its first await
        before = len(bystander_runs)
        for _ in range(calls):
            await vp.rate(1000)                  # 1 ms period...
            _spin(0.005)                         # ...and 5 ms of user code
        gained = len(bystander_runs) - before
        task.cancel()
        return gained

    gained = asyncio.run(loop())
    assert gained >= calls, (
        'rate() yielded %d times in %d over-period calls — a loop that stops '
        'yielding starves the event loop, so no browser event is dispatched and '
        'no update is flushed: the scene freezes while the program runs on'
        % (gained, calls))


def test_rate_does_not_accumulate_debt_after_an_overrun(worker_env):
    """No catch-up burst: falling behind must not buy zero-sleep iterations.

    A deadline advanced by += period would owe five periods after a 100 ms
    stall and then rush the next five calls through instantly.
    """
    vp, _ = worker_env
    target, catchup = 50, 5
    period = 1.0 / target

    async def loop():
        await vp.rate(target)                    # arm the timestep
        _spin(period * 5)                        # fall five periods behind
        await vp.rate(target)                    # already late: no sleep owed
        started = time.monotonic()
        for _ in range(catchup):
            await vp.rate(target)
        return time.monotonic() - started

    elapsed = asyncio.run(loop())
    assert elapsed > period * catchup * 0.7, (
        '%d calls to rate(%d) after an overrun took %.3f s — the loop burst '
        'through them repaying debt' % (catchup, target, elapsed))


def test_rate_recomputes_the_period_when_maxrate_changes(worker_env):
    """maxRate may differ call to call; the period in force is the current one."""
    vp, _ = worker_env

    async def loop():
        await vp.rate(1000)                      # arm with a 1 ms period
        started = time.monotonic()
        await vp.rate(10)                        # 100 ms period, effective NOW
        return time.monotonic() - started

    elapsed = asyncio.run(loop())
    assert elapsed > 0.05, (
        'rate(10) after rate(1000) slept %.3f s — it reused the old period'
        % elapsed)


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


def test_sleep_flushes_updates_to_the_host(worker_env):
    """sleep() is a pacing call too: the first one must push buffered work out."""
    vp, sent = worker_env
    before = len(sent)
    asyncio.run(vp.sleep(0.001))
    assert len(sent) > before


def test_sleep_honours_the_same_render_cap_as_rate(worker_env):
    """`while True: sleep(0.001)` must not flood the page.

    rate() was capped; sleep() sat next to it flushing on every call, which is
    ~1000 packages/second for a shape a beginner reaches by accident. Both now
    share one gate, so this asserts the same property as
    test_rate_honours_the_render_cap.
    """
    vp, sent = worker_env
    from vpython import rate_control

    calls = 40
    before = len(sent)
    started = time.monotonic()

    async def burst():
        for _ in range(calls):
            await vp.sleep(0.001)

    asyncio.run(burst())
    elapsed = time.monotonic() - started
    flushes = len(sent) - before

    assert flushes < calls, 'no render cap: every sleep() flushed'
    assert flushes <= elapsed * rate_control.MAX_RENDERS + 2


def test_rate_and_sleep_share_one_flush_gate(worker_env):
    """One cap for the pair, not one each — a loop mixing them still obeys it."""
    vp, sent = worker_env
    from vpython import rate_control

    calls = 40
    before = len(sent)
    started = time.monotonic()

    async def burst():
        for _ in range(calls):
            await vp.rate(1000)
            await vp.sleep(0.001)

    asyncio.run(burst())
    elapsed = time.monotonic() - started
    flushes = len(sent) - before

    assert flushes <= elapsed * rate_control.MAX_RENDERS + 2


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


# --- the synchronous barriers that used to deadlock silently ----------------
#
# Each of these waits for a browser reply that, in a worker, can only be
# delivered by the very thread doing the waiting. Before they were patched they
# hung — at 100% CPU, because `_wait` polls with `rate(30)` and rate is now a
# coroutine factory that never sleeps when called from synchronous library code.
# Decision V5: a deferral must be LOUD. These assert the noise.


@pytest.mark.filterwarnings('ignore::pytest.PytestUnraisableExceptionWarning')
def test_compound_defers(worker_env):
    vp, _ = worker_env
    with pytest.raises(NotImplementedError) as exc:
        vp.compound([])
    assert str(exc.value) == 'compound' + DEFERRAL_SUFFIX


@pytest.mark.filterwarnings('ignore::pytest.PytestUnraisableExceptionWarning')
def test_text_defers(worker_env):
    vp, _ = worker_env
    with pytest.raises(NotImplementedError) as exc:
        vp.text(text='hello')
    assert str(exc.value) == 'text' + DEFERRAL_SUFFIX


@pytest.mark.filterwarnings('ignore::pytest.PytestUnraisableExceptionWarning')
def test_extrusion_defers(worker_env):
    vp, _ = worker_env
    with pytest.raises(NotImplementedError) as exc:
        vp.extrusion(path=[vp.vec(0, 0, 0), vp.vec(0, 0, -1)],
                     shape=vp.shapes.circle(radius=1))
    assert str(exc.value) == 'extrusion' + DEFERRAL_SUFFIX


@pytest.mark.filterwarnings('ignore::pytest.PytestUnraisableExceptionWarning')
def test_clone_defers(worker_env):
    """Patched on standardAttributes, so every drawable object is covered.

    clone() is the intermittent one: it spins only `while not baseObj.empty()`,
    so whether it hangs depends on where the last flush fell. Raising always is
    the point — a construct that deadlocks one run in three is harder to
    diagnose than one that deadlocks every time.
    """
    vp, _ = worker_env
    from vpython import vpython as _vp
    ball = object.__new__(vp.sphere)             # no wire traffic needed
    with pytest.raises(NotImplementedError) as exc:
        _vp.standardAttributes.clone(ball)
    assert str(exc.value) == 'obj.clone' + DEFERRAL_SUFFIX


@pytest.mark.filterwarnings('ignore::pytest.PytestUnraisableExceptionWarning')
def test_mouse_pick_defers(worker_env):
    """A property, so the deferral has to fire on ATTRIBUTE ACCESS, not a call."""
    vp, _ = worker_env
    with pytest.raises(NotImplementedError) as exc:
        vp.scene.mouse.pick
    assert str(exc.value) == 'scene.mouse.pick' + DEFERRAL_SUFFIX


@pytest.mark.filterwarnings('ignore::pytest.PytestUnraisableExceptionWarning')
def test_the_module_level_waiter_defers_as_a_backstop(worker_env):
    """text/extrusion/pick are every caller today; a future one must not hang."""
    vp, _ = worker_env
    from vpython import vpython as _vp
    with pytest.raises(NotImplementedError, match='waiting for a scene event'):
        _vp._wait(None)


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
