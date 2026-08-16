"""Comm-only VPython frontend for Google Colab.

Colab's output frames run arbitrary JS (unlike VS Code), but no websocket
can reach the kernel VM (the port proxy rejects programmatic connections
from the sandboxed output iframe — probed 2026-08). What Colab does provide
is a Jupyter-comm shim (google.colab.kernel.comms), verified fully duplex.
So this frontend is the mirror image of with_wsfrontend: the ENTIRE
protocol rides an ipykernel Comm.

Three consequences of comm messages only being processed when the kernel is
idle between executions:

- No blocking handshake. `import vpython` displays the JS bootstrap,
  attempts a comm open, and RETURNS; everything is buffered in a CommSender
  until the browser's ack arrives (processed after the cell ends).

- Comm-open retry. The kernel cannot know when the bootstrap script has
  registered its comm target, and an open that arrives first is lost. A
  post_execute hook reopens the comm after every cell until acked.

- Self-clocked flush. The browser's 33 ms pacing triggers cannot reach a
  blocked kernel, so rate() synthesizes the trigger itself
  (rate_control._direct_trigger) — animation flushes at full speed from
  inside `while` loops. Camera zoom/orbit is browser-side and unaffected.
  Known v1 limitation: kernel-side event handlers (scene.bind) and
  scene.mouse only update between cells.
"""
import os
import asyncio

from IPython import get_ipython
from IPython.display import display, HTML
from ipykernel.comm import Comm

from .vpython import GlowWidget, baseObj
from . import rate_control
from ._commsender import CommSender
from ._notebook_helpers import _use_colab_frontend  # noqa: F401  (re-export for tests)
from . import __version__

COMM_TARGET = 'vpython-glow'

# Where the browser loads GlowScript + fonts/textures from. jsDelivr serves
# the public vpython/vscode-vpython repo's media/ directory (same assets the
# VS Code extension bundles). Override for development with
# VPYTHON_COLAB_CDN (must end with '/').
CDN_BASE = os.environ.get(
    'VPYTHON_COLAB_CDN',
    'https://cdn.jsdelivr.net/gh/vpython/vscode-vpython@main/media/')

sender = CommSender()
_pending_comm = None
_unconnected_cells = 0


def _open_comm():
    """One comm-open attempt. The browser acks every open it sees and the
    latest one becomes the active channel on both sides.

    NEVER close previous attempts here. The ack for open N arrives while the
    kernel is idle — exactly when a retry would be closing comm N to open
    N+1 — so a close-and-reopen loop drops every ack it ever provokes
    (observed live: 600+ buffered packages, permanently disconnected).
    Orphaned opens are cheap; the ack that finally lands picks its comm."""
    global _pending_comm
    comm = Comm(target_name=COMM_TARGET, data={'version': __version__})

    def _on_msg(msg, comm=comm):
        data = msg['content']['data']
        if isinstance(data, dict) and 'ack' in data:
            sender.attach(comm)  # latest ack wins; backlog flushes here
            return
        baseObj.glow.handle_msg(msg)  # event batch from the browser

    comm.on_msg(_on_msg)
    _pending_comm = comm


def show():
    """(Re)display the VPython output frame under the current cell.

    Manual recovery: if no scene/status box ever appeared (Colab sometimes
    drops display output emitted during `import vpython`), run
    `import vpython.with_colab as wc; wc.show()`."""
    display(HTML('<div id="vpython-colab-root"></div>'
                 '<script>' + _read_bootstrap_js() + '</script>'))


def _post_execute():
    global _unconnected_cells
    if sender.connected:
        _unconnected_cells = 0
        return
    _unconnected_cells += 1
    if _unconnected_cells >= 2:
        # Two whole cells and still no ack: assume the bootstrap frame never
        # rendered (or died) and put up a fresh one. Latest registration wins
        # on the browser side, latest ack wins here — converges cleanly.
        show()
        _unconnected_cells = 0
    _open_comm()


def _read_bootstrap_js():
    package_dir = os.path.dirname(__file__)
    path = os.path.join(package_dir, 'vpython_libraries', 'glowcomm_colab.js')
    with open(path, encoding='utf-8') as f:
        return f.read().replace('__CDN_BASE__', CDN_BASE)


show()

baseObj.glow = GlowWidget(sender_override=sender)

# Keep trying to open the comm from the kernel's idle loop: the bootstrap
# frame loads its JS asynchronously, so opens fired at import/post_execute
# time routinely race it and are lost. The kernel processes browser messages
# only while idle — which is exactly when this task runs, so an open, the
# browser's ack, and the attach all complete within ~a second of any idle
# moment after the JS is ready. Bounded so an abandoned session goes quiet.


async def _retry_until_connected():
    for _ in range(300):
        if sender.connected:
            return
        _open_comm()
        await asyncio.sleep(1.0)

asyncio.get_event_loop().create_task(_retry_until_connected())
rate_control._direct_trigger = True

_shell = get_ipython()
if _shell is not None:
    _shell.events.register('post_execute', _post_execute)

# First attempt usually races the (async) bootstrap iframe and is lost; the
# post_execute hook covers it from the next cell on.
_open_comm()

baseObj.trigger()  # buffered by CommSender until the browser acks

# Dummy name to import...
_ = None
