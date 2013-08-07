from muffin.pan import Alt, Cat, Exactly, Null, Red


fs = frozenset


def Optional(l):
    """
    Match either the given language, or the null string.
    """

    return Alt(fs([l, Null(fs())]))


def String(s):
    """
    Match every member of the string in turn, returning the entire string.
    """

    if not s:
        return Null(fs())
    parser = Exactly(s[0])
    for c in s[1:]:
        parser = Cat(parser, Exactly(c))
    return Red(parser, lambda _: s)
