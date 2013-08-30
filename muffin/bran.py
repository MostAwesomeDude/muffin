from muffin.cups import Any, Bracket
from muffin.pan import Cat, Ex, Rep, Set


char = Set("abcdefhijklmnopqrstuvwxyz")

charset = Bracket(Ex("["), Ex("]"))(char)

inverted = Bracket(Cat(Ex("["), Ex("^")), Ex("]"))(char)

expr = Rep(Any([char, charset, inverted]))
