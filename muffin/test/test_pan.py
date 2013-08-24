from unittest import TestCase

from muffin.pan import derivative, parses, Alt, Any, Empty, Ex, Rep, Term


fs = frozenset


class TestDerivative(TestCase):

    def test_any(self):
        l = Any
        c = "c"
        expected = Term(fs(["c"]))
        self.assertEqual(derivative(l, c), expected)

    def test_exactly_matching(self):
        l = Ex("c")
        c = "c"
        expected = Term(fs(["c"]))
        self.assertEqual(derivative(l, c), expected)

    def test_exactly_mismatch(self):
        l = Ex("c")
        c = "d"
        expected = Empty
        self.assertEqual(derivative(l, c), expected)

    def test_alt_many_matching(self):
        l = Alt(Ex("a"), Ex("b"))
        c = "a"
        expected = Term(fs(["a"]))
        self.assertEqual(derivative(l, c), expected)


class TestParse(TestCase):

    def test_repeat(self):
        l = Rep(Ex("a"))
        i = "aaa"
        e = fs([("a", "a", "a")])
        self.assertEqual(parses(l, i), e)
