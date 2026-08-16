"""Builds the sender.replay callable from the scene journal.

Lazy vpython imports: this module is imported by the frontends during
vpython's own import, and the journal itself must stay pure.
"""


def make_replay(journal):
    from .vpython import baseObj, vector

    def value_of(idx, attr):
        obj = baseObj.object_registry.get(idx)
        if obj is None:
            return None
        try:
            val = getattr(obj, attr)
        except Exception:
            return None
        if type(val) is vector:
            return val.value  # [x, y, z], same conversion trigger() uses
        return val

    def replay():
        return [baseObj.package(journal.replay_objdata(value_of))]

    return replay
