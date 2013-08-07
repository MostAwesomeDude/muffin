from unittest import TestCase

from muffin.pan import compact, derivative, Alt, Any, Empty, Exactly, Null


class TestDerivative(TestCase):

    def test_any(self):
        l = Any
        c = "c"
        expected = Null(frozenset(["c"]))
        self.assertEqual(derivative(l, c), expected)

    def test_exactly_matching(self):
        l = Exactly("c")
        c = "c"
        expected = Null(frozenset(["c"]))
        self.assertEqual(derivative(l, c), expected)

    def test_exactly_mismatch(self):
        l = Exactly("c")
        c = "d"
        expected = Empty
        self.assertEqual(derivative(l, c), expected)

    def test_alt_many_matching(self):
        l = Alt((Exactly("a"), Exactly("b"), Exactly("c")))
        c = "a"
        expected = Alt((Null(frozenset(["a"])), Empty, Empty))
        self.assertEqual(derivative(l, c), expected)


class TestCompact(TestCase):

    def test_alt_many_empty(self):
        l = Alt((Null(frozenset(["a"])), Empty, Empty))
        expected = Null(frozenset(["a"]))
        self.assertEqual(compact(l), expected)

    def test_alt_some_empty(self):
        l = Alt((Null(frozenset(["a"])), Null(frozenset(["b"])), Empty))
        expected = Alt((Null(frozenset(["a"])), Null(frozenset(["b"]))))
        self.assertEqual(compact(l), expected)

    def test_alt_nested(self):
        l = Alt((Null(frozenset(["a"])), Alt((Null(frozenset(["b"])), Empty))))
        expected = Alt((Null(frozenset(["a"])), Null(frozenset(["b"]))))
        self.assertEqual(compact(l), expected)
