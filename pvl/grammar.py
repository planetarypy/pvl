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

    # [sign]radix#non_decimal_integer#
    _s = r'(?P<sign>[+-]?)'
    binary_re = re.compile(fr'{_s}(?P<radix>2)#(?P<non_decimal>[01]+)#')
    octal_re = re.compile(fr'{_s}(?P<radix>8)#(?P<non_decimal>[0-7]+)#')
    hex_re = re.compile(fr'{_s}(?P<radix>16)#(?P<non_decimal>[0-9|A-F|a-f]+)#')

    _d_formats = ('%Y-%m-%d', '%Y-%j')
    _t_formats = ('%H:%M', '%H:%M:%S', '%H:%M:%S.%f')
    date_formats = _d_formats + tuple(x + 'Z' for x in _d_formats)
    time_formats = _t_formats + tuple(x + 'Z' for x in _t_formats)
    datetime_formats = list()
    for d in _d_formats:
        for t in _t_formats:
            datetime_formats.append(f'{d}T{t}')
            datetime_formats.append(f'{d}T{t}Z')

    # I really didn't want to write these, because it is so easy to
    # make a mistake with time regexes, but they're they only way
    # to parse times with 60 seconds in them.  The above regexes and
    # the datetime library are used for all other time parsing.
    _H_frag = r'(?P<hour>0\d|1\d|2[0-3])'  # 00 to 23
    _M_frag = r'(?P<minute>[0-5]\d)'  # 00 to 59
    _f_frag = r'(\.(?P<microsecond>\d+))'  # 1 or more digits
    _Y_frag = r'(?P<year>\d{3}[1-9])'  # 0001 to 9999
    _m_frag = r'(?P<month>0[1-9]|1[0-2])'  # 01 to 12
    _d_frag = r'(?P<day>0[1-9]|[12]\d|3[01])'  # 01 to 31
    _Ymd_frag = fr'{_Y_frag}-{_m_frag}-{_d_frag}'
    # 001 to 366:
    _j_frag = r'(?P<doy>(00[1-9]|0[1-9]\d)|[12]\d{2}|3[0-5]\d|36[0-6])'
    _Yj_frag = fr'{_Y_frag}-{_j_frag}'
    _time_frag = fr'{_H_frag}:{_M_frag}:60{_f_frag}?Z?'  # Only times with 60 s
    # _time_frag = fr'{_H_frag}:{_M_frag}]'  # Only times with 60 s
    leap_second_Ymd_re = re.compile(fr'({_Ymd_frag}T)?{_time_frag}')
    leap_second_Yj_re = re.compile(fr'({_Yj_frag}T)?{_time_frag}')
