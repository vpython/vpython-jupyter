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
    from . import rate_control
    from . import vpython as _vp

    async def _async_rate(maxRate):
        baseObj.trigger()                      # flush buffered updates
        await asyncio.sleep(1.0 / max(float(maxRate), 1.0))

    # rate is a module-level INSTANCE bound into user namespaces at import time
    # (rate_control.py: `rate = _RateKeeper2(...)`); patching the class __call__
    # changes the already-bound object everywhere.
    rate_control._RateKeeper2.__call__ = lambda self, maxRate=100: _async_rate(maxRate)

    async def _async_sleep(dt):
        baseObj.trigger()
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


# GlowWidget() records itself as baseObj.glow. Outside a notebook it sets the
# module-global sender to None, so ours is installed after it.
GlowWidget()
_protocol.sender = _send

js.__trinket_vpython_dispatch = create_proxy(_dispatch)

# Patch before the first flush — and, via __init__'s eager boot, before the
# star-imports bind rate/sleep into the package namespace.
apply_worker_patches()

# Start the ping-pong exactly as with_notebook does: the first trigger()
# flushes anything already buffered (the scene canvas constructed during
# `import vpython` is sitting in the buffer at this point) and sets
# baseObj.sent, which appendcmd()/addmethod() spin on.
baseObj.trigger()

# Dummy name to import, matching the other transports.
_ = None
