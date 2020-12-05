# -*- coding: utf-8 -*-
"""Describes the language aspects of PVL dialects.

These grammar objects are not particularly meant to be easily
user-modifiable during running of an external program, which is why
they have no arguments at initiation time, nor are there any methods
or functions to modify them.  This is because these grammar objects
are used both for reading and writing PVL-text.  As such, objects
like PVLGrammar and ODLGrammar shouldn't be altered, because if
they are, then the PVL-text written out with them wouldn't conform
to the spec.

Certainly, these objects do have attributes that can be altered,
but unless you've carefully read the code, it isn't recommended.

Maybe someday we'll add a more user-friendly interface to allow that,
but in the meantime, just leave an Issue on the GitHub repo.
"""

# Copyright 2019-2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import re
from collections import abc


class PVLGrammar:
    """Describes a PVL grammar for use by the lexer and parser.

    The reference for this grammar is the CCSDS-641.0-B-2 'Blue Book'.
    """

    spacing_characters = (" ", "\t")
    format_effectors = ("\n", "\r", "\v", "\f")

    # Tuple of characters to be recognized as PVL White Space
    # (used to separate syntactic elements and promote readability,
    # but the amount or presence of White Space may not be used to
    # provide different meanings).
    whitespace = spacing_characters + format_effectors

    # Tuple of characters that may not occur in Parameter Names,
    # Unquoted Strings, nor Block Names.
    reserved_characters = (
        "&",
        "<",
        ">",
        "'",
        "{",
        "}",
        ",",
        "[",
        "]",
        "=",
        "!",
        "#",
        "(",
        ")",
        "%",
        "+",
        '"',
        ";",
        "~",
        "|",
    )

    # If there are any reserved_characters that might start a number,
    # they need to be added to numeric_start_chars, otherwise that
    # character will get lexed separately from the rest.
    # Technically, since '-' isn't in reserved_characters, it isn't needed,
    # but it doesn't hurt to keep it here.
    numeric_start_chars = ("+", "-")

    delimiters = (";",)

    # Tuple of two-tuples with each two-tuple containing a pair of character
    # sequences that enclose a comment.
    comments = (("/*", "*/"),)

    # A note on keywords: they should always be compared with
    # the str.casefold() function.
    # So 'NULL'.casefold(), 'Null'.casefold(), and 'NuLl".casefold()
    # all compare equals to none_keyword.casefold().
    none_keyword = "NULL"
    true_keyword = "TRUE"
    false_keyword = "FALSE"
    group_pref_keywords = ("BEGIN_GROUP", "END_GROUP")
    group_keywords = {"GROUP": "END_GROUP", "BEGIN_GROUP": "END_GROUP"}
    object_pref_keywords = ("BEGIN_OBJECT", "END_OBJECT")
    object_keywords = {"OBJECT": "END_OBJECT", "BEGIN_OBJECT": "END_OBJECT"}
    aggregation_keywords = dict()
    aggregation_keywords.update(group_keywords)
    aggregation_keywords.update(object_keywords)
    end_statements = ("END",)
    reserved_keywords = set(end_statements)
    for p in aggregation_keywords.items():
        reserved_keywords |= set(p)

    quotes = ('"', "'")
    set_delimiters = ("{", "}")
    sequence_delimiters = ("(", ")")
    units_delimiters = ("<", ">")

    # [sign]radix#non_decimal_integer#
    _s = r"(?P<sign>[+-]?)"
    nondecimal_pre_re = re.compile(fr"{_s}(?P<radix>2|8|16)#")
    binary_re = re.compile(fr"{_s}(?P<radix>2)#(?P<non_decimal>[01]+)#")
    octal_re = re.compile(fr"{_s}(?P<radix>8)#(?P<non_decimal>[0-7]+)#")
    hex_re = re.compile(fr"{_s}(?P<radix>16)#(?P<non_decimal>[0-9A-Fa-f]+)#")
    nondecimal_re = re.compile(
        fr"{nondecimal_pre_re.pattern}(?P<non_decimal>[0-9|A-Fa-f]+)#"
    )

    _d_formats = ("%Y-%m-%d", "%Y-%j")
    _t_formats = ("%H:%M", "%H:%M:%S", "%H:%M:%S.%f")
    date_formats = _d_formats + tuple(x + "Z" for x in _d_formats)
    time_formats = _t_formats + tuple(x + "Z" for x in _t_formats)
    datetime_formats = list()
    for d in _d_formats:
        for t in _t_formats:
            datetime_formats.append(f"{d}T{t}")
            datetime_formats.append(f"{d}T{t}Z")

    # I really didn't want to write these, because it is so easy to
    # make a mistake with time regexes, but they're they only way
    # to parse times with 60 seconds in them.  The above regexes and
    # the datetime library are used for all other time parsing.
    _H_frag = r"(?P<hour>0\d|1\d|2[0-3])"  # 00 to 23
    _M_frag = r"(?P<minute>[0-5]\d)"  # 00 to 59
    _f_frag = r"(\.(?P<microsecond>\d+))"  # 1 or more digits
    _Y_frag = r"(?P<year>\d{3}[1-9])"  # 0001 to 9999
    _m_frag = r"(?P<month>0[1-9]|1[0-2])"  # 01 to 12
    _d_frag = r"(?P<day>0[1-9]|[12]\d|3[01])"  # 01 to 31
    _Ymd_frag = fr"{_Y_frag}-{_m_frag}-{_d_frag}"
    # 001 to 366:
    _j_frag = r"(?P<doy>(00[1-9]|0[1-9]\d)|[12]\d{2}|3[0-5]\d|36[0-6])"
    _Yj_frag = fr"{_Y_frag}-{_j_frag}"
    _time_frag = fr"{_H_frag}:{_M_frag}:60{_f_frag}?Z?"  # Only times with 60 s
    # _time_frag = fr'{_H_frag}:{_M_frag}]'  # Only times with 60 s
    leap_second_Ymd_re = re.compile(fr"({_Ymd_frag}T)?{_time_frag}")
    leap_second_Yj_re = re.compile(fr"({_Yj_frag}T)?{_time_frag}")

    def char_allowed(self, char):
        """Returns true if *char* is allowed in the PVL Character Set.

        This is defined as most of the ISO 8859-1 'latin-1' character
        set with some exclusions.
        """
        if len(char) != 1:
            raise Exception

        o = ord(char)

        # The vertical tab, ord('\t') = 11, is mistakenly
        # shaded on page B-3 of the PVL specification.
        if (
            o > 255
            or (0 <= o <= 8)
            or
            # o == 11 or
            (14 <= o <= 31)
            or (127 <= o <= 159)
        ):
            return False
        else:
            return True


