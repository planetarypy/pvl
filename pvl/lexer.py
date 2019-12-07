#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Provides a lexer for PVL."""

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
from enum import Enum, auto
from datetime import datetime

from .grammar import grammar as Grammar
from .token import token as Token


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


class Preserve(Enum):
    FALSE = auto()
    COMMENT = auto()
    UNIT = auto()


def lex_preserve(char: str, lexeme: str, preserve: dict) -> tuple:
    # print(f'in preserve: char "{char}", lexeme "{lexeme}, p {preserve}"')
    if char == preserve['end']:
        return (lexeme + char, dict(state=Preserve.FALSE, end=None))
    else:
        return (lexeme + char, preserve)


def lex_unit(char: str, lexeme: str, preserve: dict,
             units_delimiters: tuple) -> tuple:
    if preserve['state'] == Preserve.UNIT:
        return lex_preserve(char, lexeme, preserve)
    elif char == units_delimiters[0]:
        return (lexeme + char, dict(state=Preserve.UNIT,
                                    end=units_delimiters[1]))
    return (lexeme, preserve)


def lex_singlechar_comments(char: str, lexeme: str, preserve: dict,
                            comments: dict) -> tuple:
    '''Returns a tuple with new current states of ``lexeme``
       and ``preserve``.
    '''
    if preserve['state'] == Preserve.COMMENT:
        return lex_preserve(char, lexeme, preserve)
    elif char in comments:
        return (lexeme + char, dict(state=Preserve.COMMENT,
                                    end=comments[char]))

    return (lexeme, preserve)


def lex_multichar_comments(char: str, prev_char: str, next_char: str,
                           lexeme: str, preserve: dict,
                           comments=Grammar().comments) -> tuple:
    '''Returns a tuple with new current states of ``lexeme``,
       and ``preserve``.
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
                return (lexeme + '/*', dict(state=Preserve.COMMENT, end='*/'))
            elif next_char == '/':
                return (lexeme + '*/', dict(state=Preserve.FALSE, end=None))
            else:
                return (lexeme + '*', preserve)
        elif char == '/':
            # If part of a comment ignore, and let the char == '*' handler
            # above deal with it, otherwise add it to the lexeme.
            if prev_char != '*' and next_char != '*':
                return (lexeme + '/', preserve)

    return (lexeme, preserve)


def lex_comment(char: str, prev_char: str, next_char: str,
                lexeme: str, preserve: dict,
                comments: tuple, c_info: dict) -> tuple:

    if char in c_info['multi_chars']:
        return lex_multichar_comments(char, prev_char, next_char,
                                      lexeme, preserve,
                                      comments=comments)
    else:
        return lex_singlechar_comments(char, lexeme, preserve,
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


def lex_char(char: str, prev_char: str, next_char: str,
             lexeme: str, preserve: dict,
             g: Grammar, c_info: dict) -> tuple:
    # When we are 'in' a comment or a units expression,
    # we want those to consume everything, regardless.
    # So we must handle the 'preserve' states first,
    # and then after that we can check to see if the char
    # should put us into one of those states.

    # print(f'lex_char start: char "{char}", lexeme "{lexeme}", "{preserve}"')
    if preserve['state'] == Preserve.COMMENT:
        (lexeme,
         preserve) = lex_comment(char, prev_char, next_char,
                                 lexeme, preserve, g.comments, c_info)
    elif preserve['state'] == Preserve.UNIT:
        (lexeme,
         preserve) = lex_unit(char, lexeme, preserve, g.units_delimiters)
    elif char in c_info['chars']:
        (lexeme,
         preserve) = lex_comment(char, prev_char, next_char,
                                 lexeme, preserve, g.comments, c_info)
    elif char in g.units_delimiters:
        (lexeme,
         preserve) = lex_unit(char, lexeme, preserve, g.units_delimiters)
    else:
        if char not in g.whitespace:
            lexeme += char  # adding a char each time

    # print(f'lex_char end: char "{char}", lexeme "{lexeme}", "{preserve}"')
    return (lexeme, preserve)


def lexer(s: str, g=Grammar()):
    # We're going to assume that beyond the /* */ pair, every
    # other comment pair is just single characters.  Otherwise
    # we'll need to generalize the for loop.
    c_info = _prepare_comment_tuples(g.comments)

    lexeme = ''
    preserve = dict(state=Preserve.FALSE, end=None)
    for i, char in enumerate(s):
        prev_char = _prev_char(s, i)
        next_char = _next_char(s, i)

        # print(f'lexeme at top: {lexeme}, char: {char}, '
        #       f'prev: {prev_char}, next: {next_char}')

        (lexeme, preserve) = lex_char(char, prev_char, next_char,
                                      lexeme, preserve, g, c_info)

        # print(f'lexeme at bottom: {lexeme}')

        # Now having dealt with char, decide whether to
        # go on continue accumulating the lexeme, or yield it.
        try:
            # The ``while t is not None: yield None; t = yield(t)``
            # construction below allows a user of the lexer to
            # yield a token, not like what they see, and then use
            # the generator's send() function to put the token
            # back into the generator.
            #
            # The first yield None in there allows the call to send() on
            # this generator to return None, and keep the value of t ready
            # for the next call of next() on the generator.  This is the
            # magic # that allows a user to 'return' a token to the
            # generator.
            if lexeme != '':
                if next_char is None:
                    t = yield(Token(lexeme, grammar=g))
                    while t is not None:
                        yield None
                        t = yield(t)
                    lexeme = ''
                else:
                    # Any lexeme state that we want to just allow
                    # to run around again and don't want to get
                    # caught by the clause in the elif, should
                    # test true here.
                    if(preserve['state'] != Preserve.FALSE
                       or Token(char + next_char, grammar=g).is_numeric()
                       # Since Numeric objects can begin with a reserved
                       # characters, the reserved characters may split up
                       # the lexeme.
                       ):
                        continue

                    elif(next_char in g.whitespace or
                         next_char in g.reserved_characters or
                         s.startswith(tuple(p[0] for p in g.comments), i + 1) or
                         lexeme.endswith(tuple(p[1] for p in g.comments)) or
                         lexeme in g.reserved_characters):
                        t = yield(Token(lexeme, grammar=g))
                        while t is not None:
                            yield None
                            t = yield(t)
                        lexeme = ''
                    else:
                        continue
        except ValueError as err:
            raise LexerError(err, s, i - len(lexeme))
