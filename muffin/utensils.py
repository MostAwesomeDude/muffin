def const(x):
    return x


def compose(f, g):
    def h(x):
        return g(f(x))
    return h


def curry_first(x):
    def first(y):
        return x, y
    return first


def curry_second(x):
    def second(y):
        return y, x
    return second
