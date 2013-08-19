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


def derive(x, c):
    if isinstance(x, NT):
        return x.increment()
    else:
        if x == c:
            return Null
        else:
            return Empty


class Grammar(object):
    """
    A context-free grammar.
    """

    def __init__(self, alphabet, nonterminals, rules, entry):
        self.a = set(alphabet)
        self.n = set(nonterminals)
        self.r = rules
        self.n0 = entry

    __repr__ = pretty

    def __pretty__(self, p, cycle):
        if cycle:
            p.text("Grammar(...)")
            return

        with p.group(1, "Grammar(", ")"):
            p.pretty(self.a)
            p.text(",")
            p.breakable()

            p.pretty(self.n)
            p.text(",")
            p.breakable()

            p.pretty(self.r)
            p.text(",")
            p.breakable()

            p.pretty(self.n0)

    def heads(self, nt):
        if nt in self.r:
            return set([chain[0] for chain in self.r[nt]])
        return set()

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
                chain = [derive(chain[0], c)] + chain[1:]
                self.r[prime].append(chain)
        self.n |= seen
        self.n0 = self.n0.increment()

    def is_null(self, nt):
        """
        Calculate nullability of a single non-terminal.
        """

        heads = set()

        chains = self.r[nt]
        for chain in chains:
            if len(chain) == 1 and chain[0] is Null:
                return True
            elif isinstance(chain[0], NT):
                heads.add(chain[0])

        return any(self.is_null(x) for x in heads)

    def nullable(self):
        return self.is_null(self.n0)
