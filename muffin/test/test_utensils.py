from unittest import TestCase

from muffin.utensils import inub

class TestNub(TestCase):

    def test_unique(self):
        i = [1, 2, 3]
        o = list(inub(i))
        self.assertEqual(i, o)

    def test_duplicates(self):
        i = [1, 2, 3, 2, 1, 3]
        o = list(inub(i))
        e = [1, 2, 3]
        self.assertEqual(e, o)

    def test_mix(self):
        i = [1, 2, 3, 2, 1, 3, 4]
        o = list(inub(i))
        e = [1, 2, 3, 4]
        self.assertEqual(e, o)
