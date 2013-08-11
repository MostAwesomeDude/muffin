from unittest import TestCase

from muffin.cups import AnyOf, Optional, String
from muffin.pan import matches, parses, Cat, Ex


fs = frozenset


class TestOptional(TestCase):

    def test_yes_leading(self):
        l = Cat(Optional(Ex("a")), Ex("b"))
        i = "ab"
        e = set([("a", "b")])
        self.assertEqual(parses(l, i), e)

    def test_no_leading(self):
        l = Cat(Optional(Ex("a")), Ex("b"))
        i = "b"
        e = set([(None, "b")])
        self.assertEqual(parses(l, i), e)

    def test_yes_trailing(self):
        l = Cat(Ex("a"), Optional(Ex("b")))
        i = "ab"
        e = set([("a", "b")])
        self.assertEqual(parses(l, i), e)

    def test_no_trailing(self):
        l = Cat(Ex("a"), Optional(Ex("b")))
        i = "a"
        e = set([("a", None)])
        self.assertEqual(parses(l, i), e)


class TestString(TestCase):

    def test_char(self):
        l = String("a")
        i = "a"
        e = set(["a"])
        self.assertEqual(parses(l, i), e)

    def test_char_fail(self):
        l = String("a")
        i = "b"
        e = set()
        self.assertEqual(parses(l, i), e)

    def test_string(self):
        l = String("abc")
        i = "abc"
        e = set(["abc"])
        self.assertEqual(parses(l, i), e)

    def test_string_fail_first(self):
        l = String("abc")
        i = "dbc"
        e = set()
        self.assertEqual(parses(l, i), e)

    def test_string_fail_last(self):
        l = String("abc")
        i = "abd"
        e = set()
        self.assertEqual(parses(l, i), e)


class TestAnyOf(TestCase):

    def test_single(self):
        l = AnyOf("a")
        i = "a"
        e = fs(["a"])
        self.assertEqual(parses(l, i), e)

    def test_single_fail(self):
        l = AnyOf("a")
        i = "b"
        self.assertFalse(matches(l, i))

    def test_multiple(self):
        l = AnyOf("abc")
        i = "b"
        e = fs(["b"])
        self.assertEqual(parses(l, i), e)
