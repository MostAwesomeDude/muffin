from muffin.core import Cat, Exactly, Null, Red


def String(s):
    """
    Match every member of the string in turn, returning the entire string.
    """

    if not s:
        return Null(frozenset())
    parser = Exactly(s[0])
    for c in s[1:]:
        parser = Cat(parser, Exactly(c))
    return Red(parser, lambda _: s)
