from muffin.pan import Alt, Cat, Ex, Red, Rep, Null


fs = frozenset


def Optional(l):
    """
    Match either the given language, or the null string.
    """

    return Alt(l, Null)


def Bracket(bra, ket):
    """
    Generate an object that can be passed a language to bracket that language.

    Parse bra, then the bracketed language, then ket.
    """

    def Bracketed(l):
        """
        Bracket a language.
        """

        return Cat(bra, Cat(l, ket))

    return Bracketed


def Sep(l, s):
    """
    Parse a language at least once, with subsequent iterations separated by a
    separator in-between.

    To get a zero-or-more version, use Optional() around this combinator.
    """

    return Cat(l, Rep(Cat(s, l)))


def String(s):
    """
    Match every member of the string in turn, returning the entire string.
    """

    if not s:
        return Null
    parser = Ex(s[0])
    for c in s[1:]:
        parser = Cat(parser, Ex(c))
    return Red(parser, lambda _: s)
