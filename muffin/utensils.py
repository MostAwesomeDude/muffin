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
def const(x):
    return x


def compose(f, g):
    def h(x):
        return g(f(x))
    h.__name__ = "compose(%s, %s)" % (f.__name__, g.__name__)
    return h


def curry_first(x):
    def first(y):
        return x, y
    return first


def curry_second(x):
    def second(y):
        return y, x
    return second


def key(args, kwargs):
    return args, frozenset(kwargs.iteritems())


def kleene(bottom):
    """
    Kleene's fixed point.

    Ascend from a bottom value to a recursively-defined value. Usage is
    similar to a general fixed-point combinator, like U, Y, or Z, but with
    memoization and an explicit bottom value. This decorator can thus be used
    to deal with ill-founded recursion, as long as the values involved are
    sufficiently pure; if this decorator sees a value twice under the same
    circumstances, it will "bottom out" and ensure that the computation
    terminates eventually.
    """

    def first(f):
        cache = {}

        def second(x):
            def z(*args, **kwargs):
                k = key(args, kwargs)
                if k in cache:
                    v = cache[k]
                else:
                    cache[k] = bottom
                    v = x(x)(*args, **kwargs)
                    cache[k] = v
                return v
            return f(z)
        return second(second)
    return first


def once(f):
    cache = [None]
    def once(self, g):
        if cache[0] is None:
            cache[0] = f(self, g)
        return cache[0]
    return once


def inub(iterable):
    """
    Go through an iterable, only yielding items that have not been seen yet.

    Uses quadratic time and linear space in exchange for being lazy and not
    using hashing.
    """

    seen = []

    for item in iter(iterable):
        if item not in seen:
            seen.append(item)
            yield item
