#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Provides lexer functions for PVL."""

# Copyright 2019-2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.


from enum import Enum, auto

from .grammar import PVLGrammar
from .token import Token
from .decoder import PVLDecoder
from .exceptions import LexerError, firstpos


class Preserve(Enum):
    FALSE = auto()
    COMMENT = auto()
    UNIT = auto()
    QUOTE = auto()
    NONDECIMAL = auto()


def lex_preserve(char: str, lexeme: str, preserve: dict) -> tuple((str, dict)):
    """Returns a modified *lexeme* string and a modified *preserve*
    dict in a two-tuple.  The modified *lexeme* will always be
    the concatenation of *lexeme* and *char*.

    This is a lexer() helper function that is responsible for
    changing the state of the *preserve* dict, if needed.

    If the value for 'end' in *preserve* is the same as *char*,
    then the modified *preserve* will have its 'state' value
    set to ``Preserve.FALSE`` and its 'end' value set to None,
    otherwise second item in the returned tuple will be *preserve*
    unchanged.
    """
    # print(f'in preserve: char "{char}", lexeme "{lexeme}, p {preserve}"')
    if char == preserve["end"]:
        return lexeme + char, dict(state=Preserve.FALSE, end=None)
    else:
        return lexeme + char, preserve


def lex_singlechar_comments(
    char: str, lexeme: str, preserve: dict, comments: dict
) -> tuple((str, dict)):
    """Returns a modified *lexeme* string and a modified *preserve*
    dict in a two-tuple.

    This is a lexer() helper function for determining how to modify
    *lexeme* and *preserve* based on the single character in *char*
    which may or may not be a comment character.

    If the *preserve* 'state' value is Preserve.COMMENT then
    the value of lex_preserve() is returned.

    If *char* is among the keys of the *comments* dict, then the
    returned *lexeme* will be the concatenation of *lexeme* and
    *char*.  returned *preserve* dict will have its 'state' value
    set to Preserve.COMMENT and its 'end' value set to the value
    of *comments[char]*.

    Otherwise return *lexeme* and *preserve* unchanged in the
    two-tuple.
    """
    if preserve["state"] == Preserve.COMMENT:
        return lex_preserve(char, lexeme, preserve)
    elif char in comments:
        return (
            lexeme + char,
            dict(state=Preserve.COMMENT, end=comments[char]),
        )

    return lexeme, preserve


def lex_multichar_comments(
    char: str,
    prev_char: str,
    next_char: str,
    lexeme: str,
    preserve: dict,
    comments: tuple(tuple((str, str))) = PVLGrammar().comments,
) -> tuple((str, dict)):
    """Returns a modified *lexeme* string and a modified *preserve*
    dict in a two-tuple.

    This is a lexer() helper function for determining how to
    modify *lexeme* and *preserve* based on the single character
    in *char* which may or may not be part of a multi-character
    comment character group.

    This function has an internal list of allowed pairs of
    multi-character comments that it can deal with, if the
    *comments* tuple contains any two-tuples that cannot be
    handled, a NotImplementedError will be raised.

    This function will determine whether to append *char* to
    *lexeme* or not, and will set the value of the 'state' and
    'end' values of *preserve* appropriately.
    """
    # print(f'lex_multichar got these comments: {comments}')
    if len(comments) == 0:
        raise ValueError("The variable provided to comments is empty.")

    allowed_pairs = (("/*", "*/"),)
    for p in comments:
        if p not in allowed_pairs:
            raise NotImplementedError(
                "Can only handle these "
                "multicharacter comments: "
                f"{allowed_pairs}.  To handle "
                "others this class must be extended."
            )

    if ("/*", "*/") in comments:
        if char == "*":
            if prev_char == "/":
                return lexeme + "/*", dict(state=Preserve.COMMENT, end="*/")
            elif next_char == "/":
                return lexeme + "*/", dict(state=Preserve.FALSE, end=None)
            else:
                return lexeme + "*", preserve
        elif char == "/":
            # If part of a comment ignore, and let the char == '*' handler
            # above deal with it, otherwise add it to the lexeme.
            if prev_char != "*" and next_char != "*":
                return lexeme + "/", preserve

    return lexeme, preserve


