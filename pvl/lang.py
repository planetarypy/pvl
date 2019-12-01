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

    comment = (('/*', '*/'),)


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
                           comments=grammar().comment) -> tuple:
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
    d = dict()
    d['single_comments'] = dict()
    d['multi_chars'] = set()
    start_comments = list()
    stop_comments = list()
    for pair in comments:
        start_comments.append(pair[0])
        stop_comments.append(pair[1])
        if len(pair[0]) == 1:
            d['single_comments'][pair[0]] = pair[1]
        else:
            d['multi_chars'] |= set(pair[0])
            d['multi_chars'] |= set(pair[1])

    d['start'] = tuple(start_comments)
    d['stop'] = tuple(stop_comments)

    return d


def lexer(s: str, g=grammar()):
    # We're going to assume that beyond the /* */ pair, every
    # other comment pair is just single characters.  Otherwise
    # we'll need to generalize the for loop.
    comments = _prepare_comment_tuples(g.comment)

    lexeme = ''
    in_comment = False  # If we are in a comment, preserve all characters.
    end_comment = None
    for i, char in enumerate(s):
        prev_char = _prev_char(s, i)
        next_char = _next_char(s, i)

        if char in comments['multi_chars']:
            (lexeme,
             in_comment,
             end_comment) = lex_multichar_comments(char, prev_char, next_char,
                                                   lexeme, in_comment,
                                                   end_comment,
                                                   comments=g.comment)
        elif in_comment or char in comments['single_comments']:
            (lexeme,
             in_comment,
             end_comment) = lex_singlechar_comments(char, lexeme,
                                                    in_comment, end_comment,
                                                    comments['single_comments'])
        else:
            if char not in g.whitespace:
                lexeme += char  # adding a char each time

        # Now having dealt with char, decide whether to
        # go on continue accumulating the lexeme, or yield it.
        if lexeme != '':
            if next_char is None:
                yield(lexeme)
                lexeme = ''
            else:
                if in_comment:
                    continue
                elif(next_char in g.whitespace or
                     next_char in g.reserved_characters or
                     s.startswith(comments['start'], i + 1) or
                     lexeme.endswith(comments['stop']) or
                     lexeme in g.reserved_characters):
                    yield(lexeme)
                    lexeme = ''
                else:
                    continue
