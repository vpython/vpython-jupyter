"""Unit tests for the Colab (comm-only) frontend pieces."""
from vpython._notebook_helpers import _use_colab_frontend
from vpython._commsender import CommSender


# ---- detection ------------------------------------------------------------

def test_colab_frontend_off_elsewhere():
    assert _use_colab_frontend(environ={}) is False
    assert _use_colab_frontend(environ={'VSCODE_PID': '1'}) is False


def test_colab_frontend_auto_detects_colab():
    assert _use_colab_frontend(environ={'COLAB_RELEASE_TAG': 'r1'}) is True
    assert _use_colab_frontend(environ={'COLAB_GPU': '0'}) is True


def test_env_override_wins_both_ways():
    assert _use_colab_frontend(environ={'VPYTHON_FRONTEND': 'colab'}) is True
    assert _use_colab_frontend(
        environ={'COLAB_RELEASE_TAG': 'r1', 'VPYTHON_FRONTEND': 'jupyter'}) is False


# ---- the sender -----------------------------------------------------------

class FakeComm:
    def __init__(self):
        self.sent = []

    def send(self, data):
        self.sent.append(data)


def test_packages_buffer_until_attach_then_flush_in_order():
    s = CommSender()
    s([{'cmd': 'canvas', 'idx': 1}])
    s({'attrs': [{'idx': 1}]})
    assert s.pending() == 2 and not s.connected
    comm = FakeComm()
    s.attach(comm)
    assert s.connected
    assert comm.sent == [[{'cmd': 'canvas', 'idx': 1}], {'attrs': [{'idx': 1}]}]


def test_bare_triggers_are_dropped_while_unattached_but_sent_after():
    s = CommSender()
    s('trigger')
    s('trigger')
    assert s.pending() == 0  # noise, not scene state
    comm = FakeComm()
    s.attach(comm)
    s('trigger')
    assert comm.sent == ['trigger']


def test_detach_returns_to_buffering():
    s = CommSender()
    comm = FakeComm()
    s.attach(comm)
    s.detach()
    s([{'cmd': 'sphere', 'idx': 2}])
    assert not s.connected and s.pending() == 1
    comm2 = FakeComm()
    s.attach(comm2)
    assert comm2.sent == [[{'cmd': 'sphere', 'idx': 2}]]


def test_attach_with_replay_source_sends_replay_and_drops_backlog():
    s = CommSender()
    s([{'cmd': 'canvas', 'idx': 1}])  # stale pre-attach buffering
    s.replay = lambda: [{'cmds': [{'cmd': 'reset', 'idx': -1}], 'attrs': 'X'}]
    comm = FakeComm()
    s.attach(comm)
    assert comm.sent == [{'cmds': [{'cmd': 'reset', 'idx': -1}], 'attrs': 'X'}]
    assert s.pending() == 0
