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

from pvl import lang


class TestInternal(unittest.TestCase):

    def test_prev_char(self):
        self.assertIsNone(lang._prev_char('foo', 0))
        self.assertEqual('f', lang._prev_char('foo', 1))

    def test_next_char(self):
        self.assertIsNone(lang._next_char('foo', 2))
        self.assertEqual('b', lang._next_char('fob', 1))

    def test_prepare_comment_tuples(self):
        d = dict(single_comments=dict(),
                 multi_chars=set('/*'),
                 chars=set('/*'))
        self.assertEqual(d, lang._prepare_comment_tuples((('/*', '*/'),)))

        d = dict(single_comments={'#': '\n'},
                 multi_chars=set('/*'),
                 chars=set('/*#'))
        self.assertEqual(d, lang._prepare_comment_tuples((('/*', '*/'),
                                                          ('#', '\n'))))


class TestLexComments(unittest.TestCase):

    def test_lex_multichar_comments(self):
        self.assertEqual(('', False, None),
                         lang.lex_multichar_comments('a', 'b', 'c',
                                                     '', False, None))
        self.assertEqual(('', False, None),
                         lang.lex_multichar_comments('/', '*', 'c',
                                                     '', False, None))
        self.assertEqual(('', False, None),
                         lang.lex_multichar_comments('/', 'b', '*',
                                                     '', False, None))
        self.assertEqual(('/', False, None),
                         lang.lex_multichar_comments('/', 'b', 'c',
                                                     '', False, None))
        self.assertEqual(('*', True, None),
                         lang.lex_multichar_comments('*', 'b', 'c',
                                                     '', True, None))
        self.assertEqual(('/*', True, None),
                         lang.lex_multichar_comments('*', '/', 'c',
                                                     '', False, None))
        self.assertEqual(('*/', False, None),
                         lang.lex_multichar_comments('*', 'c', '/',
                                                     '', True, None))

        self.assertRaises(ValueError,
                          lang.lex_multichar_comments, 'a', 'b', 'c',
                          '', False, None, tuple())
        self.assertRaises(NotImplementedError,
                          lang.lex_multichar_comments, 'a', 'b', 'c',
                          '', False, None, (('/*', '*/'), ('#', '\n')))

    def test_lex_singlechar_comments(self):
        self.assertEqual(('', False, 'end'),
                         lang.lex_singlechar_comments('a', '', False, 'end',
                                                      {'k': 'v'}))
        self.assertEqual(('#', True, '\n'),
                         lang.lex_singlechar_comments('#', '', False, 'end',
                                                      {'#': '\n'}))
        self.assertEqual(('#\n', False, None),
                         lang.lex_singlechar_comments('\n', '#', True, '\n',
                                                      {'#': '\n'}))

    def test_lex_comment(self):
        self.assertEqual(('', False, 'end'),
                         lang.lex_comment('a', 'b', 'c',
                                          '', False, 'end',
                                          (('/*', '*/'),),
                                          dict(single_comments={'k': 'v'},
                                               multi_chars=set(('/', '*')))))

        self.assertEqual(('/*', True, None),
                         lang.lex_comment('*', '/', 'c',
                                          '', False, None,
                                          (('/*', '*/'),),
                                          dict(single_comments={'k': 'v'},
                                               multi_chars=set(('/', '*')))))


class TestLexer(unittest.TestCase):

    def setUp(self):
        def get_tokens(s):
            tokens = list()
            lex = lang.lexer(s)
            for t in lex:
                # print(f'yields: {t}')
                tokens.append(t)
            return tokens

        self.get_tokens = get_tokens

    def test_plain(self):
        s = 'This is a test.'
        tokens = s.split()
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_newline(self):
        s = 'This \n is  a\ttest.'
        tokens = ['This', 'is', 'a', 'test.']
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_reserved(self):
        s = 'Te=st'
        tokens = ['Te', '=', 'st']
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_comment(self):
        s = 'There is a /* comment */'
        tokens = ['There', 'is', 'a', '/* comment */']
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

        s = '/* At */ the beginning'
        tokens = ['/* At */', 'the', 'beginning']
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

        s = 'In/*the*/middle.'
        tokens = ['In', '/*the*/', 'middle.']
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_custom_comment(self):
        def get_tokens(s):
            tokens = list()
            g = lang.grammar()
            g.comments = (('/*', '*/'), ('#', '\n'))
            lex = lang.lexer(s, g=g)
            for t in lex:
                # print(f'yields: {t}')
                tokens.append(t)
            return tokens

        s = 'There is a # comment'
        tokens = ['There', 'is', 'a', '# comment']
        out = get_tokens(s)
        self.assertEqual(tokens, out)

        s = 'There is a # comment \n then more'
        tokens = ['There', 'is', 'a', '# comment \n', 'then', 'more']
        out = get_tokens(s)
        self.assertEqual(tokens, out)

        s = '# Leading \n then \n more'
        tokens = ['# Leading \n', 'then', 'more']
        out = get_tokens(s)
        self.assertEqual(tokens, out)

    def test_numeric(self):
        s = 'Number: +79'
        tokens = ['Number:', '+79']
        out = self.get_tokens(s)
        self.assertEqual(tokens, out)

    def test_lexer_recurse(self):

        def foo(tokens):
            two = list()
            for t in tokens:
                if t == 'f':
                    break
                two.append(t)
            return two

        lex = lang.lexer('a b c d e f g h')
        one = list()
        for t in lex:
            if t == 'c':
                two = foo(lex)
            else:
                one.append(t)

        self.assertEqual(['a', 'b', 'g', 'h'], one)
        self.assertEqual(['d', 'e'], two)


