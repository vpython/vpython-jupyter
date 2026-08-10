"""gcurve/gdots constructor `size=` must reach the browser.

`gobj.size` is DERIVED from `_radius`, so `gobj.setup`'s `setattr(self,'_'+a,val)`
convention wrote a dead `_size` and the send loop shipped the default. See
https://github.com/vpython/vpython-jupyter/issues/287.

These tests drive `gobj.setup` directly against a stub so they need no transport,
no browser and no event loop — the bug and its fix are entirely in that method.
"""
import sys
import types

import pytest


@pytest.fixture()
def gobj_cls(monkeypatch):
    """Import vpython.vpython far enough to reach gobj, with the transport faked.

    Importing the PACKAGE would build a canvas and select a transport; importing
    the module alone is enough, since gobj.setup only touches baseObj bookkeeping.
    """
    saved = {k: v for k, v in sys.modules.items() if k.startswith('vpython')}
    for k in list(sys.modules):
        if k.startswith('vpython'):
            del sys.modules[k]

    # `vpython/__init__.py` imports pkg_resources (setuptools), which is absent
    # from a bare CPython and from wasm builds. Faked rather than depended on so
    # this test does not need setuptools installed to run.
    if 'pkg_resources' not in sys.modules:
        pkg = types.ModuleType('pkg_resources')

        class _DistNotFound(Exception):
            pass

        # Must REPORT a version rather than raise: __init__ swallows
        # DistributionNotFound and leaves __version__ unset, and vpython.py
        # then fails on `from vpython import __version__`.
        def _get_distribution(name):
            return types.SimpleNamespace(version='0.0.0-test')

        pkg.DistributionNotFound = _DistNotFound
        pkg.get_distribution = _get_distribution
        monkeypatch.setitem(sys.modules, 'pkg_resources', pkg)

    # `scene = canvas()` runs at package import, but canvas construction sets
    # baseObj._canvas_constructing, which SKIPS the transport selection — so no
    # websocket/Jupyter machinery is reached and these fakes are enough.
    js = types.ModuleType('js')
    js.__trinket_vpython_send = lambda s: None
    ffi = types.ModuleType('pyodide.ffi'); ffi.create_proxy = lambda f: f
    pyo = types.ModuleType('pyodide'); pyo.ffi = ffi
    monkeypatch.setitem(sys.modules, 'js', js)
    monkeypatch.setitem(sys.modules, 'pyodide', pyo)
    monkeypatch.setitem(sys.modules, 'pyodide.ffi', ffi)

    try:
        from vpython import vpython as vp
        yield vp
    finally:
        for k in list(sys.modules):
            if k.startswith('vpython'):
                del sys.modules[k]
        sys.modules.update(saved)


def _make(vp, cls_name, **kwargs):
    """Run gobj.setup for one constructor without a live transport.

    appendcmd is captured so the test can assert on the WIRE package — the thing
    the browser actually receives — rather than only on the Python object.
    """
    # setup() -> baseObj.__init__() would otherwise select a transport (on a
    # desktop that means no_notebook, i.e. an http server + autobahn). Declaring
    # the view already constructed skips that; the argument handling under test
    # is unaffected by which transport is in place.
    vp.baseObj._view_constructed = True

    cls = getattr(vp, cls_name)
    obj = object.__new__(cls)
    sent = []
    obj.appendcmd = sent.append
    args = dict(kwargs)
    args['_objName'] = cls_name
    vp.gobj.setup(obj, args)
    return obj, (sent[0] if sent else {})


@pytest.mark.parametrize('cls_name', ['gdots', 'gcurve'])
def test_constructor_size_reaches_the_object_and_the_wire(gobj_cls, cls_name):
    obj, cmd = _make(gobj_cls, cls_name, size=8)
    assert obj.size == 8, 'the constructor argument was dropped'
    assert obj.radius == 4, 'size must set the backing _radius (size == 2*radius)'
    assert cmd.get('size') == 8, 'the browser was sent the default instead of the argument'


@pytest.mark.parametrize('cls_name', ['gdots', 'gcurve'])
def test_no_dead_private_size_attribute_is_left_behind(gobj_cls, cls_name):
    obj, _ = _make(gobj_cls, cls_name, size=8)
    assert not hasattr(obj, '_size'), '_size is not the backing store and must not be written'


def test_radius_still_works_and_agrees_with_size(gobj_cls):
    obj, cmd = _make(gobj_cls, 'gdots', radius=4)
    assert obj.radius == 4
    assert obj.size == 8
    assert cmd.get('radius') == 4


def test_default_size_is_unchanged_when_not_specified(gobj_cls):
    obj, cmd = _make(gobj_cls, 'gdots', color=None) if False else _make(gobj_cls, 'gdots')
    assert obj.size == 6 and obj.radius == 3, 'defaults must not move'
    assert 'size' not in cmd, 'unspecified attributes are not sent'


def test_the_setter_path_still_works(gobj_cls):
    """Post-construction assignment was never broken; pin it so a fix here
    cannot regress it."""
    obj, _ = _make(gobj_cls, 'gdots')
    obj.addattr = lambda attr: None          # setter calls addattr; no transport here
    obj.size = 10
    assert obj.size == 10 and obj.radius == 5
