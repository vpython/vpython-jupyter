"""Transport for Pyodide/wasm hosts — e.g. trinket's #108 Web Worker.

The notebook transport talks over a Jupyter Comm; the standalone transport
stands up an ``http.server`` plus autobahn websockets in threads. Neither
exists inside a Web Worker: there is no Jupyter, no server, and no threads.
What a worker does have is a host JS environment with ``postMessage`` — so
here the host supplies the pipe and this module supplies the seam.

The contract with the host, kept deliberately tiny:

* Before ``import vpython``, the host defines ``__trinket_vpython_send`` on
  the JS global scope: a function of one argument, a JSON string. Every
  outbound update package (and the bare ``"trigger"`` handshake) goes through
  it. What the host does with the string — ``postMessage`` it to a page, hand
  it to a renderer — is its business.

* This module sets ``__trinket_vpython_dispatch`` on the JS global scope: a
  function of one argument, a JSON **array** of browser events in glowcomm's
  wire format. The host calls it whenever events arrive. Each call processes
  the events and then flushes buffered updates back out through
  ``__trinket_vpython_send`` — the same request/reply rhythm the websocket
  transport uses, with the host (ultimately the browser's ~33 ms
  ``canvas_update`` timer) setting the pace.

Like the other transports, importing this module IS the setup; it ends by
binding the module-global ``sender``, patching vpython's blocking surface (see
``apply_worker_patches``) and starting the update ping-pong.
"""

import json

import js
from pyodide.ffi import create_proxy

from .vpython import GlowWidget, baseObj
from . import vpython as _protocol


def _send(msg):
    """Ship one update package (or the 'trigger' handshake) to the host.

    ``trigger()`` hands us either the bare string ``'trigger'`` or the
    ``{cmds, methods, attrs}`` dict from ``baseObj.package``. Encode
    uniformly; the receiving side re-parses.
    """
    js.__trinket_vpython_send(json.dumps(msg))


def _dispatch(events_json):
    """Process a JSON array of browser events, then flush updates back.

    Mirrors the websocket transports: events go one at a time to
    ``handle_msg`` (bound-event handlers rely on that), and every inbound
    message — including a bare trigger with no events — is answered with a
    flush. ``_isnotebook`` is False here, so ``handle_msg`` does not trigger
    by itself; the flush below is that reply.
    """
    events = json.loads(events_json) if events_json else []
    for evt in events:
        if isinstance(evt, dict) and 'trigger' in evt:
            continue                       # pacing only; the flush below answers it
        baseObj.glow.handle_msg({'content': {'data': [evt]}})
    baseObj.trigger()


_DEFER = ("{name} is not supported in the worker runtime yet — "
          "run without the workerVPython flag to use it.")


