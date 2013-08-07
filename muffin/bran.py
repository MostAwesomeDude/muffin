from muffin.core import Alt, Cat, Exactly, Rep


char = Alt((Exactly("a"), Exactly("b")))

charset = Cat(Exactly("["), Cat(Rep(char), Exactly("]")))

expr = Rep(Alt((char, charset)))
