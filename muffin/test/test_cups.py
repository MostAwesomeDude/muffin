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

from muffin.cups import Optional, Sep, String
from muffin.pan import parses, Cat, Ex


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


class TestSep(TestCase):

    def test_one(self):
        l = Sep(Ex("a"), Ex(","))
        i = "a"
        e = fs([("a",)])
        self.assertEqual(parses(l, i), e)

    def test_two(self):
        l = Sep(Ex("a"), Ex(","))
        i = "a,a"
        e = fs([("a", "a")])
        self.assertEqual(parses(l, i), e)

    def test_three(self):
        l = Sep(Ex("a"), Ex(","))
        i = "a,a,a"
        e = fs([("a", "a", "a")])
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
