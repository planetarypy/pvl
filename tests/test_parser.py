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

import datetime
import unittest

from pvl.parser import PVLParser
from pvl.lexer import lexer as Lexer
from pvl._collections import Units, PVLModule, PVLGroup, PVLObject


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
        pairs = (('GROUP = name next', 'GROUP', 'name'),
                 ('OBJECT=name next', 'OBJECT', 'name'),
                 ('BEGIN_GROUP /*c1*/ = /*c2*/ name /*c3*/ next',
                  'BEGIN_GROUP', 'name'))
        for x in pairs:
            with self.subTest(pair=x):
                tokens = Lexer(x[0])
                # next_t = x[1].split()[-1]
                self.assertEqual((x[1], x[2]),
                                 self.p.parse_begin_aggregation_statement(tokens))

        tokens = Lexer('Not-a-Begin-Aggegation-Statement = name')
        self.assertRaises(ValueError,
                          self.p.parse_begin_aggregation_statement,
                          tokens)

        strings = ('GROUP equals name', 'GROUP = 5')
        for s in strings:
            with self.subTest(string=s):
                tokens = Lexer(s)
                self.assertRaises(ValueError,
                                  self.p.parse_begin_aggregation_statement,
                                  tokens)

    def test_parse_end_aggregation(self):
        groups = (('END_GROUP', 'GROUP', 'name'),
                  ('END_GROUP = name', 'BEGIN_GROUP', 'name'),
                  ('END_OBJECT /*c1*/ =   \n name', 'OBJECT', 'name'))
        for g in groups:
            with self.subTest(groups=g):
                tokens = Lexer(g[0])
                self.assertIsNone(self.p.parse_end_aggregation(g[1], g[2],
                                                               tokens))

        bad_groups = (('END_GROUP', 'OBJECT', 'name'),
                      ('END_GROUP = foo', 'BEGIN_GROUP', 'name'))
        for g in bad_groups:
            with self.subTest(groups=g):
                tokens = Lexer(g[0])
                self.assertRaises(ValueError,
                                  self.p.parse_end_aggregation, g[1], g[2],
                                  tokens)

        tokens = Lexer('END_GROUP = ')
        self.assertRaises(StopIteration, self.p.parse_end_aggregation,
                          'BEGIN_GROUP', 'name', tokens)

    def test_parse_around_equals(self):
        strings = ('=', ' = ', '/*c1*/ = /*c2*/')
        for s in strings:
            with self.subTest(string=s):
                tokens = Lexer(s)
                self.assertIsNone(self.p._parse_around_equals(tokens))
        bad_strings = ('f', ' f ', '')
        for s in bad_strings:
            with self.subTest(string=s):
                tokens = Lexer(s)
                self.assertRaises(ValueError,
                                  self.p._parse_around_equals, tokens)
        tokens = Lexer(' = f')
        self.p._parse_around_equals(tokens)
        f = next(tokens)
        self.assertEqual(f, 'f')

    def test_parse_units(self):
        pairs = (('m', '<m>'), ('m', '< m >'),
                 ('m /* comment */', '< m /* comment */>'),
                 ('m\nfoo', '< m\nfoo >'))
        for p in pairs:
            with self.subTest(pairs=p):
                tokens = Lexer(p[1])
                self.assertEqual(p[0], self.p.parse_units(tokens))

    def test_parse_set(self):
        pairs = ((set(['a', 'b', 'c']), '{a,b,c}'),
                 (set(['a', 'b', 'c']), '{ a, b, c }'),
                 (set(['a', 'b', 'c']), '{ a, /* random */b, c }'),
                 (set(['a', frozenset(['x', 'y']), 'c']), '{ a, {x,y}, c }'))
        for p in pairs:
            with self.subTest(pairs=p):
                tokens = Lexer(p[1])
                self.assertEqual(p[0], self.p.parse_set(tokens))

    def test_parse_sequence(self):
        pairs = ((['a', 'b', 'c'], '(a,b,c)'),
                 (['a', 'b', 'c'], '( a, b, c )'),
                 (['a', 'b', 'c'], '( a, /* random */b, c )'),
                 (['a', ['x', 'y'], 'c'], '( a, (x,y), c )'))
        for p in pairs:
            with self.subTest(pairs=p):
                tokens = Lexer(p[1])
                self.assertEqual(p[0], self.p.parse_sequence(tokens))

    def test_parse_WSC_until(self):
        triplets = (('   stop <units>', 'stop', True),)
        for t in triplets:
            with self.subTest(triplet=t):
                tokens = Lexer(t[0])
                self.assertEqual(t[2], self.p.parse_WSC_until(t[1], tokens))

    def test_parse_value(self):
        pairs = (('(a,b,c)', ['a', 'b', 'c']),
                 ('{ a, b, c }', set(['a', 'b', 'c'])),
                 ('2001-01-01', datetime.date(2001, 1, 1)),
                 ('2#0101#', 5),
                 ('-79', -79),
                 ('Unquoted', 'Unquoted'),
                 ('"Quoted"', 'Quoted'),
                 ('Null', None),
                 ('TRUE', True),
                 ('false', False),
                 ('9 <planets>', Units(9, 'planets')))
        for p in pairs:
            with self.subTest(pairs=p):
                tokens = Lexer(p[0])
                self.assertEqual(p[1], self.p.parse_value(tokens))

    def test_parse_assignment_statement(self):
        pairs = (('a=b', 'a', 'b'),
                 ('a =\tb', 'a', 'b'),
                 ('a /*comment*/ = +80', 'a', 80),
                 ('a = b c = d', 'a', 'b'),
                 ('a = b; c = d', 'a', 'b'))
        for p in pairs:
            with self.subTest(pairs=p):
                tokens = Lexer(p[0])
                self.assertEqual((p[1], p[2]),
                                 self.p.parse_assignment_statement(tokens))

    def test_parse_aggregation_block(self):
        groups = (('GROUP = name bob = uncle END_GROUP',
                   ('name', PVLGroup(bob='uncle'))),
                  ('GROUP = name OBJECT = uncle name = bob END_OBJECT END_GROUP',
                   ('name', PVLGroup(uncle=PVLObject(name='bob')))),
                  ('GROUP = name bob = uncle END_GROUP = name next = token',
                   ('name', PVLGroup(bob='uncle'))))
        for g in groups:
            with self.subTest(groups=g):
                tokens = Lexer(g[0])
                self.assertEqual(g[1],
                                 self.p.parse_aggregation_block(tokens))

        bad_blocks = ('Group = name bob = uncle END_OBJECT',
                      'GROUP= name = bob = uncle END_GROUP',)
        for b in bad_blocks:
            with self.subTest(block=b):
                tokens = Lexer(b)
                self.assertRaises(ValueError,
                                  self.p.parse_aggregation_block, tokens)

        tokens = Lexer('')
        self.assertRaises(StopIteration,
                          self.p.parse_aggregation_block, tokens)

    def test_parse_end_statement(self):
        strings = ('END;', 'End ; ', 'End /*comment*/', 'END next',
                   'END', 'end', 'END ', 'END\n\n')
        for g in strings:
            with self.subTest(groups=g):
                tokens = Lexer(g)
                # top = Lexer(g)
                # for t in top:
                #     print(f'token : "{t}"')
                self.assertIsNone(self.p.parse_end_statement(tokens))

        tokens = Lexer('the_end')
        self.assertRaises(ValueError, self.p.parse_end_statement, tokens)

    def test_parse_module(self):
        groups = (('a = b c = d END', PVLModule(a='b', c='d')),
                  ('a =b GROUP = g f=g END_GROUP END',
                   PVLModule(a='b', g=PVLGroup(f='g'))),
                  ('GROUP = g f=g END_GROUP END',
                   PVLModule(g=PVLGroup(f='g'))),
                  ('GROUP = g f=g END_GROUP a = b OBJECT = o END_OBJECT END',
                   PVLModule(g=PVLGroup(f='g'), a='b', o=PVLObject())),
                  ('blob', PVLModule()))
        for g in groups:
            with self.subTest(groups=g):
                tokens = Lexer(g[0])
                self.assertEqual(g[1],
                                 self.p.parse_module(tokens))

        tokens = Lexer('blob =')
        self.assertRaises(StopIteration,
                          self.p.parse_module, tokens)

        tokens = Lexer('GROUP GROUP')
        self.assertRaises(ValueError,
                          self.p.parse_module, tokens)

    def test_parse(self):
        groups = (('a = b c = d END', PVLModule(a='b', c='d')),
                  ('a =b GROUP = g f=g END_GROUP END',
                   PVLModule(a='b', g=PVLGroup(f='g'))),
                  ('GROUP = g f=g END_GROUP END',
                   PVLModule(g=PVLGroup(f='g'))),
                  ('GROUP = g f=g END_GROUP a = b OBJECT = o END_OBJECT END',
                   PVLModule(g=PVLGroup(f='g'), a='b', o=PVLObject())),
                  ('blob', PVLModule()))
        for g in groups:
            with self.subTest(groups=g):
                self.assertEqual(g[1], self.p.parse(g[0]))
