from muffin.cups import Any, AnyOf, Bracket
from muffin.pan import Cat, Ex, Rep


# char = AnyOf("abcdefhijklmnopqrstuvwxyz")
char = AnyOf("abc")

charset = Bracket(Ex("["), Ex("]"))(char)

inverted = Bracket(Cat(Ex("["), Ex("^")), Ex("]"))(char)

expr = Rep(Any([char, charset, inverted]))