def lex_comment(
    char: str,
    prev_char: str,
    next_char: str,
    lexeme: str,
    preserve: dict,
    c_info: dict,
) -> tuple((str, dict)):
    """Returns a modified *lexeme* string and a modified *preserve*
    dict in a two-tuple.

    This is a lexer() helper function for determining how to
    modify *lexeme* and *preserve* based on the single character
    in *char* which may or may not be a comment character.

    This function just makes the decision about whether to call
    lex_multichar_comments() or lex_singlechar_comments(), and
    then returns what they return.
    """

    if char in c_info["multi_chars"]:
        return lex_multichar_comments(
            char,
            prev_char,
            next_char,
            lexeme,
            preserve,
            comments=c_info["multi_comments"],
        )
    else:
        return lex_singlechar_comments(
            char, lexeme, preserve, c_info["single_comments"]
        )


def _prev_char(s: str, idx: int):
    """Returns the character from *s* at the position before *idx*
    or None, if *idx* is zero.
    """
    if idx <= 0:
        return None
    else:
        return s[idx - 1]


def _next_char(s: str, idx: int):
    """Returns the character from *s* at the position after *idx*
    or None, if *idx* is the last position in *s*.
    """
    try:
        return s[idx + 1]
    except IndexError:
        return None


def _prepare_comment_tuples(comments: tuple(tuple((str, str)))) -> dict:
    """Returns a dict of information based on the contents
    of *comments*.

    This is a lexer() helper function to prepare information
    for lexer().
    """
    # I initially tried to avoid this function, if you
    # don't pre-compute this stuff, you end up re-computing
    # it every time you pass into the lex_comment() function,
    # which seemed excessive.
    d = dict()
    m = list()
    d["single_comments"] = dict()
    d["multi_chars"] = set()
    for pair in comments:
        if len(pair[0]) == 1:
            d["single_comments"][pair[0]] = pair[1]
        else:
            m.append(pair)
            for p in pair:
                d["multi_chars"] |= set(p)

    d["chars"] = set(d["single_comments"].keys())
    d["chars"] |= d["multi_chars"]
    d["multi_comments"] = tuple(m)

    # print(d)
    return d


def lex_char(
    char: str,
    prev_char: str,
    next_char: str,
    lexeme: str,
    preserve: dict,
    g: PVLGrammar,
    c_info: dict,
) -> tuple((str, dict)):
    """Returns a modified *lexeme* string and a modified *preserve*
    dict in a two-tuple.

    This is the main lexer() helper function for determining how
    to modify (or not) *lexeme* and *preserve* based on the
    single character in *char* and the other values passed into
    this function.
    """

    # When we are 'in' a comment or a units expression,
    # we want those to consume everything, regardless.
    # So we must handle the 'preserve' states first,
    # and then after that we can check to see if the char
    # should put us into one of those states.

    # print(f'lex_char start: char "{char}", lexeme "{lexeme}", "{preserve}"')

    if preserve["state"] != Preserve.FALSE:
        if preserve["state"] == Preserve.COMMENT:
            (lexeme, preserve) = lex_comment(
                char, prev_char, next_char, lexeme, preserve, c_info
            )
        elif preserve["state"] in (
            Preserve.UNIT,
            Preserve.QUOTE,
            Preserve.NONDECIMAL,
        ):
            (lexeme, preserve) = lex_preserve(char, lexeme, preserve)
        else:
            raise ValueError(
                "{} is not a ".format(preserve["state"])
                + "recognized preservation state."
            )
    elif (
        char == "#"
        and g.nondecimal_pre_re.fullmatch(lexeme + char) is not None
    ):
        lexeme += char
        preserve = dict(state=Preserve.NONDECIMAL, end="#")
    elif char in c_info["chars"]:
        (lexeme, preserve) = lex_comment(
            char, prev_char, next_char, lexeme, preserve, c_info
        )
    elif char in g.units_delimiters[0]:
        lexeme += char
        preserve = dict(state=Preserve.UNIT, end=g.units_delimiters[1])
    elif char in g.quotes:
        lexeme += char
        preserve = dict(state=Preserve.QUOTE, end=char)
    else:
        if char not in g.whitespace:
            lexeme += char  # adding a char each time

    # print(f'lex_char end: char "{char}", lexeme "{lexeme}", "{preserve}"')
    return lexeme, preserve


