from muffin.cups import Any
from muffin.pan import Alt, Cat, Ex, Red, Rep, Set


BC, BO, COLON, SC, SO, PC, PO, SEMICOLON = range(8)


def Token(l, token):
    """
    Produce a token upon matching a language.
    """

    return Red(l, lambda _: token)


colon = Token(Ex(":"), COLON)
bc = Token(Ex("}"), BC)
bo = Token(Ex("{"), BO)
sc = Token(Ex("]"), SC)
so = Token(Ex("["), SO)
pc = Token(Ex(")"), PC)
po = Token(Ex("("), PO)
semicolon = Token(Ex(";"), SEMICOLON)


digit = Set("1234567890")
alpha = Set("abcdefhijklmnopqrstuvwxyzABCDEFHIJKLMNOPQRSTUVWXYZ")
alphanum = Alt(alpha, digit)
identifier = Cat(alpha, Rep(alphanum))


python = Rep(Any([
    colon, semicolon,
    bc, bo, sc, so, pc, po,
    identifier,
]))