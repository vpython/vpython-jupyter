"""Records the scene so any frontend can be rebuilt at any time.

Frontends are ephemeral: Colab re-renders output frames on scroll, VS Code
can evict outputs, pages reload. The kernel is the only durable holder of
the scene, so it must be able to replay it — reset, then every cmd in its
original emission order, then the current value of every attribute that
ever changed — whenever a (new) frontend attaches.

Emission order matters: canvas construction emits its ctor, then a
lights='empty_list' follow-up (wiping glow's built-in default lights), then
the two standard distant_light ctors. Replaying follow-ups after the
constructors would run that wipe last and delete the standard lights — the
scene rebuilds but renders ambient-only (dim).

Pure bookkeeping: no vpython imports (the hooks in vpython.py call in), no
wire encoding (the caller pushes the returned objdata through
baseObj.package, the same encoder the live path uses).
"""

_CTOR, _EXTRA = 'ctor', 'extra'


class SceneJournal:
    def __init__(self):
        self._cmds = {}    # idx -> constructor cmd (live reference)
        self._log = []     # (_CTOR, idx) | (_EXTRA, cmd) in emission order
        self._dirty = set()  # (idx, attr) ever changed after construction

    def record_cmd(self, cmd):
        idx = cmd.get('idx')
        if cmd.get('cmd') == 'delete':
            self._cmds.pop(idx, None)
            self._log = [(kind, ref) for (kind, ref) in self._log
                         if not (kind == _CTOR and ref == idx)
                         and not (kind == _EXTRA and ref.get('idx') == idx)]
            self._dirty = {(i, a) for (i, a) in self._dirty if i != idx}
            return
        if cmd.get('cmd') is None:
            # Follow-up on an existing object (title/caption/lights/...):
            # same idx as its constructor — must NOT clobber it, and must
            # keep its place in the emission order.
            self._log.append((_EXTRA, cmd))
            return
        if idx not in self._cmds:
            self._log.append((_CTOR, idx))
        # Store the LIVE reference, copy at replay time: constructors are
        # enriched after appendcmd (canvas adds its attrs afterwards), and a
        # record-time copy ships a bare canvas (observed: dim default scene).
        self._cmds[idx] = cmd

    def record_attr(self, idx, attr):
        self._dirty.add((idx, attr))

    def constructors(self):
        return [dict(self._cmds[ref]) for (kind, ref) in self._log
                if kind == _CTOR]

    def dirty_attrs(self):
        return set(self._dirty)

    def _replay_cmds(self):
        out = [{'cmd': 'reset', 'idx': -1}]
        for (kind, ref) in self._log:
            out.append(dict(self._cmds[ref]) if kind == _CTOR else dict(ref))
        return out

    def replay_objdata(self, value_of):
        """Build the {'cmds', 'methods', 'attrs'} objdata that reconstructs
        the scene. value_of(idx, attr) returns the CURRENT wire-ready value,
        or None when the object is gone (entry skipped)."""
        attrs = {}
        for (idx, attr) in self._dirty:
            if idx not in self._cmds:
                continue
            val = value_of(idx, attr)
            if val is None:
                continue
            attrs.setdefault(idx, {})[attr] = val
        return {
            'cmds': self._replay_cmds(),
            'methods': [],
            'attrs': attrs,
        }
