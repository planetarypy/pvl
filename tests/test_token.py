#!/usr/bin/env python
"""This module has tests for the pvl lang functions."""

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

import unittest

from pvl.grammar import PVLGrammar
from pvl.decoder import PVLDecoder
from pvl.token import Token


class TestToken(unittest.TestCase):
    def test_init(self):
        s = "token"
        self.assertEqual(s, Token(s))
        self.assertEqual(s, Token(s, grammar=PVLGrammar()))
        self.assertEqual(s, Token(s, decoder=PVLDecoder()))
        self.assertRaises(TypeError, Token, s, grammar="not a grammar")
        self.assertRaises(
            TypeError, Token, s, grammar=PVLGrammar(), decoder="not a decoder"
        )

    def test_is_comment(self):
        c = Token("/* comment */")
        self.assertTrue(c.is_comment())

        n = Token("not comment */")
        self.assertFalse(n.is_comment())

    def test_is_begin_aggregation(self):
        for s in ("BEGIN_GROUP", "Begin_Group", "ObJeCt"):
            with self.subTest(string=s):
                t = Token(s)
                self.assertTrue(t.is_begin_aggregation())

        b = Token("END_GROUP")
        self.assertFalse(b.is_begin_aggregation())

    def test_is_end_statement(self):
        t = Token("END")
        self.assertTrue(t.is_end_statement())

        t = Token("Start")
        self.assertFalse(t.is_end_statement())

    def test_is_datetime(self):
        for s in (
            "2001-027T23:45",
            "2001-01-01T01:34Z",
            "01:42:57Z",
            "23:45",
            "01:42:57",
            "12:34:56.789",
            "2001-01-01",
            "2001-027",
        ):
            with self.subTest(string=s):
                t = Token(s)
                self.assertTrue(t.is_datetime())

        for s in ("3:450", "frank"):
            with self.subTest(string=s):
                t = Token(s)
                self.assertFalse(t.is_datetime())

    def test_is_parameter_name(self):
        for s in ("Hello", "ProductId"):
            with self.subTest(string=s):
                t = Token(s)
                self.assertTrue(t.is_parameter_name())

        for s in ("Group", "/*comment*/", "2001-027"):
            with self.subTest(string=s):
                t = Token(s)
                self.assertFalse(t.is_parameter_name())

    def test_is_decimal(self):
        for s in (
            "125",
            "+211109",
            "-79",  # Integers
            "69.35",
            "+12456.345",
            "-0.23456",
            ".05",
            "-7.",  # Floating
            "-2.345678E12",
            "1.567E-10",
            "+4.99E+3",
        ):  # Exponential
            with self.subTest(string=s):
                t = Token(s)
                self.assertTrue(t.is_decimal())

        for s in ("2#0101#", "frank"):
            with self.subTest(string=s):
                t = Token(s)
                self.assertFalse(t.is_decimal())

    def test_is_binary(self):
        for s in ("2#0101#", "+2#0101#", "-2#0101#"):
            with self.subTest(string=s):
                t = Token(s)
                # self.assertTrue(t.is_binary())
                self.assertTrue(t.is_non_decimal())

        # for s in ('+211109', 'echo', '+8#0156#'):
        for s in ("+211109", "echo"):
            with self.subTest(string=s):
                t = Token(s)
                self.assertFalse(t.is_non_decimal())

    def test_is_octal(self):
        for s in ("8#0107#", "+8#0156#", "-8#0134#"):
            with self.subTest(string=s):
                t = Token(s)
                # self.assertTrue(t.is_octal())
                self.assertTrue(t.is_non_decimal())

        # for s in ('+211109', 'echo', '2#0101#'):
        #     with self.subTest(string=s):
        #         t = Token(s)
        #         self.assertFalse(t.is_octal())

    def test_is_hex(self):
        for s in ("16#100A#", "+16#23Bc#", "-16#98ef#"):
            with self.subTest(string=s):
                t = Token(s)
                # self.assertTrue(t.is_hex())
                self.assertTrue(t.is_non_decimal())

        # for s in ('+211109', 'echo', '2#0101#', '8#0107#'):
        #     with self.subTest(string=s):
        #         t = Token(s)
        #         self.assertFalse(t.is_hex())

    def test_isnumeric(self):
        for s in (
            "125",
            "+211109",
            "-79",  # Integers
            "69.35",
            "+12456.345",
            "-0.23456",
            ".05",
            "-7.",  # Floating
            "-2.345678E12",
            "1.567E-10",
            "+4.99E+3",  # Exponential
            "2#0101#",
            "+2#0101#",
            "-2#0101#",  # Binary
            "8#0107#",
            "+8#0156#",
            "-8#0134#",  # Octal
            "16#100A#",
            "+16#23Bc#",
            "-16#98ef#",
        ):  # Hex
            with self.subTest(string=s):
                t = Token(s)
                self.assertTrue(t.isnumeric())

        for s in ("frank", "#", "-apple"):
            with self.subTest(string=s):
                t = Token(s)
                self.assertFalse(t.isnumeric())

    def test_is_space(self):
        for s in ("  ", "\t\n"):
            with self.subTest(string=s):
                t = Token(s)
                self.assertTrue(t.is_space())
                self.assertTrue(t.isspace())

        for s in ("not space", ""):
            with self.subTest(string=s):
                t = Token(s)
                self.assertFalse(t.is_space())

    def test_is_WSC(self):
        for s in (" /*com*/  ", "/*c1*/\n/*c2*/", " "):
            with self.subTest(string=s):
                t = Token(s)
                self.assertTrue(t.is_WSC())

        for s in (" /*com*/ not comment", " surrounding "):
            with self.subTest(string=s):
                t = Token(s)
                self.assertFalse(t.is_WSC())

    def test_is_delimiter(self):
        t = Token(";")
        self.assertTrue(t.is_delimiter())

        t = Token("not")
        self.assertFalse(t.is_delimiter())

    def test_is_quote(self):
        for s in ('"', "'"):
            with self.subTest(string=s):
                t = Token(s)
                self.assertTrue(t.is_quote())

        t = Token("not a quote mark")
        self.assertFalse(t.is_quote())

    def test_is_unquoted_string(self):
        for s in ("Hello", "Product", "Group"):
            with self.subTest(string=s):
                t = Token(s)
                self.assertTrue(t.is_unquoted_string())

        for s in (
            "/*comment*/",
            "second line of comment*/",
            "2001-027",
            '"quoted"',
            "\t"
        ):
            with self.subTest(string=s):
                t = Token(s)
                self.assertFalse(t.is_unquoted_string())

    def test_is_quoted_string(self):
        for s in ('"Hello &"', "'Product Id'", '""'):
            with self.subTest(string=s):
                t = Token(s)
                self.assertTrue(t.is_quoted_string())

        for s in ("/*comment*/", "2001-027", '"'):
            with self.subTest(string=s):
                t = Token(s)
                self.assertFalse(t.is_quoted_string())

    def test_is_string(self):
        for s in (
            '"Hello &"',
            "'Product Id'",
            '""',
            "Hello",
            "Product",
            "Group",
        ):
            with self.subTest(string=s):
                t = Token(s)
                self.assertTrue(t.is_string())

        for s in ("/*comment*/", "2001-027", '"'):
            with self.subTest(string=s):
                t = Token(s)
                self.assertFalse(t.is_string())

    def test_is_simple_value(self):
        for s in (
            '"Hello &"',
            "'Product Id'",
            '""',  # Quoted Strings
            "Hello",
            "Group" "2001-01-01",  # Unquoted Strings
            "2001-027",  # Date
            "23:45",
            "01:42:57",
            "12:34:56.789" "2001-027T23:45",  # Time
            "2001-01-01T01:34Z",  # Datetime
            "125",
            "+211109",
            "-79",  # Integers
            "69.35",
            "+12456.345",
            "-0.23456",
            ".05",
            "-7.",  # Floating
            "-2.345678E12",
            "1.567E-10",
            "+4.99E+3",  # Exponential
            "2#0101#",
            "+2#0101#",
            "-2#0101#",  # Binary
            "8#0107#",
            "+8#0156#",
            "-8#0134#",  # Octal
            "16#100A#",
            "+16#23Bc#",
            "-16#98ef#",
        ):  # Hex
            with self.subTest(string=s):
                t = Token(s)
                self.assertTrue(t.is_simple_value())

        for s in ("/*comment*/", "=", '"', "{", "(", "Product Id"):
            with self.subTest(string=s):
                t = Token(s)
                self.assertFalse(t.is_simple_value())

    def test_split(self):
        s = "Hello Bob"
        t = Token(s)
        t_list = t.split()
        for x in t_list:
            with self.subTest(token=x):
                self.assertIsInstance(x, Token)

    def test_index(self):
        s = "3"
        t = Token(s)
        self.assertEqual(3, int(t))
        self.assertEqual(3, t.__index__())
        self.assertRaises(ValueError, Token("3.4").__index__)
        self.assertRaises(ValueError, Token("a").__index__)

    def test_float(self):
        s = "3.14"
        t = Token(s)
        self.assertEqual(3.14, float(t))

    def test_lstrip(self):
        s = "  leftward space "
        t = Token(s)
        self.assertEqual("leftward space ", t.lstrip())

    def test_rstrip(self):
        s = " rightward space  "
        t = Token(s)
        self.assertEqual(" rightward space", t.rstrip())