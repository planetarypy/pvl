#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Describes the language aspects of PVL."""

# Copyright 2019, Ross A. Beyer (rbeyer@seti.org)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived
# from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import re
from datetime import datetime


class LexerError(ValueError):
    """Subclass of ValueError with the following additional properties:

       msg: The unformatted error message
       doc: The PVL document being parsed
       pos: The start index of doc where parsing failed
       lineno: The line corresponding to pos
       colno: The column corresponding to pos
    """

    def __init__(self, msg, doc, pos):
        lineno = doc.count('\n', 0, pos) + 1
        colno = pos - doc.rfind('\n', 0, pos)
        errmsg = f'{msg}: line {lineno} column {colno} (char {pos})'
        ValueError.__init__(self, errmsg)
        self.msg = msg
        self.doc = doc
        self.pos = pos
        self.lineno = lineno
        self.colno = colno

    def __reduce__(self):
        return self.__class__, (self.msg, self.doc, self.pos)


class grammar():
    '''Describes a particular PVL grammar for use by the lexer and parser.

       :var whitespace: Tuple of characters to be recognized as PVL
       White Space (used to separate syntactic elements and promote
       readability, but the amount or presence of White Space may
       not be used to provide different meanings).

       :var reserved_characters: Tuple of characters that may not
       occur in Parameter Names, Unquoted Strings, or Block Names.

       :var comment: Tuple of two-tuples with each two-tuple containing
       a pair of character sequences that enclose a comment.
    '''

    whitespace = (' ', '\n', '\r', '\t', '\v', '\f')
    reserved_characters = ('&', '<', '>', "'", '{', '}', ',',
                           '[', ']', '=', '!', '#', '(', ')',
                           '%', '+', '"', ';', '~', '|')

    # If there are any reserved_characters that might start a number,
    # they need to be added to numeric_start_chars, otherwise that
    # character will get lexed separately from the rest.
    # Technically, since '-' isn't in reserved_characters, it isn't needed,
    # but it doesn't hurt to keep it here.
    numeric_start_chars = ('+', '-')

    delimiters = (';',)

    comments = (('/*', '*/'),)
    group_keywords = (('BEGIN_GROUP', 'END_GROUP'),
                      ('GROUP', 'END_GROUP'))
    object_keywords = (('BEGIN_OBJECT', 'END_OBJECT'),
                       ('OBJECT', 'END_OBJECT'))
    aggregation_keywords = (group_keywords + object_keywords)
    end_statements = ('END',)
    reserved_keywords = set(end_statements)
    for p in aggregation_keywords:
        reserved_keywords |= set(p)

    quotes = ('"', "'")
    set_delimiters = ('{', '}')
    sequence_delimiters = ('(', ')')
    units_delimiters = ('<', '>')

    date_formats = ('%Y-%m-%d', '%Y-%j')
    time_formats = ('%H:%M', '%H:%M:%S', '%H:%M:%S.%f')
    datetime_formats = list()
    for d in (date_formats + (None,)):
        for t in (time_formats + (None,)):
            if d is None and t is None:
                continue
            elif d is None:
                datetime_formats.append(t)
                datetime_formats.append(f'{t}Z')
            elif t is None:
                datetime_formats.append(d)
                datetime_formats.append(f'{d}Z')
            else:
                datetime_formats.append(f'{d}T{t}')
                datetime_formats.append(f'{d}T{t}Z')

    # [sign]radix#non_decimal_integer#
    _s = r'(?P<sign>[+-]?)'
    binary_re = re.compile(fr'{_s}(?P<radix>2)#(?P<non_decimal>[01]+)#')
    octal_re = re.compile(fr'{_s}(?P<radix>8)#(?P<non_decimal>[0-7]+)#')
    hex_re = re.compile(fr'{_s}(?P<radix>16)#(?P<non_decimal>[0-9|A-F|a-f]+)#')


