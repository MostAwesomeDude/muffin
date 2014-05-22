# Copyright (C) 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from unittest import TestCase

from muffin.pan import derivative, parses, Alt, Any, Empty, Ex, Rep, Set, Term


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

    def test_set_matching(self):
        l = Set("abc")
        c = "c"
        expected = Term(fs(["c"]))
        self.assertEqual(derivative(l, c), expected)

    def test_set_mismatch(self):
        l = Set("abc")
        c = "d"
        expected = Empty
        self.assertEqual(derivative(l, c), expected)

    def test_set_single(self):
        l = Set("a")
        c = "a"
        expected = Term(fs(["a"]))
        self.assertEqual(derivative(l, c), expected)

    def test_set_fail(self):
        l = Set("a")
        c = "b"
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
