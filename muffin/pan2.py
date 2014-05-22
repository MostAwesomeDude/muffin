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
from collections import defaultdict
from functools import wraps

from pretty import pretty

from muffin.pan import Empty, Null


class NT(object):
    """
    A symbol for a sequence of terminals and nonterminals.
    """

    chars = ()

    def __init__(self, name):
        self.name = name

    __repr__ = pretty

    def __pretty__(self, p, cycle):
        p.text(self.name + "".join(self.chars))

    def __hash__(self):
        return hash((self.name, self.chars))

    def __eq__(self, other):
        if not isinstance(other, NT):
            return False
        return self.name == other.name and self.chars == other.chars

    def derivative(self, c):
        n = NT(self.name)
        n.chars = self.chars + (c,)
        return n


def alphabet(g):
    a = set()
    for chains in g.itervalues():
        for chain in chains:
            for item in chain:
                if not isinstance(item, NT):
                    a.add(item)
    return a


def nonterminals(g):
    return set(g)


def rewrite_chains(f):
    @wraps(f)
    def inner(g):
        for nt, chains in g.items():
            chains = f(chains)
            if chains is None:
                del g[nt]
            else:
                g[nt] = chains
    return inner


@rewrite_chains
def remove_empty_rules(chains):
    return chains or None


@rewrite_chains
def remove_empty_chains(chains):
    return [chain for chain in chains if chain != (Empty,)]


@rewrite_chains
def dedupe_chains(chains):
    return list(set(chains))


def strip_null_chain(chain):
    for i, rule in enumerate(chain):
        if rule is not Null:
            break
    return chain[i:]


@rewrite_chains
def strip_nulls(chains):
    rv = set()
    for chain in chains:
        rv.add(strip_null_chain(chain))
    return list(rv)


def heads(g, nt):
    return set(chain[0] for chain in g[nt] if chain)


def derive(x, c):
    if isinstance(x, NT):
        return x.derivative(c)
    else:
        if x == c:
            return Null
        else:
            return Empty


def derivative(g, n0, c):
    seen = set()
    stack = [n0]
    d = defaultdict(list)
    while stack:
        nt = stack.pop()
        prime = nt.derivative(c)
        if prime in seen:
            continue
        seen.add(prime)
        chains = g[nt]

        for chain in chains:
            for rule in chain:
                if rule in nonterminals(g):
                    stack.append(rule)

            chain = strip_null_chain(chain)
            if chain:
                chain = [derive(chain[0], n0)] + chain[1:]
                d[prime].append(chain)
    return dict(d)


def is_null(g, nt):
    """
    Calculate nullability of a single non-terminal.
    """

    if not isinstance(nt, NT):
        return nt is Null

    # Heads with no rules can't possibly be null.
    if nt not in g:
        return False

    heads = set()

    chains = g[nt]
    for chain in chains:
        chain = strip_nulls(chain)
        if len(chain) == 1 and chain[0] is Null:
            return True
        elif isinstance(chain[0], NT):
            heads.add(chain[0])

    return any(is_null(x) for x in heads)


def nullable(self):
    return self.is_null(self.n0)
