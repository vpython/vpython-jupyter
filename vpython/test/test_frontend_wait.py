"""The frontend-connect wait must never hang forever (issue #281).

Pure-python tests: the helper takes its clock, sleeper, and environment as
parameters, so no kernel, websocket, or notebook is involved.
"""
import pytest

from vpython._frontend_wait import wait_for_frontend, DEFAULT_TIMEOUT


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def time(self):
        return self.now

    def sleep(self, dt):
        self.now += dt


def test_returns_as_soon_as_the_frontend_connects():
    clock = FakeClock()
    flips_at = 1.0
    wait_for_frontend(lambda: clock.now >= flips_at,
                      environ={}, _time=clock.time, _sleep=clock.sleep)
    assert clock.now < flips_at + 1.0  # returned promptly, no full-timeout burn


def test_raises_instead_of_hanging_when_nothing_ever_connects():
    clock = FakeClock()
    with pytest.raises(RuntimeError) as exc:
        wait_for_frontend(lambda: False,
                          environ={}, _time=clock.time, _sleep=clock.sleep)
    msg = str(exc.value)
    assert 'no VPython frontend connected' in msg
    assert 'vpython-jupyter/issues/281' in msg
    assert 'Jupyter' in msg  # points at an environment that works


def test_message_names_vscode_when_running_under_vscode():
    clock = FakeClock()
    with pytest.raises(RuntimeError) as exc:
        wait_for_frontend(lambda: False,
                          environ={'VSCODE_PID': '123'},
                          _time=clock.time, _sleep=clock.sleep)
    assert 'VS Code' in str(exc.value)


def test_message_names_colab_when_running_under_colab():
    clock = FakeClock()
    with pytest.raises(RuntimeError) as exc:
        wait_for_frontend(lambda: False,
                          environ={'COLAB_RELEASE_TAG': 'x'},
                          _time=clock.time, _sleep=clock.sleep)
    assert 'Colab' in str(exc.value)


def test_timeout_is_overridable_via_environment():
    clock = FakeClock()
    with pytest.raises(RuntimeError):
        wait_for_frontend(lambda: False,
                          environ={'VPYTHON_CONNECT_TIMEOUT': '2'},
                          _time=clock.time, _sleep=clock.sleep)
    assert clock.now < DEFAULT_TIMEOUT  # honored the shorter override


def test_bogus_override_falls_back_to_default():
    clock = FakeClock()
    with pytest.raises(RuntimeError):
        wait_for_frontend(lambda: False,
                          environ={'VPYTHON_CONNECT_TIMEOUT': 'soon'},
                          _time=clock.time, _sleep=clock.sleep)
    assert clock.now >= DEFAULT_TIMEOUT
