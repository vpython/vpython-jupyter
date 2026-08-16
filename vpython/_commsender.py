"""Kernel->browser sender for the Colab (comm-only) frontend.

Same buffering contract as _wssender.WsSender — the scene is built during
`import vpython`, before any frontend can possibly attach — but the channel
is an ipykernel Comm (Colab's google.colab.kernel.comms shim on the browser
side), so there is no cross-thread marshaling: everything runs on the
kernel's main thread and comm.send() is called directly.

One wrinkle the ws sender doesn't have: in Colab mode rate() self-clocks
scene flushes (the browser's pacing triggers can't reach a blocked kernel),
so trigger() runs repeatedly before the frontend attaches. Buffering every
resulting bare 'trigger' handshake would just stuff the backlog with noise,
so unattached 'trigger' strings are dropped; real packages are kept.
"""


class CommSender:
    def __init__(self):
        self._comm = None
        self._backlog = []
        self.replay = None  # callable -> list of wire objdata packages

    @property
    def connected(self):
        return self._comm is not None

    def attach(self, comm):
        """The browser acked on this comm: replay the scene (if a replay
        source is set — it supersedes anything buffered), else flush."""
        self._comm = comm
        if self.replay is not None:
            self._backlog = []
            for objdata in self.replay():
                comm.send(objdata)
            return
        backlog, self._backlog = self._backlog, []
        for objdata in backlog:
            comm.send(objdata)

    def detach(self):
        self._comm = None

    def pending(self):
        return len(self._backlog)

    def __call__(self, objdata):
        if self._comm is None:
            if objdata == 'trigger':
                return  # empty handshake; meaningless to a frontend that missed it
            self._backlog.append(objdata)
        else:
            self._comm.send(objdata)
