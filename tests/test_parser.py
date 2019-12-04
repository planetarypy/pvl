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

from pvl.parser import PVLParser
from pvl.lexer import lexer as Lexer


class TestParse(unittest.TestCase):

    def setUp(self):
        self.p = PVLParser()

    # def test_broken_assignment(self):
    #     self.assertRaises(DecodeError,
    #                       self.d.broken_assignment, 'foo', 0)

    #     self.d.strict = False
    #     empty = EmptyValueAtLine(1)
    #     self.assertEqual(empty, self.d.broken_assignment('foo', 0))

    # def test_parse_iterable(self):
    #     def pv(s, idx):
    #         (t, _, _) = s[idx:-1].partition(',')
    #         v = t.strip()
    #         i = s.find(v, idx)
    #         return v, i + len(v)

    #     with patch('pvl.decoder.PVLDecoder.parse_value', side_effect=pv):
    #         i = '( a, b, c, d )'
    #         v = ['a', 'b', 'c', 'd']
    #         self.assertEqual((v, len(i)),
    #                          self.d.parse_iterable(i, 0, '(', ')'))

    def test_parse_begin_aggregation_statement(self):
        pairs = (('name', 'GROUP = name next'),
                 ('name', 'OBJECT=name next'),
                 ('name', 'BEGIN_GROUP /*c1*/ = /*c2*/ name /*c3*/ next'))
        for x in pairs:
            with self.subTest(pair=x):
                tokens = Lexer(x[1])
                next_t = x[1].split()[-1]
                self.assertEqual((x[0], next_t),
                                 self.p.parse_begin_aggregation_statement(next(tokens),
                                                                          tokens))

        tokens = Lexer('Not-a-Begin-Aggegation-Statement = name')
        self.assertRaises(ValueError,
                          self.p.parse_begin_aggregation_statement,
                          next(tokens), tokens)

        strings = ('GROUP equals name', 'GROUP = 5')
        for s in strings:
            with self.subTest(string=s):
                tokens = Lexer(s)
                self.assertRaises(ValueError,
                                  self.p.parse_begin_aggregation_statement,
                                  next(tokens), tokens)

    # def test_parse_units(self):

    # parse_set
    # parse_sequence
    # parse_value
    # parse_assignment_statement
    # def test_parse_aggregation_block(self):
    # def test_is_end_aggregation_statement(self)
    # def test_parse_module(self):
