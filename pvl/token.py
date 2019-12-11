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

from .decoder import PVLDecoder
from .grammar import grammar as Grammar


class token(str):
    '''A PVL-aware string token.
    '''

    def __new__(cls, content, grammar=None, decoder=None):
        return str.__new__(cls, content)

    def __init__(self, content, grammar=None, decoder=None):

        if grammar is None:
            self.grammar = Grammar()
        elif isinstance(grammar, Grammar):
            self.grammar = grammar
        else:
            raise Exception

        if decoder is None:
            self.decoder = PVLDecoder(self.grammar)
        elif isinstance(decoder, PVLDecoder):
            self.decoder = decoder
        else:
            raise Exception

    def __repr__(self):
        return (f'{self.__class__.__name__}(\'{self}\', '
                f'\'{self.grammar}\')')

    def __index__(self):
        try:
            return self.decoder.decode_non_decimal(self)
        except:
            raise
            # return int(self, base=10)

    def split(self, sep=None, maxsplit=-1) -> list:
        # This overrides the parent function so that calling
        # split on a token returns a list of tokens.
        str_list = super().split(sep, maxsplit)
        tkn_list = list()
        for t in str_list:
            tkn_list.append(token(t, grammar=self.grammar,
                                  decoder=self.decoder))
        return tkn_list

    def replace(self, *args):
        # Override parent function to return a token.
        return token(super().replace(*args),
                     grammar=self.grammar, decoder=self.decoder)

    def lstrip(self, chars=None):
        # Override parent function to strip the grammar's whitespace
        return self._strip(super().lstrip, chars)

    def rstrip(self, chars=None):
        # Override parent function to strip the grammar's whitespace
        return self._strip(super().rstrip, chars)

    def strip(self, chars=None):
        # Override parent function to strip the grammar's whitespace
        return self._strip(super().strip, chars)

    def _strip(self, strip_func, chars=None):
        if chars is None:
            chars = ''.join(self.grammar.whitespace)
        return token(strip_func(chars),
                     grammar=self.grammar, decoder=self.decoder)

    def isspace(self) -> bool:
        # Since there is a parent function with this name on str(),
        # we override here, so that we don't get inconsisent behavior
        # if someone forgets an underbar.
        return self.is_space()

    def is_space(self) -> bool:
        if len(self) == 0:
            return False

        return all(c in self.grammar.whitespace for c in self)

    def is_WSC(self) -> bool:
        if self.is_comment():
            return True

        if self.is_space():
            return True

        for ws in reversed(self.grammar.whitespace):
            self = self.replace(ws, ' ')

        return all(t.is_comment() for t in self.split())

    def is_comment(self) -> bool:
        for pair in self.grammar.comments:
            if self.startswith(pair[0]) and self.endswith(pair[1]):
                return True
        return False

    def is_quote(self) -> bool:
        if self in self.grammar.quotes:
            return True
        else:
            return False

    def is_quoted_string(self) -> bool:
        try:
            self.decoder.decode_quoted_string(self)
            return True
        except ValueError:
            return False

    def is_delimiter(self) -> bool:
        if self in self.grammar.delimiters:
            return True
        return False

    def is_begin_aggregation(self) -> bool:
        for k in self.grammar.aggregation_keywords.keys():
            if self.casefold() == k.casefold():
                return True
        return False

    def is_unquoted_string(self) -> bool:
        for char in self.grammar.reserved_characters:
            if char in self:
                return False

        for pair in self.grammar.comments:
            if pair[0] in self:
                return False
            if pair[1] in self:
                return False

        if self.is_numeric() or self.is_datetime():
            return False

        return True

    def is_string(self) -> bool:
        if self.is_quoted_string() or self.is_unquoted_string():
            return True
        return False

    def is_parameter_name(self) -> bool:
        for word in self.grammar.reserved_keywords:
            if word.casefold() == self.casefold():
                return False

        return self.is_unquoted_string()

    def is_end_statement(self) -> bool:
        for e in self.grammar.end_statements:
            if e.casefold() == self.casefold():
                return True
        return False

    def isnumeric(self) -> bool:
        # Since there is a parent function with this name on str(),
        # we override here, so that we don't get inconsisent behavior
        # if someone forgets an underbar.
        return self.is_numeric()

    def is_numeric(self) -> bool:
        if self.is_decimal():
            return True

        if self.is_non_decimal():
            return True

        return False

    def is_decimal(self) -> bool:
        try:
            self.decoder.decode_decimal(self)
            return True
        except ValueError:
            return False

    def is_non_decimal(self) -> bool:
        try:
            self.decoder.decode_non_decimal(self)
            return True
        except ValueError:
            return False

    def is_binary(self) -> bool:
        if self.grammar.binary_re.fullmatch(self) is None:
            return False
        else:
            return True

    def is_octal(self) -> bool:
        if self.grammar.octal_re.fullmatch(self) is None:
            return False
        else:
            return True

    def is_hex(self) -> bool:
        if self.grammar.hex_re.fullmatch(self) is None:
            return False
        else:
            return True

    def is_datetime(self) -> bool:
        # Separate is_date() or is_time() functions aren't needed,
        # since PVL parsing doesn't distinguish between them.
        # If a user needs that distinction the decoder's
        # decode_datetime(self) function should return a datetime
        # time, date, or datetime object, as appropriate, and
        # a user can use isinstance() to check.
        try:
            self.decoder.decode_datetime(self)
            return True
        except ValueError:
            return False

    def is_simple_value(self) -> bool:
        try:
            self.decoder.decode_simple_value(self)
            return True
        except ValueError:
            return False