def lex_continue(
    char: str,
    next_char: str,
    lexeme: str,
    token: Token,
    preserve: dict,
    g: PVLGrammar,
) -> bool:
    """Return True if accumulation of *lexeme* should continue based
    on the values passed into this function, false otherwise.

    This is a lexer() helper function.
    """

    if next_char is None:
        return False

    if not g.char_allowed(next_char):
        return False

    if preserve["state"] != Preserve.FALSE:
        return True

    # Since Numeric objects can begin with a reserved
    # character, the reserved characters may split up
    # the lexeme.
    if (
        char in g.numeric_start_chars
        and Token(char + next_char, grammar=g).is_numeric()
    ):
        return True

    # Since Non Decimal Numerics can have reserved characters in them.
    if g.nondecimal_pre_re.fullmatch(lexeme + next_char) is not None:
        return True

    # Since the numeric signs could be in the reserved characters,
    # make sure we can parse scientific notation correctly:
    if (
        char.lower() == "e"
        and next_char in g.numeric_start_chars
        and Token(lexeme + next_char + "2", grammar=g).is_numeric()
    ):
        return True

    # Some datetimes can have trailing numeric tz offsets,
    # if the decoder allows it, this means there could be
    # a '+' that splits the lexeme that we don't want.
    if next_char in g.numeric_start_chars and token.is_datetime():
        return True

    return False


def lexer(s: str, g=PVLGrammar(), d=PVLDecoder()):
    """This is a generator function that returns pvl.Token objects
    based on the passed in string, *s*, when the generator's
    next() is called.

    A call to send(*t*) will 'return' the value *t* to the
    generator, which will be yielded upon calling next().
    This allows a user to 'peek' at the next token, but return it
    if they don't like what they see.

    *g* is expected to be an instance of pvl.grammar, and *d* an
    instance of pvl.decoder.  The lexer will perform differently,
    given different values of *g* and *d*.
    """
    c_info = _prepare_comment_tuples(g.comments)
    # print(c_info)

    lexeme = ""
    preserve = dict(state=Preserve.FALSE, end=None)
    for i, char in enumerate(s):
        if not g.char_allowed(char):
            raise LexerError(
                f'The character "{char}" (ord: {ord(char)}) '
                " is not allowed by the grammar.",
                s,
                i,
                lexeme,
            )

        prev_char = _prev_char(s, i)
        next_char = _next_char(s, i)

        # print(repr(f'lexeme at top: ->{lexeme}<-, char: {char}, '
        #            f'prev: {prev_char}, next: {next_char}, '
        #            f'{preserve}'))

        (lexeme, preserve) = lex_char(
            char, prev_char, next_char, lexeme, preserve, g, c_info
        )

        # print(repr(f'       at bot: ->{lexeme}<-,          '
        #            f'                  '
        #            f'{preserve}'))

        # Now having dealt with char, decide whether to
        # go on continue accumulating the lexeme, or yield it.

        if lexeme == "":
            continue

        try:
            # The ``while t is not None: yield None; t = yield(t)``
            # construction below allows a user of the lexer to
            # yield a token, not like what they see, and then use
            # the generator's send() function to put the token
            # back into the generator.
            #
            # The first ``yield None`` in there allows the call to
            # send() on this generator to return None, and keep the
            # value of *t* ready for the next call of next() on the
            # generator.  This is the magic that allows a user to
            # 'return' a token to the generator.
            tok = Token(lexeme, grammar=g, decoder=d, pos=firstpos(lexeme, i))

            if lex_continue(char, next_char, lexeme, tok, preserve, g):
                # Any lexeme state that we want to just allow
                # to run around again and don't want to get
                # caught by the clause in the elif, should
                # test true via lex_continue()
                continue

            elif (
                next_char is None
                or not g.char_allowed(next_char)
                or next_char in g.whitespace
                or next_char in g.reserved_characters
                or s.startswith(tuple(p[0] for p in g.comments), i + 1)
                or lexeme.endswith(tuple(p[1] for p in g.comments))
                or lexeme in g.reserved_characters
                or tok.is_quoted_string()
            ):
                # print(f'yielding {tok}')
                t = yield tok
                while t is not None:
                    yield None
                    t = yield t
                lexeme = ""
            else:
                continue

        except ValueError as err:
            raise LexerError(err, s, i, lexeme)
