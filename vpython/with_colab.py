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
import uuid

from IPython import get_ipython
from IPython.display import display, HTML
from ipykernel.comm import Comm

from .vpython import GlowWidget, baseObj
from . import rate_control
from ._commsender import CommSender
from ._scene_journal import SceneJournal
from ._frontend_replay import make_replay
from ._notebook_helpers import _use_colab_frontend  # noqa: F401  (re-export for tests)
from . import __version__

COMM_TARGET = 'vpython-glow'
# JS-initiated handshake target (preferred): the kernel registers this
# passively at import and the BROWSER opens the comm once its libraries have
# actually loaded — no races, no retry guessing. The kernel-initiated path
# below stays as a fallback for hosts whose comms shim cannot open().
KERNEL_TARGET = 'vpython-glow-kernel'

# Stamped into the bootstrap JS. Colab notebooks saved WITH outputs replay
# old bootstrap frames on reopen; those zombies happily call comms.open at
# the new kernel and fight the live frame for the scene (observed). Opens
# must present the CURRENT session's nonce or be closed immediately.
SESSION_NONCE = uuid.uuid4().hex

# Where the browser loads GlowScript + fonts/textures from. jsDelivr serves
# the public vpython/vscode-vpython repo's media/ directory (same assets the
# VS Code extension bundles). Override for development with
# VPYTHON_COLAB_CDN (must end with '/').
CDN_BASE = os.environ.get(
    'VPYTHON_COLAB_CDN',
    'https://cdn.jsdelivr.net/gh/vpython/vscode-vpython@main/media/')

sender = CommSender()
_journal = SceneJournal()
baseObj._journal = _journal      # record every cmd/attr from here on
sender.replay = make_replay(_journal)  # every attach rebuilds the scene
_pending_comm = None
_unconnected_cells = 0
_bootstrap_shown = False


def _open_comm():
    """One comm-open attempt. The browser acks every open it sees and the
    latest one becomes the active channel on both sides.

    NEVER close previous attempts here. The ack for open N arrives while the
    kernel is idle — exactly when a retry would be closing comm N to open
    N+1 — so a close-and-reopen loop drops every ack it ever provokes
    (observed live: 600+ buffered packages, permanently disconnected).
    Orphaned opens are cheap; the ack that finally lands picks its comm."""
    global _pending_comm
    comm = Comm(target_name=COMM_TARGET,
                data={'version': __version__, 'nonce': SESSION_NONCE})

    _wire_comm(comm)
    _pending_comm = comm


def show():
    """(Re)display the VPython output frame under the current cell.

    Manual recovery: if no scene/status box ever appeared, run
    `import vpython.with_colab as wc; wc.show()`.

    The bootstrap logic loads as an EXTERNAL script from the same CDN as
    GlowScript; the inline part is one line. (Colab silently declines to
    activate large inline scripts in display output — observed 2026-08 —
    while script-src tags and one-liners run fine.)"""
    display(HTML(
        "<div id='vpython-colab-root'></div>"
        "<script>(function(){"
        "var s=document.createElement('script');"
        "s.src='" + CDN_BASE + "glowcomm_colab.js?v=" + SESSION_NONCE + "';"
        "s.onload=function(){window.__VPYTHON_COLAB_BOOT({cdn:'" + CDN_BASE +
        "',nonce:'" + SESSION_NONCE + "'});};"
        "s.onerror=function(){document.getElementById('vpython-colab-root')"
        ".textContent='VPython: failed to load bootstrap from CDN';};"
        "document.head.appendChild(s);})();</script>"))


def _wire_comm(comm):
    """Attach a live comm (from either handshake direction) to the sender
    and route its incoming messages."""
    def _on_msg(msg, comm=comm):
        data = msg['content']['data']
        if isinstance(data, dict) and 'ack' in data:
            sender.attach(comm)
            return
        baseObj.glow.handle_msg(msg)
    comm.on_msg(_on_msg)


def _on_target_open(comm, open_msg):
    # Browser-initiated open (preferred path): the JS is ready by definition.
    data = (open_msg or {}).get('content', {}).get('data', {})
    if not isinstance(data, dict) or data.get('nonce') != SESSION_NONCE:
        try:
            comm.close()  # zombie frame from a previously saved output
        except Exception:
            pass
        return
    _wire_comm(comm)
    sender.attach(comm)


def _post_execute():
    global _unconnected_cells
    if sender.connected:
        _unconnected_cells = 0
        return
    _unconnected_cells += 1
    if _unconnected_cells >= 1 and not _bootstrap_shown:
        # Two whole cells and still no ack: assume the bootstrap frame never
        # rendered (or died) and put up a fresh one. Latest registration wins
        # on the browser side, latest ack wins here — converges cleanly.
        show()
        _unconnected_cells = 0
    _open_comm()


# Passive target for the browser-initiated handshake — registered BEFORE the
# bootstrap is displayed, so whenever the JS opens the comm the target exists.
try:
    _shell_for_target = get_ipython()
    if _shell_for_target is not None and getattr(_shell_for_target, 'kernel', None) is not None:
        _shell_for_target.kernel.comm_manager.register_target(
            KERNEL_TARGET, _on_target_open)
except Exception:
    pass  # fall back to the kernel-initiated handshake below

# NOT calling show() here: Colab silently drops display output emitted
# during `import vpython` (observed consistently; import-time displays
# never rendered once). The scene box appears either from an explicit
# wc.show() cell (the demo's cell 3) or from the post_execute self-heal.

baseObj.glow = GlowWidget(sender_override=sender)

# NOTE: no kernel-side retry loop. The browser initiates the handshake
# (comms.open against the passive target above) the moment its JS is ready,
# so kernel-initiated opens are pure fallback (one per post_execute). A 1 Hz
# idle-loop of comm_opens was observed to make Colab silently DROP display
# outputs emitted near them — it cost us the bootstrap box entirely.
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