class token(str):
    '''A PVL-aware string token.
    '''

    def __new__(cls, content, grammar=grammar()):
        return str.__new__(cls, content)

    def __init__(self, content, grammar=grammar()):
        self.grammar = grammar

    def __repr__(self):
        return (f'{self.__class__.__name__}(\'{self}\', '
                f'\'{self.grammar}\')')

    def isspace(self):
        # Since there is a parent function with this name on str(),
        # we override here, so that we don't get inconsisent behavior
        # if someone forgets an underbar.
        return self.is_space()

    def is_space(self):
        if len(self) == 0:
            return False

        return all(c in self.grammar.whitespace for c in self)

    def is_WSC(self):
        if self.is_comment():
            return True

        if self.is_space():
            return True

        return all(t.is_comment() for t in lexer(self, g=self.grammar))

    def is_comment(self):
        for pair in self.grammar.comments:
            if self.startswith(pair[0]) and self.endswith(pair[1]):
                return True
        return False

    def is_quoted_string(self):
        for q in self.grammar.quotes:
            if(self.startswith(q) and
               self.endswith(q) and
               len(self) > 1):
                return True
        return False

    def is_delimiter(self):
        if self in self.grammar.delimiters:
            return True
        return False

    def is_begin_aggregation(self):
        for pair in self.grammar.aggregation_keywords:
            if self.casefold() == pair[0].casefold():
                return True
        return False

    def is_unquoted_string(self):
        for char in self.grammar.reserved_characters:
            if char in self:
                return False

        for pair in self.grammar.comments:
            if pair[0] in self:
                return False
            if pair[1] in self:
                return False

        if self.isnumeric() or self.is_datetime():
            return False

        return True

    def is_string(self):
        if self.is_quoted_string() or self.is_unquoted_string():
            return True
        return False

    def is_parameter_name(self):
        for word in self.grammar.reserved_keywords:
            if word.casefold() == self.casefold():
                return False

        return self.is_unquoted_string()

    def is_end_statement(self):
        for e in self.grammar.end_statements:
            if e.casefold() == self.casefold():
                return True
        return False

    def isnumeric(self):
        # Since there is a parent function with this name on str(),
        # we override here, so that we don't get inconsisent behavior
        # if someone forgets an underbar.
        return self.is_numeric()

    def is_numeric(self):
        if self.is_decimal():
            return True

        if self.is_binary():
            return True

        if self.is_octal():
            return True

        if self.is_hex():
            return True

        return False

    def is_decimal(self):
        try:
            float(self)
            return True
        except ValueError:
            return False

    def is_binary(self):
        if self.grammar.binary_re.fullmatch(self) is None:
            return False
        else:
            return True

    def is_octal(self):
        if self.grammar.octal_re.fullmatch(self) is None:
            return False
        else:
            return True

    def is_hex(self):
        if self.grammar.hex_re.fullmatch(self) is None:
            return False
        else:
            return True

    def is_date(self):
        for tf in self.grammar.date_formats:
            try:
                datetime.strptime(self, tf)
                return True
            except ValueError:
                pass
        return False

    def is_time(self):
        for tf in self.grammar.time_formats:
            try:
                datetime.strptime(self, tf)
                return True
            except ValueError:
                pass
        return False

    def is_datetime(self):
        for tf in self.grammar.datetime_formats:
            try:
                datetime.strptime(self, tf)
                return True
            except ValueError as err:
                pass
        return False

    def is_simple_value(self):
        if self.is_datetime() or self.is_numeric() or self.is_string():
            return True
        return False


def lex_singlechar_comments(char: str,
                            lexeme: str, in_comment: bool,
                            end_comment: str,
                            comments: dict) -> tuple:
    '''Returns a tuple with new current states of ``lexeme``,
       ``in_comment``, and ``end_comment``.
    '''
    if in_comment:
        if char == end_comment:
            return (lexeme + char, False, None)
        else:
            return (lexeme + char, in_comment, end_comment)

    elif char in comments:
        return (lexeme + char, True, comments[char])

    return (lexeme, in_comment, end_comment)


