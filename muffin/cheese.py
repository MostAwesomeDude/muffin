from muffin.pan import const, matches, tie, Alt, Cat, Ex, Lazy, Patch

S = Alt(Ex("N"), Cat(Lazy(const, Patch), Cat(Ex("+"), Lazy(const, Patch))))
tie(S)

def runS():
    s = "N" + "+N" * 10
    print matches(S, s)
