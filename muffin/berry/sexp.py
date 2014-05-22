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

acceptable = string.letters + string.digits + "!@#$%^&*"

character = Set(acceptable)
name = Red(OneOrMore(character), lambda cs: "".join(cs))
obj = Alt(rec("sexp"), name)
whitespace = Red(OneOrMore(Ex(" ")), lambda _: None)
contents = Sep(obj, whitespace)

sexp = Red(All([po, contents, pc]), lambda ((_, objs), __): tuple(objs))

tie(obj, {"sexp": sexp})
