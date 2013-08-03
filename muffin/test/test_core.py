from unittest import TestCase

from muffin.core import derivative, Empty, Exactly, Null


class TestDerivative(TestCase):

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
