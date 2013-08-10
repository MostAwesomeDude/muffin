from muffin.pan import Alt, Cat, Ex, Rep


char = Alt((Ex("a"), Ex("b")))

charset = Cat(Ex("["), Cat(Rep(char), Ex("]")))

expr = Rep(Alt((char, charset)))
