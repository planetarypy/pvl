# -*- coding: utf-8 -*-
"""
Exceptions for the Parameter Value Library.
"""

# Copyright 2019-2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.


def firstpos(sub: str, pos: int):
    """On the assumption that *sub* is a substring contained in a longer
    string, and *pos* is the index in that longer string of the final
    character in sub, returns the position of the first character of
    sub in that longer string.

    This is useful in the PVL library when we know the position of the
    final character of a token, but want the position of the first
    character.
    """
    return pos - len(sub) + 1


def linecount(doc: str, end: int, start: int = 0):
    """Returns the number of lines (by counting the
    number of newline characters \\n, with the first line
    being line number one) in the string *doc* between the
    positions *start* and *end*.
    """
    return doc.count("\n", start, end) + 1


class LexerError(ValueError):
    """Subclass of ValueError with the following additional properties:

    msg: The unformatted error message
    doc: The PVL text being parsed
    pos: The start index in doc where parsing failed
    lineno: The line corresponding to pos
    colno: The column corresponding to pos
    """

    def __init__(self, msg, doc, pos, lexeme):
        self.pos = firstpos(lexeme, pos)
        lineno = linecount(doc, self.pos)
        colno = self.pos - doc.rfind("\n", 0, self.pos)
        # Assemble a context string that consists of whole
        # words, using fragments is hard to read.
        context_tokens = doc[self.pos - 15: self.pos + 15].split(" ")
        context = " ".join(context_tokens[1:-1])
        errmsg = (
            f"{msg}: line {lineno} column {colno} (char {pos}) "
            f'near "{context}"'
        )
        super().__init__(self, errmsg)
        self.msg = msg
        self.doc = doc
        self.lineno = lineno
        self.colno = colno
        self.lexeme = lexeme

    def __reduce__(self):
        return self.__class__, (self.msg, self.doc, self.pos, self.lexeme)


class ParseError(Exception):
    """An exception to signal errors in the pvl parser."""

    def __init__(self, msg, token=None):
        super().__init__(self, msg)
        self.token = token


class QuantityError(Exception):
    """A simple exception to distinguish errors from Quantity classes."""

    pass