class ODLGrammar(PVLGrammar):
    """This defines a PDS3 ODL grammar.

    The reference for this grammar is the PDS3 Standards Reference
    (version 3.8, 27 Feb 2009) Chapter 12: Object Description
    Language Specification and Usage.
    """

    group_pref_keywords = ("GROUP", "END_GROUP")
    object_pref_keywords = ("OBJECT", "END_OBJECT")

    # ODL does not allow times with a seconds value of 60.
    leap_second_Ymd_re = None
    leap_second_Yj_re = None

    # ODL allows the radix to be from 2 to 16, but the optional sign
    # must be after the first octothorpe (#).  Why ODL thought this was
    # an important difference to make from PVL, I have no idea.
    # radix#[sign]non_decimal_integer#
    nondecimal_pre_re = re.compile(fr"(?P<radix>[2-9]|1[0-6])#{PVLGrammar._s}")
    nondecimal_re = re.compile(
        fr"{nondecimal_pre_re.pattern}(?P<non_decimal>[0-9A-Fa-f]+)#"
    )

    def char_allowed(self, char):
        """Returns true if *char* is allowed in the ODL Character Set.

        The ODL Character Set is limited to ASCII.  This is fewer
        characters than PVL, but appears to allow more control
        characters to be in quoted strings than PVL does.
        """
        if len(char) != 1:
            raise Exception

        try:
            char.encode(encoding="ascii")
            return True
        except UnicodeError:
            return False


