# Copyright (C) 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import string

from muffin.cups import All, Any, Sep, String
from muffin.pan import Alt, Cat, Ex, Red, Rep, Set, rec, tie


def OneOrMore(l):
    """
    Match one or more of the given language.
    """

    return Red(Cat(l, Rep(l)),
               lambda (car, cdr): (car,) + cdr if cdr else (car,))


# Primitives.
digit = Set(string.digits)
digit19 = Set("123456789")

e = Any([Ex("e"), Ex("E"), String("e-"), String("e+"), String("E-"),
         String("E+")])

digits = OneOrMore(digit)

exp = Cat(e, digits)

frac = Cat(Ex("."), digits)

int = Any([digit, Cat(digit19, digit), Cat(Ex("-"), digits),
           All([Ex("-"), digit19, digits])])

number = Any([int, Cat(int, frac), Cat(int, exp), All([int, frac, exp])])

#XXX
char = Any([Set(string.letters)])

chars = OneOrMore(char)

string = Alt(String('""'), All([Ex('"'), chars, Ex('"')]))

value = Any([string, number, rec("obj"), rec("array"), String("true"),
             String("false"), String("null")])

elements = Sep(value, Ex(","))

array = Alt(String("[]"), All([Ex("["), elements, Ex("]")]))

pair = All([string, Ex(":"), value])

members = Sep(pair, Ex(","))

obj = Alt(String("{}"), All([Ex("{"), members, Ex("}")]))


tie(value, {"array": array, "obj": obj})
