import string

from muffin.cups import All, Any, String
from muffin.pan import Alt, Cat, Ex, Set, rec, tie


# Primitives.
digit = Set(string.digits)
digit19 = Set("123456789")

e = Any([Ex("e"), Ex("E"), String("e-"), String("e+"), String("E-"),
         String("E+")])

digits = Alt(digit, Cat(digit, rec("digits")))

exp = Cat(e, digits)

frac = Cat(Ex("."), digits)

int = Any([digit, Cat(digit19, digit), Cat(Ex("-"), digits),
           All([Ex("-"), digit19, digits])])

number = Any([int, Cat(int, frac), Cat(int, exp), All([int, frac, exp])])

#XXX
char = Any([Set(string.letters)])

chars = Alt(char, Cat(char, rec("chars")))

string = Alt(String('""'), All([Ex('"'), chars, Ex('"')]))

value = Any([string, number, rec("obj"), rec("array"), String("true"),
             String("false"), String("null")])

elements = Alt(value, All([value, Ex(","), rec("elements")]))

array = Alt(String("[]"), All([Ex("["), elements, Ex("]")]))

pair = All([string, Ex(":"), value])

members = Alt(pair, All([pair, Ex(","), rec("members")]))

obj = Alt(String("{}"), All([Ex("{"), members, Ex("}")]))


tie(value, {"array": array, "chars": chars, "digits": digits,
            "elements": elements, "members": members, "obj": obj})