class ISISGrammar(PVLGrammar):
    """This defines the ISIS version of PVL.

       This is valid as of ISIS 3.9, and before, at least.

       The ISIS 'Pvl' object typically writes out parameter
       values and keywords in CamelCase (e.g. 'Group', 'End_Group',
       'CenterLatitude', etc.), but it will accept all-uppercase
       versions.

       Technically, since the ISIS 'Pvl' object which parses
       PVL text into C++ objects for ISIS programs to work with
       does not recognize the 'BEGIN_<GROUP|OBJECT>' construction,
       this means that ISIS does not parse PVL text that would be
       valid according to the PVL, ODL, or PDS3 specs.
    """

    # The other thing that ISIS seems to be doing differently is to
    # split any text of all kinds with a dash continuation character.  This
    # is currently handled in the OmniParser.parse() function.

    # At
    # https://astrodiscuss.usgs.gov/t/what-pvl-specification-does-isis-conform-to/
    #
    # Stuart Sides, ISIS developer, says:
    #     The ISIS3 implementation of PVL/ODL (like) does not strictly
    #     follow any of the published standards. It was based on PDS3
    #     ODL from the 1990s, but has several extensions (your example
    #     of continuation lines) adopted from existing and prior data
    #     sets from ISIS2, PDS, JAXA, ISRO, ..., and extensions used
    #     only within ISIS3 files (cub, net). This is one of the
    #     reasons using ISIS cube files as an archive format has been
    #     strongly discouraged. So to answer your question, there is
    #     no published specification for ISIS3 PVL.

    # The ISIS parser (at least <=3.9) doesn't recognize the
    # 'BEGIN_<GROUP|OBJECT>' construction, which is why we must
    # have a separate grammar object.  Since we're at it, we might
    # as well use the *_pref_keywords to indicate the CamelCase
    # that ISIS folks are expecting.
    group_pref_keywords = ("Group", "End_Group")
    group_keywords = {"GROUP": "END_GROUP"}
    object_pref_keywords = ("Object", "End_Object")
    object_keywords = {"OBJECT": "END_OBJECT"}

    # A single-line comment that starts with the octothorpe (#) is not part
    # of PVL or ODL, but it is used when ISIS writes out comments.
    comments = (("/*", "*/"), ("#", "\n"))

    def __init__(self):
        # ISIS allows for + characters in Unquoted String values.
        self.reserved_characters = tuple(
            self.adjust_reserved_characters(self.reserved_characters)
        )

    @staticmethod
    def adjust_reserved_characters(chars: abc.Iterable):
        # ISIS allows for + characters in Unquoted String values.
        # Removing the plus from the reserved characters allows for
        # that, but might lead to other parsing errors, so be on the lookout.
        rc = list(chars)
        rc.remove("+")
        return rc


class OmniGrammar(PVLGrammar):
    """A broadly permissive grammar.

    This grammar does not follow a specification, but is meant to allow
    the broadest possible ingestion of PVL-like text that is found.

    This grammar should not be used to write out Python objects to PVL,
    instead please use one of the grammars that follows a published
    specification, like the PVLGrammar or the ODLGrammar.
    """

    # Interestingly, a single-line comment that starts with the
    # octothorpe (#) is neither part of PVL nor ODL, but people use
    # it all the time.
    comments = (("/*", "*/"), ("#", "\n"))

    # ODL allows the radix to be from 2 to 16, and allows the sign to be
    # 'inside' the octothorpes, so we need to allow for the wide variety
    # of radix, and the variational placement of the optional sign:
    # [sign]radix#[sign]non_decimal_integer#
    _ss = r"(?P<second_sign>[+-]?)"
    nondecimal_pre_re = re.compile(
        PVLGrammar._s + fr"(?P<radix>[2-9]|1[0-6])#{_ss}"
    )
    nondecimal_re = re.compile(
        nondecimal_pre_re.pattern + r"(?P<non_decimal>[0-9A-Fa-f]+)#"
    )

    def __init__(self):
        # Handle the fact that ISIS writes out unquoted plus signs.
        # See ISISGrammar for details.
        self.reserved_characters = tuple(
            ISISGrammar.adjust_reserved_characters(self.reserved_characters)
        )
