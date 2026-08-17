"""Kernel->browser sender for the websocket-only frontend.

Classic Jupyter sends scene packages over an ipykernel Comm. Hosts like VS
Code give third-party renderers no Comm access, so this sender writes the
same packages to the tornado websocket instead.

Two realities shape it:

- The renderer connects *after* the first packages exist (`import vpython`
  builds the scene before any frontend can possibly attach), so everything
  is buffered until a connection appears, then flushed in order.

- vpython calls the sender from the kernel's main thread, but the tornado
  server lives on its own thread with its own IOLoop; tornado websockets are
  not thread-safe, so every write is marshaled with IOLoop.add_callback.
"""
import json


class WsSender:
    def __init__(self):
        self._handler = None
        self._ioloop = None
        self._backlog = []
        self.replay = None  # callable -> list of wire objdata packages

    def attach(self, handler, ioloop):
        """A renderer connected: replay the scene (if a replay source is
        set — it supersedes anything buffered), else flush the backlog."""
        self._handler = handler
        self._ioloop = ioloop
        if self.replay is not None:
            self._backlog = []
            for objdata in self.replay():
                ioloop.add_callback(handler.write_message, json.dumps(objdata))
            return
        backlog, self._backlog = self._backlog, []
        for text in backlog:
            ioloop.add_callback(handler.write_message, text)

    def detach(self):
        """The renderer went away; buffer until another one connects."""
        self._handler = None
        self._ioloop = None

    def pending(self):
        return len(self._backlog)

    def __call__(self, objdata):
        # sender() receives either the literal handshake string 'trigger' or
        # a JSON-able package (dict from baseObj.package, list of cmds).
        text = objdata if isinstance(objdata, str) else json.dumps(objdata)
        if self._handler is None:
            self._backlog.append(text)
        else:
            self._ioloop.add_callback(self._handler.write_message, text)
