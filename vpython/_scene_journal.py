"""Records the scene so any frontend can be rebuilt at any time.

Frontends are ephemeral: Colab re-renders output frames on scroll, VS Code
can evict outputs, pages reload. The kernel is the only durable holder of
the scene, so it must be able to replay it — reset, every constructor in
creation order, then the current value of every attribute that ever
changed — whenever a (new) frontend attaches.

Pure bookkeeping: no vpython imports (the hooks in vpython.py call in), no
wire encoding (the caller pushes the returned objdata through
baseObj.package, the same encoder the live path uses).
"""


class SceneJournal:
    def __init__(self):
        self._cmds = {}    # idx -> constructor cmd (copy)
        self._order = []   # idx in creation order
        self._dirty = set()  # (idx, attr) ever changed after construction
        self._extras = []    # follow-up cmds (title/caption/...): no 'cmd' key

    def record_cmd(self, cmd):
        idx = cmd.get('idx')
        if cmd.get('cmd') == 'delete':
            if idx in self._cmds:
                del self._cmds[idx]
                self._order.remove(idx)
            self._dirty = {(i, a) for (i, a) in self._dirty if i != idx}
            self._extras = [e for e in self._extras if e.get('idx') != idx]
            return
        if cmd.get('cmd') is None:
            # Follow-up on an existing object (title/caption/...): same idx
            # as its constructor — must NOT clobber it.
            self._extras.append(dict(cmd))
            return
        if idx not in self._cmds:
            self._order.append(idx)
        self._cmds[idx] = dict(cmd)

    def record_attr(self, idx, attr):
        self._dirty.add((idx, attr))

    def constructors(self):
        return [self._cmds[i] for i in self._order]

    def dirty_attrs(self):
        return set(self._dirty)

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
            'cmds': ([{'cmd': 'reset', 'idx': -1}] + self.constructors()
                     + [dict(e) for e in self._extras]),
            'methods': [],
            'attrs': attrs,
        }
