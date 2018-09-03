from .vpython import baseObj

# This must come after creating a canvas


class MISC(baseObj):
    def __init__(self):
        # _canvas_constructing is set below to
        # avoid initiating the connection to javascript
        # until the first object is drawn.
        baseObj._canvas_constructing = True
        super(MISC, self).__init__()
        baseObj._canvas_constructing = False

    def prnt(self, s):
        self.addmethod('GSprint', s)


__misc = MISC()


def GSprint(*args):
    s = ''
    for a in args:
        s += str(a) + ' '
    s = s[:-1]
    __misc.prnt(s)