class TestToken(unittest.TestCase):

    def test_init(self):
        s = 'token'
        self.assertEqual(s, lang.token(s))
        self.assertEqual(s, lang.token(s, grammar=lang.grammar()))

    def test_is_comment(self):
        c = lang.token('/* comment */')
        self.assertTrue(c.is_comment())

        n = lang.token('not comment */')
        self.assertFalse(n.is_comment())

    def test_is_begin_aggregation(self):
        for s in ('BEGIN_GROUP', 'Begin_Group', 'ObJeCt'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertTrue(t.is_begin_aggregation())

        b = lang.token('END_GROUP')
        self.assertFalse(b.is_begin_aggregation())

    def test_is_end_statement(self):
        t = lang.token('END')
        self.assertTrue(t.is_end_statement())

        t = lang.token('Start')
        self.assertFalse(t.is_end_statement())

    def test_is_date(self):
        for s in ('2001-01-01', '2001-027'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertTrue(t.is_date())

        for s in ('2001-01-00', '23:43'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertFalse(t.is_date())

    def test_is_time(self):
        for s in ('23:45', '01:42:57', '12:34:56.789'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertTrue(t.is_time())

        for s in ('3:450', '2013-180'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertFalse(t.is_time())

    def test_is_datetime(self):
        for s in ('2001-027T23:45', '2001-01-01T01:34Z', '01:42:57Z'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertTrue(t.is_datetime())

        for s in ('3:450', 'frank'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertFalse(t.is_datetime())

    def test_is_parameter_name(self):
        for s in ('Hello', 'Product Id'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertTrue(t.is_parameter_name())

        for s in ('Group', '/*comment*/', '2001-027'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertFalse(t.is_parameter_name())

    def test_is_decimal(self):
        for s in ('125', '+211109', '-79',  # Integers
                  '69.35', '+12456.345', '-0.23456', '.05', '-7.',  # Floating
                  '-2.345678E12', '1.567E-10', '+4.99E+3'):  # Exponential
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertTrue(t.is_decimal())

        for s in ('2#0101#', 'frank'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertFalse(t.is_decimal())

    def test_is_binary(self):
        for s in ('2#0101#', '+2#0101#', '-2#0101#'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertTrue(t.is_binary())

        for s in ('+211109', 'echo', '+8#0156#'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertFalse(t.is_binary())

    def test_is_octal(self):
        for s in ('8#0107#', '+8#0156#', '-8#0134#'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertTrue(t.is_octal())

        for s in ('+211109', 'echo', '2#0101#'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertFalse(t.is_octal())

    def test_is_hex(self):
        for s in ('16#100A#', '+16#23Bc#', '-16#98ef#'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertTrue(t.is_hex())

        for s in ('+211109', 'echo', '2#0101#', '8#0107#'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertFalse(t.is_hex())

    def test_isnumeric(self):
        for s in ('125', '+211109', '-79',  # Integers
                  '69.35', '+12456.345', '-0.23456', '.05', '-7.',  # Floating
                  '-2.345678E12', '1.567E-10', '+4.99E+3',  # Exponential
                  '2#0101#', '+2#0101#', '-2#0101#',  # Binary
                  '8#0107#', '+8#0156#', '-8#0134#',  # Octal
                  '16#100A#', '+16#23Bc#', '-16#98ef#'):  # Hex
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertTrue(t.isnumeric())

        for s in ('frank', '#', '-apple'):
            with self.subTest(string=s):
                t = lang.token(s)
                self.assertFalse(t.isnumeric())
