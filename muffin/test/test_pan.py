from unittest import TestCase

from muffin.pan import compact, derivative, Alt, Any, Empty, Exactly, Term


fs = frozenset


class TestDerivative(TestCase):

    def test_any(self):
        l = Any
        c = "c"
        expected = Term(fs(["c"]))
        self.assertEqual(derivative(l, c), expected)

    def test_exactly_matching(self):
        l = Exactly("c")
        c = "c"
        expected = Term(fs(["c"]))
        self.assertEqual(derivative(l, c), expected)

    def test_exactly_mismatch(self):
        l = Exactly("c")
        c = "d"
        expected = Empty
        self.assertEqual(derivative(l, c), expected)

    def test_alt_many_matching(self):
        l = Alt(Exactly("a"), Exactly("b"))
        c = "a"
        expected = Alt(Term(fs(["a"])), Empty)
        self.assertEqual(derivative(l, c), expected)


class TestCompact(TestCase):

    def test_alt_many_empty(self):
        l = Alt(Term(fs(["a"])), Alt(Empty, Empty))
        expected = Term(fs(["a"]))
        self.assertEqual(compact(l), expected)

    def test_alt_some_empty(self):
        l = Alt(Term(fs(["a"])), Alt(Term(fs(["b"])), Empty))
        expected = Alt(Term(fs(["a"])), Term(fs(["b"])))
        self.assertEqual(compact(l), expected)
