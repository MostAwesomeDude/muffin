from unittest import TestCase

from muffin.basic import String
from muffin.core import parses


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