def apply_worker_patches():
    """Make vpython's blocking surface cooperative (or loudly absent) for a
    single-threaded wasm host. Called from the transport bootstrap; separated so
    plain-CPython tests can exercise the patches without a live transport.

    Every construct patched here spins the one and only thread while waiting on
    the browser — which, in a worker, is the thread the browser's replies have
    to arrive on. Waiting is therefore a deadlock, so each is either made
    awaitable (``rate``, ``sleep``: the async transform inserts the ``await``)
    or made to fail loudly rather than hang.
    """
    import asyncio
    import time
    from . import rate_control
    from . import vpython as _vp

    # Upstream RateKeeper decouples the rate() call frequency from the render
    # frequency: however often the loop asks, at most MAX_RENDERS renders go out
    # per second (rate_control.py:153). Keep that contract — rate(1000) must
    # still pace at 1000 Hz, but it must not flush 1000 packages/second at the
    # page. Flushes we skip are not lost: the updates stay buffered and go out
    # with the next one.
    _render_period = 1.0 / rate_control.MAX_RENDERS
    _last_flush = [float('-inf')]

    def _flush_if_due():
        """Flush buffered updates, at most MAX_RENDERS times a second.

        Shared by rate() and sleep(): both are pacing calls in a student's loop,
        and both must therefore obey the same render cap. Without it,
        ``while True: sleep(0.001)`` — a shape a beginner reaches by accident —
        floods the page with ~1000 update packages a second, each one a
        postMessage plus a handle() on the main thread.
        """
        now = time.monotonic()
        if now - _last_flush[0] >= _render_period:
            _last_flush[0] = now
            baseObj.trigger()                  # flush buffered updates

    # rate(N) means "N iterations per second", not "sleep 1/N between them".
    # Upstream measures the time spent in user code between rate() returns
    # (_RateKeeper2.__call__'s `userTime`, rate_control.py:173) and subtracts it
    # from the delay. A flat sleep does not: rate(60) with 10 ms of physics per
    # iteration runs at ~37 Hz, visibly slower than the same program elsewhere.
    # So remember when the last call RETURNED (i.e. when the user's iteration
    # began) and sleep only the remainder of the period.
    _last_return = [None]

    async def _async_rate(maxRate):
        _flush_if_due()
        # Recomputed every call: maxRate may change between calls, and the
        # period in force is the current one — rate(10) after a rate(1000) loop
        # must slow down on THIS call, not the next.
        period = 1.0 / float(maxRate)
        last = _last_return[0]
        # FIRST call: nothing has been timed yet, so no part of a period is
        # owed; yield and return, as upstream's `count == 1` branch does after
        # callInteract(). It costs one period once per program and gets the
        # flush we just issued onto the page without an added wait.
        remaining = 0.0 if last is None else (last + period) - time.monotonic()
        # Always await, even at zero. When user code overruns the period the
        # remainder is negative and there is nothing left to wait for — but a
        # bare return would never yield to the event loop, and in a worker run
        # nothing else does either: the host delivers browser events by CALLING
        # __trinket_vpython_dispatch, and that call only gets a turn when the
        # running coroutine gives one up. A rate() that stops yielding therefore
        # freezes the scene — no events dispatched, no flush, a program running
        # flat out with a picture that never changes.
        #
        # It does NOT break Stop: Stop is worker.terminate() on the page side,
        # which is unconditional and needs no cooperation from this thread
        # (trinket's worker-client.js says so at the top). That makes the
        # symptom subtler, not milder — a frozen animation from a program that
        # is still running reads as "vpython is broken" rather than as a hang.
        #
        # asyncio.sleep(0) yields. Clamping at 0 also means a loop that falls
        # behind simply stays behind rather than banking debt and then bursting
        # through a batch of zero-sleep iterations to catch up.
        await asyncio.sleep(remaining if remaining > 0.0 else 0.0)
        # Anchor on the ACTUAL return, not on `last + period`: that is what makes
        # the clamp above debt-free.
        _last_return[0] = time.monotonic()

    def _rate(self, maxRate=100):
        # Validate SYNCHRONOUSLY, before building the coroutine: parity with
        # _RateKeeper2.__call__ (rate_control.py:265), where rate(0) raises at
        # the call site. Inside the coroutine the error would surface only on
        # await — and not at all if the program never awaits.
        if maxRate < 1:
            raise ValueError("rate value must be greater than or equal to 1")
        return _async_rate(maxRate)

    # rate is a module-level INSTANCE bound into user namespaces at import time
    # (rate_control.py: `rate = _RateKeeper2(...)`); patching the class __call__
    # changes the already-bound object everywhere.
    rate_control._RateKeeper2.__call__ = _rate

    async def _async_sleep(dt):
        _flush_if_due()
        await asyncio.sleep(dt)
    _vp.sleep = _async_sleep                   # BEFORE __init__'s star-import binds it

    def _deferred(name):
        def _raise(*args, **kwargs):
            raise NotImplementedError(_DEFER.format(name=name))
        return _raise

    _vp.canvas.pause = _deferred('scene.pause')
    _vp.canvas.waitfor = _deferred('scene.waitfor')
    # button/checkbox/radio/winput/menu/slider all subclass `controls`, but each
    # defines its own __init__ that calls `controls.setup` — setup, not
    # __init__, is the one shared entry point, so that is what gets patched.
    _vp.controls.setup = _deferred('widgets (button/slider/menu/checkbox/radio/winput)')

    # The OTHER synchronous barriers — the ones that look like ordinary drawing
    # rather than like waiting, which is exactly why they have to be loud.
    #
    # Each of these spins the one and only thread until the browser answers, and
    # in a worker the browser's answer arrives *on that thread* (via
    # __trinket_vpython_dispatch). So the wait can never end: they deadlock.
    # Worse, they do it at 100% CPU — `_wait()` polls with `rate(30)`, and rate
    # is now a coroutine factory, so called from synchronous library code it
    # builds a coroutine and throws it away without ever sleeping.
    #
    #   compound(...)        vpython.py: `while not baseObj.sent: time.sleep(.001)`
    #   text(...)            vpython.py: _wait(canvas)  — measures the glyph run
    #   extrusion(...)       vpython.py: _wait(canvas)  — measures the swept shape
    #   scene.mouse.pick     vpython.py: _wait(canvas)  — waits for setpick
    #   obj.clone()          vpython.py: `while not baseObj.empty(): rate(60)`
    #
    # A student who hits one of these gets no scene, no error and a Stop button
    # that works — the silent no-op decision V5 exists to forbid. Making them
    # raise costs the feature and keeps the diagnosis. (`clone` is the one that
    # only *sometimes* hangs, depending on whether the buffer happens to be
    # empty; a construct that deadlocks intermittently is worse than one that
    # always does, not better.)
    _vp.compound.__init__ = _deferred('compound')
    _vp.text.__init__ = _deferred('text')
    _vp.extrusion.__init__ = _deferred('extrusion')
    _vp.standardAttributes.clone = _deferred('obj.clone')
    # pick is a property; keep the original setter, which already refuses.
    _vp.Mouse.pick = property(_deferred('scene.mouse.pick'), _vp.Mouse.pick.fset)
    # Backstop for any other caller of the module-level waiter: the four above
    # are every one in the package today, but a future one would otherwise hang
    # silently rather than say so.
    _vp._wait = _deferred('waiting for a scene event')


# GlowWidget() records itself as baseObj.glow. Outside a notebook it sets the
# module-global sender to None, so ours is installed after it.
GlowWidget()
_protocol.sender = _send

js.__trinket_vpython_dispatch = create_proxy(_dispatch)

# Patch before the first flush — and, via __init__'s eager boot, before the
# star-imports bind rate/sleep into the package namespace.
apply_worker_patches()

# Start the ping-pong exactly as with_notebook does. Because __init__.py boots
# this transport EAGERLY — before `scene = canvas()` — the buffer is empty here,
# so this first trigger() is the bare 'trigger' handshake rather than a package;
# the scene canvas and its lights are constructed just afterwards and flush on
# the next trigger (the first rate() call, or the host's next dispatch ping).
# What matters either way is that it sets baseObj.sent, which appendcmd() and
# addmethod() spin on.
baseObj.trigger()

# Dummy name to import, matching the other transports.
_ = None