def lex_multichar_comments(char: str, prev_char: str, next_char: str,
                           lexeme: str, in_comment: bool, end_comment: str,
                           comments=grammar().comments) -> tuple:
    '''Returns a tuple with new current states of ``lexeme``,
       ``in_comment``, and ``end_comment``.
    '''

    if len(comments) == 0:
        raise ValueError('The variable provided to comments is empty.')

    allowed_pairs = (('/*', '*/'),)
    for p in comments:
        if p not in allowed_pairs:
            raise NotImplementedError('Can only handle these '
                                      'multicharacter comments: '
                                      f'{allowed_pairs}.  To handle '
                                      'others this class must be extended.')

    if ('/*', '*/') in comments:
        if char == '*':
            if prev_char == '/':
                return (lexeme + '/*', True, end_comment)
            elif next_char == '/':
                return (lexeme + '*/', False, None)
            else:
                return (lexeme + '*', in_comment, end_comment)
        elif char == '/':
            # If part of a comment ignore, and let the char == '*' handler
            # above deal with it, otherwise add it to the lexeme.
            if prev_char != '*' and next_char != '*':
                return (lexeme + '/', in_comment, end_comment)

    return (lexeme, in_comment, end_comment)


def lex_comment(char: str, prev_char: str, next_char: str,
                lexeme: str, in_comment: bool, end_comment: str,
                comments: tuple, c_info: dict) -> tuple:

    if char in c_info['multi_chars']:
        return lex_multichar_comments(char, prev_char, next_char,
                                      lexeme, in_comment, end_comment,
                                      comments=comments)
    else:
        return lex_singlechar_comments(char,
                                       lexeme, in_comment, end_comment,
                                       c_info['single_comments'])


def _prev_char(s: str, idx: int):
    if idx <= 0:
        return None
    else:
        return s[idx - 1]


def _next_char(s: str, idx: int):
    try:
        return s[idx + 1]
    except IndexError:
        return None


def _prepare_comment_tuples(comments: tuple) -> tuple:
    # I initially tried to avoid this function, if you
    # don't pre-compute this stuff, you end up re-computing
    # it every time you pass into the lex_comment() function,
    # which seemed excessive.
    d = dict()
    d['single_comments'] = dict()
    d['multi_chars'] = set()
    for pair in comments:
        if len(pair[0]) == 1:
            d['single_comments'][pair[0]] = pair[1]
        else:
            for p in pair:
                d['multi_chars'] |= set(p)

    d['chars'] = set(d['single_comments'].keys())
    d['chars'] |= d['multi_chars']

    # print(d)
    return d


def lexer(s: str, g=grammar()):
    # We're going to assume that beyond the /* */ pair, every
    # other comment pair is just single characters.  Otherwise
    # we'll need to generalize the for loop.
    c_info = _prepare_comment_tuples(g.comments)

    lexeme = ''
    in_comment = False  # If we are in a comment, preserve all characters.
    end_comment = None
    for i, char in enumerate(s):
        prev_char = _prev_char(s, i)
        next_char = _next_char(s, i)

        # print(f'lexeme at top: {lexeme}, char: {char}, '
        #       f'prev: {prev_char}, next: {next_char}')

        # Handle comments first.
        # Since we want comments to consume everything, and they may have
        # reserved characters within them, deal with them first.
        if in_comment or char in c_info['chars']:
            (lexeme,
             in_comment,
             end_comment) = lex_comment(char, prev_char, next_char,
                                        lexeme, in_comment, end_comment,
                                        g.comments, c_info)

        # Since Numeric objects can begin with reserved characters,
        # they must be handled specially, otherwise the reserved
        # characters will split up the lexeme.
        elif char in g.numeric_start_chars:
            if token(char + next_char).isnumeric():
                lexeme += char
                continue
        else:
            if char not in g.whitespace:
                lexeme += char  # adding a char each time

        # print(f'lexeme at bottom: {lexeme}')

        # Now having dealt with char, decide whether to
        # go on continue accumulating the lexeme, or yield it.
        try:
            if lexeme != '':
                if next_char is None:
                    yield(token(lexeme, grammar=g))
                    lexeme = ''
                else:
                    if in_comment:
                        continue
                    elif(next_char in g.whitespace or
                         next_char in g.reserved_characters or
                         s.startswith(tuple(p[0] for p in g.comments), i + 1) or
                         lexeme.endswith(tuple(p[1] for p in g.comments)) or
                         lexeme in g.reserved_characters):
                        yield(token(lexeme, grammar=g))
                        lexeme = ''
                    else:
                        continue
        except ValueError as err:
            raise LexerError(err, s, i - len(lexeme))
