#!/usr/bin/env python
"""This module has new tests for the pvl decoder functions."""

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
from unittest.mock import patch

from pvl import decoder


class TestParse(unittest.TestCase):

    def setUp(self):
        self.d = decoder.PVLDecoder()

    def test_has_whitespace(self):
        self.assertTrue(self.d.has_whitespace(' Starts with a space.', 0))
        self.assertTrue(self.d.has_whitespace('\nStarts with a newline.', 0))
        self.assertTrue(self.d.has_whitespace('Space at index.', 5))
        self.assertFalse(self.d.has_whitespace('Does not starts with a space.',
                                               0))

    def test_skip_whitespace(self):
        self.assertEqual(1, self.d.skip_whitespace(' Starts with a space.', 0))
        self.assertEqual(0, self.d.skip_whitespace('Does not.', 0))
        self.assertEqual(2, self.d.skip_whitespace(' \nMore complicated.', 0))

    def test_has_line_comment(self):
        self.assertTrue(self.d.has_line_comment('# This is a comment.', 0))
        self.assertFalse(self.d.has_line_comment('% This is not.', 0))

    def test_has_multiline_comment(self):
        self.assertTrue(self.d.has_multiline_comment('/* This is a comment.',
                                                     0))
        self.assertFalse(self.d.has_multiline_comment('# This is not multi.',
                                                      0))

    def test_skip_comment(self):
        self.assertEqual(10, self.d.skip_comment('# Comment\nParse more.', 0))
        self.assertEqual(19, self.d.skip_comment('/* This\nis\nmulti */Parse',
                                                 0))

    def test_skip_whitespace_or_comment(self):
        self.assertEqual(0, self.d.skip_whitespace_or_comment('No comment.',
                                                              0))
        c = '# Comment\n/* Multi\nline */ Parse'
        #    0123456789 012345678 9012345678901
        #               1          2         3
        # len(c) = 32
        self.assertEqual(27, self.d.skip_whitespace_or_comment(c, 0))

    def test_has_eof(self):
        self.assertEqual(12, self.d.has_eof('Out of index', 12))
        self.assertIsNone(self.d.has_eof('Out of index', 0))
        self.assertEqual(1, self.d.has_eof('\0', 0))

    def test_has_end(self):
        self.assertFalse(self.d.has_end('No End here.', 0))
        self.assertTrue(self.d.has_end('End here.', 0))
        self.assertTrue(self.d.has_end('End', 0))
        self.assertTrue(self.d.has_end('End/* Really */', 0))
        self.assertTrue(self.d.has_end('End;', 0))
        self.assertTrue(self.d.has_end('\0', 0))

    def test_has_end_group(self):
        self.assertFalse(self.d.has_end_group('No End here.', 0))
        self.assertTrue(self.d.has_end_group('End_Group', 0))

    def test_ensure_assignment(self):
        self.assertEqual(3, self.d.ensure_assignment(' = ', 0))
        self.assertEqual(3, self.d.ensure_assignment(' = ', 1))
        self.assertEqual(1, self.d.ensure_assignment('=', 0))
        self.assertRaises(decoder.DecodeError,
                          self.d.ensure_assignment, 'Nope', 0)

    def test_has_delimiter(self):
        self.assertTrue(self.d.has_delimiter('\0'))
        self.assertTrue(self.d.has_delimiter('#'))
        self.assertTrue(self.d.has_delimiter('/*'))
        self.assertTrue(self.d.has_delimiter('&'))
        self.assertFalse(self.d.has_delimiter('A'))

    def test_next_token(self):
        self.assertEqual('Token', self.d.next_token('Token', 0))
        self.assertEqual('Token', self.d.next_token('Token = value', 0))
        self.assertEqual('Token', self.d.next_token('Token# Comment', 0))
        self.assertRaises(decoder.DecodeError,
                          self.d.next_token, ' Token', 0)

    def test_skip_statement_delimiter(self):
        self.assertEqual(0, self.d.skip_statement_delimiter('No delim', 0))
        self.assertEqual(1, self.d.skip_statement_delimiter('; After delim', 0))
        self.assertEqual(2, self.d.skip_statement_delimiter(' ; after', 0))

    def test_expect_in(self):
        self.assertEqual(2, self.d.expect_in('AaBb', 0, ('Aa', 'Bbb'), 'foo'))
        self.assertEqual(3, self.d.expect_in('BbbAa', 0, ('Aa', 'Bbb'), 'foo'))
        self.assertRaises(decoder.DecodeError,
                          self.d.expect_in, 'No Tokens', 0, ('A', 'B'), 'foo')

    def test_parse_end_assignment(self):
        self.assertEqual(5, self.d.parse_end_assignment('=Name', 0, 'Name'))
        self.assertEqual(1, self.d.parse_end_assignment(' Next', 0, 'Name'))
        self.assertRaises(decoder.DecodeError,
                          self.d.parse_end_assignment, '= Foo', 0, 'Name')

    def test_has_end_object(self):
        self.assertFalse(self.d.has_end_object('No End here.', 0))
        self.assertTrue(self.d.has_end_object('End_Object', 0))

    def test_broken_assignment(self):
        self.assertRaises(decoder.DecodeError,
                          self.d.broken_assignment, 'foo', 0)

        self.d.strict = False
        empty = decoder.EmptyValueAtLine(1)
        self.assertEqual(empty, self.d.broken_assignment('foo', 0))

    def test_parse_iterable(self):
        def pv(s, idx):
            (t, _, _) = s[idx:-1].partition(',')
            v = t.strip()
            i = s.find(v, idx)
            return v, i + len(v)

        with patch('pvl.decoder.PVLDecoder.parse_value', side_effect=pv):
            i = '( a, b, c, d )'
            v = ['a', 'b', 'c', 'd']
            self.assertEqual((v, len(i)),
                             self.d.parse_iterable(i, 0, '(', ')'))

    def test_unescape_next_char(self):
        self.assertEqual(('"', 1), self.d.unescape_next_char('"', 0))
        self.assertEqual(('\n', 1), self.d.unescape_next_char('n', 0))
        self.assertRaises(decoder.DecodeError,
                          self.d.unescape_next_char, 'i', 0)

    def test_parse_quoted_string(self):
        self.assertEqual(('Quoted', 8),
                         self.d.parse_quoted_string('"Quoted"', 0))
        self.assertEqual(('He said, "hello"', 18),
                         self.d.parse_quoted_string("'He said, \"hello\"'", 0))
        self.assertEqual(('He said, "hello"', 20),
                         self.d.parse_quoted_string(r"'He said, \"hello\"'", 0))
        self.assertEqual(('No\tin Python', 15),
                         self.d.parse_quoted_string(r"'No\tin Python'", 0))
        self.assertEqual(('Line Continued', 19),
                         self.d.parse_quoted_string("'Line -\n Continued'", 0))

    # def test_parse_simple_value(self)

    # def test_parse_value(self):
    #     pass

    # def test_parse_assignment(self):
    #     pass

    # def test_parse_aggregation(self):
    #     # test for Group and Object
    #     pass

    # def test_parse_statement(self):
    #     pass

    # def test_parse_block(self):
    #     pass

    # def test_decode(self):
