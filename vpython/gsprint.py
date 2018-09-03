from .vpython import baseObj

# This must come after creating a canvas


class MISC(baseObj):
    def __init__(self):
        super(MISC, self).__init__()

    def prnt(self, s):
        self.addmethod('GSprint', s)


__misc = MISC()


def GSprint(*args):
    s = ''
    for a in args:
        s += str(a) + ' '
    s = s[:-1]
    __misc.prnt(s)
