import string

from muffin.cups import All, Sep
from muffin.pan import Alt, Cat, Ex, Red, Rep, Set, rec, tie


def OneOrMore(l):
    """
    Match one or more of the given language.
    """

    return Red(Cat(l, Rep(l)),
               lambda (car, cdr): (car,) + cdr if cdr else (car,))


po = Ex("(")
pc = Ex(")")

character = Set(string.letters + string.digits + string.punctuation)
name = OneOrMore(character)
obj = Alt(rec("sexp"), name)
whitespace = Red(OneOrMore(Ex(" ")), lambda _: None)
contents = Sep(obj, whitespace)

sexp = All([po, contents, pc])

tie(obj, {"sexp": sexp})
