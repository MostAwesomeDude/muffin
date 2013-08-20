from functools import wraps

from pretty import pretty

from muffin.pan import Empty, Null


class NT(object):
    """
    A symbol for a sequence of terminals and nonterminals.
    """

    prime = 0

    def __init__(self, name):
        self.name = name

    __repr__ = pretty

    def __pretty__(self, p, cycle):
        p.text(self.name + "`" * self.prime)

    def __hash__(self):
        return hash((self.name, self.prime))

    def __eq__(self, other):
        if not isinstance(other, NT):
            return False
        return self.name == other.name and self.prime == other.prime

    def increment(self):
        n = NT(self.name)
        n.prime = self.prime + 1
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


@rewrite_chains
def strip_nulls(chains):
    rv = set()
    for chain in chains:
        for i, rule in enumerate(chain):
            if rule is not Null:
                break
        rv.add(chain[i:])
    return list(rv)


def heads(g, nt):
    return set(chain[0] for chain in g[nt] if chain)


def derive(self, x, c):
    if isinstance(x, NT):
        return x.increment()
    else:
        if x == c:
            return Null
        else:
            return Empty

def derivative(self, c):
    seen = set()
    stack = [self.n0]
    while stack:
        nt = stack.pop()
        prime = nt.increment()
        if prime in seen:
            continue
        seen.add(prime)
        chains = self.r[nt]
        if chains:
            self.r.setdefault(prime, [])
        for chain in chains:
            for rule in chain:
                if rule in self.n:
                    stack.append(rule)

            chain = self.strip_nulls(chain)
            if chain:
                chain = [self.derive(chain[0], c)] + chain[1:]
            else:
                chain = Empty,
            self.r[prime].append(chain)
    self.n |= seen
    self.n0 = self.n0.increment()

def prune_empty(self):
    """
    Remove any empty rules.
    """

    changed = True
    while changed:
        dropped = set()
        changed = False

        for head, chains in self.r.iteritems():
            chains = [chain for chain in chains if Empty not in chain]
            if not chains:
                dropped.add(head)
            else:
                self.r[head] = chains

        for nt in dropped:
            del self.r[nt]
            self.n.discard(nt)
            changed = True

def is_null(self, nt):
    """
    Calculate nullability of a single non-terminal.
    """

    if not isinstance(nt, NT):
        return nt is Null

    # Heads with no rules can't possibly be null.
    if nt not in self.r:
        return False

    heads = set()

    chains = self.r[nt]
    for chain in chains:
        chain = self.strip_nulls(chain)
        if len(chain) == 1 and chain[0] is Null:
            return True
        elif isinstance(chain[0], NT):
            heads.add(chain[0])

    return any(self.is_null(x) for x in heads)

def nullable(self):
    return self.is_null(self.n0)
