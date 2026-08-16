"""Websocket-only VPython frontend, for notebook hosts that never run
vpython's injected JavaScript — VS Code notebooks foremost (issue #281).

Classic Jupyter (`with_notebook.py`) splits the wire in two: scene packages
go kernel->browser over an ipykernel Comm, and mouse/key events come back
over a raw websocket served by tornado inside the kernel. Renderer hosts
like VS Code expose no Comm channel to third parties, but the websocket is
reachable in both directions. So here the ENTIRE protocol rides the
websocket, and the kernel announces the port with a custom-MIME display
output that the VPython VS Code extension renders:

    application/vnd.vpython.v1+json   {"api": 1, "port": N, "wsuri": "/ws"}

Differences from with_notebook.py, all deliberate:
 - no nbextension file transfer, no display(Javascript(...)) bootstrap
 - sender is a WsSender (buffers until the renderer connects; marshals
   writes onto the tornado thread) instead of a Comm
 - a closing socket does NOT stop tornado: a re-rendered or reloaded
   renderer reconnects and the scene keeps going (latest connection wins)
"""
import os
import json
import socket
import asyncio
import logging
from threading import Thread

from IPython.display import display

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web

from .vpython import GlowWidget, baseObj
from .rate_control import ws_queue
from ._wssender import WsSender
from ._scene_journal import SceneJournal
from ._frontend_replay import make_replay
from ._frontend_wait import wait_for_frontend
from . import __version__

MIME_TYPE = 'application/vnd.vpython.v1+json'


def find_free_port():
    s = socket.socket()
    s.bind(('', 0))
    return s.getsockname()[1]


__SOCKET_PORT = find_free_port()

wsConnected = False
sender = WsSender()
_journal = SceneJournal()
baseObj._journal = _journal      # record every cmd/attr from here on
sender.replay = make_replay(_journal)  # every (re)connect rebuilds the scene
_server_ioloop = None  # the tornado thread's IOLoop, set by start_server


class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        global wsConnected
        sender.attach(self, _server_ioloop)
        wsConnected = True

    def on_message(self, message):
        ws_queue.put(message)

    def on_close(self):
        # Only forget the connection if it is still the active one; a newer
        # renderer may have attached already (VS Code re-renders outputs).
        if sender._handler is self:
            sender.detach()

    def check_origin(self, origin):
        return True


def start_server():
    global _server_ioloop
    asyncio.set_event_loop(asyncio.new_event_loop())
    _server_ioloop = tornado.ioloop.IOLoop.current()
    application = tornado.web.Application([(r'/ws', WSHandler)])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(__SOCKET_PORT)
    log = logging.getLogger('tornado.access')
    log.setLevel(logging.getLevelName('WARN'))
    _server_ioloop.start()


t = Thread(target=start_server, daemon=True)
t.start()

# GlowWidget wires handle_msg/handle_close; sender_override bypasses the Comm.
baseObj.glow = GlowWidget(wsport=__SOCKET_PORT, wsuri='/ws',
                          sender_override=sender)

# Announce the scene to whatever renderer is watching this MIME type. The
# text/plain fallback is what users see when no renderer is installed.
display({
    MIME_TYPE: {'api': 1, 'port': __SOCKET_PORT, 'wsuri': '/ws',
                'version': __version__},
    'text/plain': ('VPython scene (websocket frontend, port {}). '
                   'Install the VPython extension for VS Code to view it; '
                   'see https://github.com/vpython/vpython-jupyter/issues/281'
                   .format(__SOCKET_PORT)),
}, raw=True)

wait_for_frontend(lambda: wsConnected)

baseObj.trigger()  # start the trigger ping-pong process


async def wsperiodic():
    while True:
        if ws_queue.qsize() > 0:
            data = ws_queue.get()
            d = json.loads(data)
            for m in d:
                # message format used by GlowWidget.handle_msg
                msg = {'content': {'data': [m]}}
                baseObj.glow.handle_msg(msg)
        await asyncio.sleep(0.033)

loop = asyncio.get_event_loop()
loop.create_task(wsperiodic())

# Dummy name to import...
_ = None
