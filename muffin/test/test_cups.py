from unittest import TestCase

from muffin.cups import Optional, String
from muffin.pan import parses, Cat, Ex


class TestOptional(TestCase):

    def test_yes_leading(self):
        l = Cat(Optional(Ex("a")), Ex("b"))
        i = "ab"
        e = set(["ab"])
        self.assertEqual(parses(l, i), e)

    def test_no_leading(self):
        l = Cat(Optional(Ex("a")), Ex("b"))
        i = "b"
        e = set(["b"])
        self.assertEqual(parses(l, i), e)

    def test_yes_trailing(self):
        l = Cat(Ex("a"), Optional(Ex("b")))
        i = "ab"
        e = set(["ab"])
        self.assertEqual(parses(l, i), e)

    def test_no_trailing(self):
        l = Cat(Ex("a"), Optional(Ex("b")))
        i = "a"
        e = set(["a"])
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
