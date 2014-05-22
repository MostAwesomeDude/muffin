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
from muffin.pan import matches, parses, tie, Alt, Cat, Ex, Lazy, Null, Patch
from muffin.utensils import const

S = Alt(Ex("N"), Cat(Lazy(const, Patch), Cat(Ex("+"), Lazy(const, Patch))))
tie(S)


def runS():
    s = "N" + "+N" * 10
    print matches(S, s)
    s = "N" + "+N" * 9 + "++N"
    print matches(S, s)


B = Alt(Null,
        Cat(Lazy(const, Patch), Cat(Ex("("), Cat(Lazy(const, Patch),
            Ex(")")))))
tie(B)


def runBs():
    s = "()"
    print matches(B, s)
    print parses(B, s)


def runB():
    s = "(())(())"
    print matches(B, s)
    print parses(B, s)
    s = "(((())))"
    print matches(B, s)
    print parses(B, s)
