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
from muffin.pan import Alt, Cat, Empty, Ex, Red, Rep, Null


fs = frozenset


def Optional(l):
    """
    Match either the given language, or the null string.
    """

    return Alt(l, Null)


def Bracket(bra, ket):
    """
    Generate an object that can be passed a language to bracket that language.

    Parse bra, then the bracketed language, then ket.
    """

    def Bracketed(l):
        """
        Bracket a language.
        """

        def unbracket(xyz):
            x, (y, z) = xyz
            return y

        return Red(Cat(bra, Cat(l, ket)), unbracket)

    return Bracketed


def Sep(l, s):
    """
    Parse a language at least once, with subsequent iterations separated by a
    separator in-between.

    To get a zero-or-more version, use Optional() around this combinator.
    """

    return Red(Cat(l, Rep(Red(Cat(s, l), lambda (x, y): y))),
               lambda (car, cdr): (car,) + cdr if cdr else (car,))


def Any(ls):
    """
    Match any of the given languages.
    """

    if not ls:
        return Empty
    parser = ls[0]
    for l in ls[1:]:
        parser = Alt(parser, l)
    return parser


def All(ls):
    """
    Match all of the given languages, in order.
    """

    if not ls:
        return Empty
    parser = ls[0]
    for l in ls[1:]:
        parser = Cat(parser, l)
    return parser


def String(s):
    """
    Match every member of the string in turn, returning the entire string.
    """

    return Red(All(map(Ex, s)), lambda _: s)
