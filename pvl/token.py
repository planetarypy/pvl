# -*- coding: utf-8 -*-

# Copyright 2019-2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.


from .decoder import PVLDecoder
from .grammar import PVLGrammar


class Token(str):
    """A PVL-aware string.

    :var content: A string that is the Token text.

    :var grammar: A pvl.grammar object, if None or not specified, it will
                  be set to the grammar parameter of *decoder* (if
                  *decoder* is not None) or will default to PVLGrammar().

    :var decoder: A pvl.decoder object, defaults to
                  PVLDecoder(grammar=*grammar*).

    :var pos: Integer that describes the starting position of this
              Token in the source string, defaults to zero.
    """

    def __new__(cls, content, grammar=None, decoder=None, pos=0):
        return str.__new__(cls, content)

    def __init__(self, content, grammar=None, decoder=None, pos=0):
        if grammar is None:
            if decoder is not None:
                self.grammar = decoder.grammar
            else:
                self.grammar = PVLGrammar()
        elif isinstance(grammar, PVLGrammar):
            self.grammar = grammar
        else:
            raise TypeError("The grammar object is not of type PVLGrammar.")

        if decoder is None:
            self.decoder = PVLDecoder(grammar=self.grammar)
        elif isinstance(decoder, PVLDecoder):
            self.decoder = decoder
        else:
            raise TypeError("The decoder object is not of type PVLDecoder.")

        self.pos = pos

    def __repr__(self):
        return f"{self.__class__.__name__}('{self}', " f"'{self.grammar}')"

    def __index__(self):
        return self.decoder.decode_non_decimal(str(self))

    def __float__(self):
        return self.decoder.decode_decimal(str(self))

    def split(self, sep=None, maxsplit=-1) -> list:
        """Extends ``str.split()`` that calling split() on a Token
        returns a list of Tokens.
        """
        str_list = super().split(sep, maxsplit)
        tkn_list = list()
        for t in str_list:
            tkn_list.append(
                Token(t, grammar=self.grammar, decoder=self.decoder)
            )
        return tkn_list

    def replace(self, *args):
        """Extends ``str.replace()`` to return a Token."""
        return Token(
            super().replace(*args), grammar=self.grammar, decoder=self.decoder
        )

    def lstrip(self, chars=None):
        """Extends ``str.lstrip()`` to strip whitespace according
        to the definition of whitespace in the Token's grammar
        instead of the default Python whitespace definition.
        """
        return self._strip(super().lstrip, chars)

    def rstrip(self, chars=None):
        """Extends ``str.rstrip()`` to strip whitespace according
        to the definition of whitespace in the Token's grammar
        instead of the default Python whitespace definition.
        """
        return self._strip(super().rstrip, chars)

    def strip(self, chars=None):
        """Extends ``str.strip()`` to strip whitespace according
        to the definition of whitespace in the Token's grammar
        instead of the default Python whitespace definition.
        """
        return self._strip(super().strip, chars)

    def _strip(self, strip_func, chars=None):
        # Shared functionality for the various strip functions.
        if chars is None:
            chars = "".join(self.grammar.whitespace)
        return Token(
            strip_func(chars), grammar=self.grammar, decoder=self.decoder
        )

    def isspace(self) -> bool:
        """Overrides ``str.isspace()`` to be the same as Token's
        is_space() function, so that we don't get inconsisent
        behavior if someone forgets an underbar.
        """
        # So that we don't get inconsisent behavior
        # if someone forgets an underbar.
        return self.is_space()

    def is_space(self) -> bool:
        """Return true if the Token contains whitespace according
        to the definition of whitespace in the Token's grammar
        and there is at least one character, false otherwise.
        """
        if len(self) == 0:
            return False

        return all(c in self.grammar.whitespace for c in self)

    def is_WSC(self) -> bool:
        """Return true if the Token is white space characters or comments
        according to the Token's grammar, false otherwise.
        """
        if self.is_comment():
            return True

        if self.is_space():
            return True

        for ws in reversed(self.grammar.whitespace):
            temp = self.replace(ws, " ")

        return all(t.is_comment() for t in temp.split())

    def is_comment(self) -> bool:
        """Return true if the Token is a comment according to the
        Token's grammar (defined as beginning and ending with
        comment delimieters), false otherwise.
        """
        for pair in self.grammar.comments:
            if self.startswith(pair[0]) and self.endswith(pair[1]):
                return True
        return False

    def is_quote(self) -> bool:
        """Return true if the Token is a comment character (or
        multicharacter comment delimiter) according to the
        Token's grammar, false otherwise.
        """
        if self in self.grammar.quotes:
            return True
        else:
            return False

    def is_quoted_string(self) -> bool:
        """Return true if the Token can be converted to a quoted
        string by the Token's decoder, false otherwise.
        """
        try:
            self.decoder.decode_quoted_string(self)
            return True
        except ValueError:
            return False

    def is_delimiter(self) -> bool:
        """Return true if the Token is a delimiter character
        (e.g. the ';' in PVL) according to the Token's grammar,
        false otherwise.
        """
        if self in self.grammar.delimiters:
            return True
        return False

    def is_begin_aggregation(self) -> bool:
        """Return true if the Token is a begin aggregation
        keyword (e.g. 'BEGIN_GROUP' in PVL) according to
        the Token's grammar, false otherwise.
        """
        for k in self.grammar.aggregation_keywords.keys():
            if self.casefold() == k.casefold():
                return True
        return False

    def is_unquoted_string(self) -> bool:
        """Return false if the Token has any
        reserved characters, comment characters, whitespace
        characters or could be interpreted as a number,
        date, or time according to the Token's grammar,
        true otherwise.
        """
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

        for char in self.grammar.whitespace:
            if char in self:
                return False

        return True

    def is_string(self) -> bool:
        """Return true if either the Token's is_quoted_string()
        or is_unquoted_string() return true, false otherwise.
        """
        if self.is_quoted_string() or self.is_unquoted_string():
            return True
        return False

    def is_parameter_name(self) -> bool:
        """Return true if the Token is an unquoted string that
        isn't a reserved_keyword according to the Token's
        grammar, false otherwise.
        """
        for word in self.grammar.reserved_keywords:
            if word.casefold() == self.casefold():
                return False

        return self.is_unquoted_string()

    def is_end_statement(self) -> bool:
        """Return true if the Token matches an end statement
        from its grammar, false otherwise.
        """
        for e in self.grammar.end_statements:
            if e.casefold() == self.casefold():
                return True
        return False

    def isnumeric(self) -> bool:
        """Overrides ``str.isnumeric()`` to be the same as Token's
        is_numeric() function, so that we don't get inconsisent behavior
        if someone forgets an underbar.
        """
        return self.is_numeric()

    def is_numeric(self) -> bool:
        """Return true if the Token's is_decimal() or is_non_decimal()
        functions return true, false otherwise.
        """
        if self.is_decimal() or self.is_non_decimal():
            return True

        return False

    def is_decimal(self) -> bool:
        """Return true if the Token's decoder can convert the Token
        to a decimal value, false otherwise.
        """
        try:
            self.decoder.decode_decimal(self)
            return True
        except ValueError:
            return False

    def is_non_decimal(self) -> bool:
        """Return true if the Token's decoder can convert the Token
        to a numeric non-decimal value, false otherwise.
        """
        try:
            self.decoder.decode_non_decimal(self)
            return True
        except ValueError:
            return False

    # Took these out, since some grammars allow a much wider
    # range of radix values.
    #
    # def is_binary(self) -> bool:
    #     if self.grammar.binary_re.fullmatch(self) is None:
    #         return False
    #     else:
    #         return True

    # def is_octal(self) -> bool:
    #     if self.grammar.octal_re.fullmatch(self) is None:
    #         return False
    #     else:
    #         return True

    # def is_hex(self) -> bool:
    #     if self.grammar.hex_re.fullmatch(self) is None:
    #         return False
    #     else:
    #         return True

    def is_datetime(self) -> bool:
        """Return true if the Token's decoder can convert the Token
        to a datetime, false otherwise.

        Separate is_date() or is_time() functions aren't needed,
        since PVL parsing doesn't distinguish between them.
        If a user needs that distinction the decoder's
        decode_datetime(self) function should return a datetime
        time, date, or datetime object, as appropriate, and
        a user can use isinstance() to check.
        """
        try:
            self.decoder.decode_datetime(self)
            return True
        except ValueError:
            return False

    def is_simple_value(self) -> bool:
        """Return true if the Token's decoder can convert the Token
        to a 'simple value', however the decoder defines that, false
        otherwise.
        """
        try:
            self.decoder.decode_simple_value(self)
            return True
        except ValueError:
            return False
