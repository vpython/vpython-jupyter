"""Unit tests for the websocket-only frontend (VS Code notebooks).

Pure-python: the sender takes its ioloop/handler as injected fakes, and the
mode-selection helpers take an environment dict.
"""
import json

from vpython._notebook_helpers import _use_ws_frontend
from vpython._wssender import WsSender


# ---- mode selection -------------------------------------------------------

def test_ws_frontend_off_in_plain_jupyter():
    assert _use_ws_frontend(environ={}) is False


def test_ws_frontend_auto_detects_vscode():
    assert _use_ws_frontend(environ={'VSCODE_PID': '123'}) is True
    assert _use_ws_frontend(environ={'VSCODE_CWD': '/x'}) is True


def test_env_override_forces_ws_frontend_anywhere():
    assert _use_ws_frontend(environ={'VPYTHON_FRONTEND': 'ws'}) is True


def test_env_override_forces_classic_even_under_vscode():
    env = {'VSCODE_PID': '123', 'VPYTHON_FRONTEND': 'jupyter'}
    assert _use_ws_frontend(environ=env) is False


# ---- the sender -----------------------------------------------------------

class FakeIOLoop:
    """Records add_callback calls; run() executes them (simulating the
    tornado thread servicing its queue)."""
    def __init__(self):
        self.queue = []

    def add_callback(self, fn, *args):
        self.queue.append((fn, args))

    def run(self):
        q, self.queue = self.queue, []
        for fn, args in q:
            fn(*args)


class FakeHandler:
    def __init__(self):
        self.sent = []

    def write_message(self, text):
        self.sent.append(text)


def test_packages_sent_before_connect_are_buffered_then_flushed_in_order():
    s = WsSender()
    s('trigger')
    s([{'cmd': 'canvas', 'idx': 1}])
    handler, ioloop = FakeHandler(), FakeIOLoop()
    s.attach(handler, ioloop)
    ioloop.run()
    assert handler.sent[0] == 'trigger'
    assert json.loads(handler.sent[1]) == [{'cmd': 'canvas', 'idx': 1}]


def test_send_after_connect_goes_through_the_ioloop_not_directly():
    s = WsSender()
    handler, ioloop = FakeHandler(), FakeIOLoop()
    s.attach(handler, ioloop)
    ioloop.run()
    s({'attrs': [{'idx': 1, 'pos': [0, 0, 0]}]})
    # nothing written until the tornado thread services its callback queue
    assert handler.sent == []
    ioloop.run()
    assert json.loads(handler.sent[0]) == {'attrs': [{'idx': 1, 'pos': [0, 0, 0]}]}


def test_detach_buffers_again_until_reconnect():
    s = WsSender()
    handler, ioloop = FakeHandler(), FakeIOLoop()
    s.attach(handler, ioloop)
    ioloop.run()
    s.detach()
    s('trigger')
    assert s.pending() == 1
    handler2 = FakeHandler()
    s.attach(handler2, ioloop)
    ioloop.run()
    assert handler2.sent == ['trigger']


def test_strings_pass_through_unjsonified():
    s = WsSender()
    handler, ioloop = FakeHandler(), FakeIOLoop()
    s.attach(handler, ioloop)
    s('trigger')
    ioloop.run()
    assert handler.sent == ['trigger']
