#!/usr/bin/env python
"""This module has tests for the pvl grammar regexes."""

# Copyright 2019, Ross A. Beyer (rbeyer@seti.org)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import unittest

from pvl.grammar import PVLGrammar, ODLGrammar


class TestLeapSeconds(unittest.TestCase):
    def setUp(self):
        self.g = PVLGrammar()

    def test_H_frag(self):
        for s in ("00", "05", "10", "19", "23"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._H_frag, s)
                self.assertEqual(s, m.groupdict()["hour"])

    def test_M_frag(self):
        for s in ("00", "05", "10", "19", "23", "59"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._M_frag, s)
                self.assertEqual(s, m.groupdict()["minute"])

    def test_f_frag(self):
        for s in (".1", ".123", ".789"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._f_frag, s)
                self.assertEqual(s[1:], m.groupdict()["microsecond"])
        for s in ("1", "", "abc"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._f_frag, s)
                self.assertEqual(None, m)

    def test_Y_frag(self):
        for s in ("0001", "1985", "9999"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._Y_frag, s)
                self.assertEqual(s, m.groupdict()["year"])
        for s in ("0000", "10000", "abc"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._Y_frag, s)
                self.assertEqual(None, m)

    def test_m_frag(self):
        for s in ("01", "04", "11", "12"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._m_frag, s)
                self.assertEqual(s, m.groupdict()["month"])
        for s in ("1", "00", "abc"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._m_frag, s)
                self.assertEqual(None, m)

    def test_d_frag(self):
        for s in ("01", "10", "28", "31"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._d_frag, s)
                self.assertEqual(s, m.groupdict()["day"])
        for s in ("1", "00", "32"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._d_frag, s)
                self.assertEqual(None, m)

    def test_j_frag(self):
        for s in ("001", "123", "234", "366"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._j_frag, s)
                self.assertEqual(s, m.groupdict()["doy"])
        for s in ("1", "30", "367"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._j_frag, s)
                self.assertEqual(None, m)

    def test_Ymd_frag(self):
        for s in ("2001-01-01", "2019-12-04"):
            with self.subTest(string=s):
                self.assertIsNotNone(re.fullmatch(self.g._Ymd_frag, s))
        for s in ("2001-1-1", "2019-12-00"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._Ymd_frag, s)
                self.assertEqual(None, m)

    def test_Yj_frag(self):
        for s in ("2001-001", "2019-180"):
            with self.subTest(string=s):
                self.assertIsNotNone(re.fullmatch(self.g._Yj_frag, s))
        for s in ("2001-1-1", "2019-367"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._Yj_frag, s)
                self.assertEqual(None, m)

    def test_time_frag(self):
        for s in ("01:02:60", "02:03:60Z", "03:04:60.123", "03:04:60.123Z"):
            with self.subTest(string=s):
                self.assertIsNotNone(re.fullmatch(self.g._time_frag, s))
        for s in ("01:02:59", "23:56"):
            with self.subTest(string=s):
                m = re.fullmatch(self.g._time_frag, s)
                self.assertEqual(None, m)

    def test_leap_second_Ymd_re(self):
        for s in ("2001-12-31T01:59:60.123Z", "01:59:60Z", "01:59:60"):
            with self.subTest(string=s):
                self.assertIsNotNone(self.g.leap_second_Ymd_re.fullmatch(s))

    def test_leap_second_Yj_re(self):
        for s in ("2001-180T01:59:60.123Z", "01:59:60Z", "01:59:60"):
            with self.subTest(string=s):
                self.assertIsNotNone(self.g.leap_second_Yj_re.fullmatch(s))


class TestAllowed(unittest.TestCase):

    def test_allowed(self):
        g = PVLGrammar()
        for c in ("a", "b", " ", "\n"):
            with self.subTest(char=c):
                self.assertTrue(g.char_allowed(c))

        for c in ("\b", chr(127)):
            with self.subTest(char=c):
                self.assertFalse(g.char_allowed(c))

        self.assertRaises(ValueError, g.char_allowed, "too long")

        odlg = ODLGrammar()
        self.assertFalse(odlg.char_allowed("😆"))
