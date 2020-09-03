# -*- coding: utf-8 -*-
"""Parameter Value Language decoder.

The definition of PVL used in this module is based on the Consultive
Committee for Space Data Systems, and their Parameter Value
Language Specification (CCSD0006 and CCSD0008), CCSDS 6441.0-B-2,
referred to as the Blue Book with a date of June 2000.

A decoder deals with converting strings given to it (typically
by the parser) to the appropriate Python type.
"""
# Copyright 2015, 2017, 2019-2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import re
from datetime import datetime, timedelta, timezone
from itertools import repeat, chain
from warnings import warn

from .grammar import PVLGrammar, ODLGrammar
from .collections import Quantity
from .exceptions import QuantityError


def for_try_except(exception, function, *iterable):
    """Return the result of the first successful application of *function*
    to an element of *iterable*.  If the *function* raises an Exception
    of type *exception*, it will continue to the next item of *iterable*.
    If there are no successful applications an Exception of type
    *exception* will be raised.

    If additional *iterable* arguments are passed, *function* must
    take that many arguments and is applied to the items from
    all iterables in parallel (like ``map()``). With multiple iterables,
    the iterator stops when the shortest iterable is exhausted.
    """
    for tup in zip(*iterable):
        try:
            return function(*tup)
        except exception:
            pass

    raise exception


class PVLDecoder(object):
    """A decoder based on the rules in the CCSDS-641.0-B-2 'Blue Book'
    which defines the PVL language.

    :param grammar: defaults to a :class:`pvl.grammar.PVLGrammar`, but can
        be any object that implements the :class:`pvl.grammar` interface.

    :param quantity_cls: defaults to :class:`pvl.collections.Quantity`, but
        could be any class object that takes two arguments, where the
        first is the value, and the second is the units value.
    """

    def __init__(self, grammar=None, quantity_cls=None):
        self.errors = []

        if grammar is None:
            self.grammar = PVLGrammar()
        elif isinstance(grammar, PVLGrammar):
            self.grammar = grammar
        else:
            raise Exception

        if quantity_cls is None:
            self.quantity_cls = Quantity
        else:
            self.quantity_cls = quantity_cls

    def decode(self, value: str):
        """Returns a Python object based on *value*."""
        return self.decode_simple_value(value)

    def decode_simple_value(self, value: str):
        """Returns a Python object based on *value*, assuming
        that *value* can be decoded as a PVL Simple Value::

         <Simple-Value> ::= (<Date-Time> | <Numeric> | <String>)
        """
        for d in (
            self.decode_quoted_string,
            self.decode_non_decimal,
            self.decode_decimal,
            self.decode_datetime,
        ):
            try:
                return d(value)
            except ValueError:
                pass

        if value.casefold() == self.grammar.none_keyword.casefold():
            return None

        if value.casefold() == self.grammar.true_keyword.casefold():
            return True

        if value.casefold() == self.grammar.false_keyword.casefold():
            return False

        return self.decode_unquoted_string(value)

    def decode_unquoted_string(self, value: str) -> str:
        """Returns a Python ``str`` if *value* can be decoded
        as an unquoted string, based on this decoder's grammar.
        Raises a ValueError otherwise.
        """
        for coll in (
            ("a comment", chain.from_iterable(self.grammar.comments)),
            ("some whitespace", self.grammar.whitespace),
            ("a special character", self.grammar.reserved_characters),
        ):
            for item in coll[1]:
                if item in value:
                    raise ValueError(
                        "Expected a Simple Value, but encountered "
                        f'{coll[0]} in "{self}": "{item}".'
                    )

        agg_keywords = self.grammar.aggregation_keywords.items()
        for kw in chain.from_iterable(agg_keywords):
            if kw.casefold() == value.casefold():
                raise ValueError(
                    "Expected a Simple Value, but encountered "
                    f'an aggregation keyword: "{value}".'
                )

        for es in self.grammar.end_statements:
            if es.casefold() == value.casefold():
                raise ValueError(
                    "Expected a Simple Value, but encountered "
                    f'an End-Statement: "{value}".'
                )

        # This try block is going to look illogical.  But the decode
        # rules for Unquoted Strings spell out the things that they
        # cannot be, so if it *can* be a datetime, then it *can't* be
        # an Unquoted String, which is why we raise if it succeeds,
        # and pass if it fails:
        try:
            self.decode_datetime(value)
            raise ValueError
        except ValueError:
            pass

        return str(value)

    def decode_quoted_string(self, value: str) -> str:
        """Returns a Python ``str`` if *value* begins and ends
        with matching quote characters based on this decoder's
        grammar.  Raises ValueError otherwise.
        """
        for q in self.grammar.quotes:
            if value.startswith(q) and value.endswith(q) and len(value) > 1:
                return str(value[1:-1])
        raise ValueError(f'The object "{value}" is not a PVL Quoted String.')

    @staticmethod
    def decode_decimal(value: str):
        """Returns a Python ``int`` or ``float`` as appropriate
        based on *value*.  Raises a ValueError otherwise.
        """
        # Returns int or float
        try:
            return int(value, base=10)
        except ValueError:
            return float(value)

    def decode_non_decimal(self, value: str) -> int:
        """Returns a Python ``int`` as decoded from *value*
        on the assumption that *value* conforms to a
        non-decimal integer value as defined by this decoder's
        grammar, raises ValueError otherwise.
        """
        # Non-Decimal (Binary, Hex, and Octal)
        for nd_re in (
            self.grammar.binary_re,
            self.grammar.octal_re,
            self.grammar.hex_re,
        ):
            match = nd_re.fullmatch(value)
            if match is not None:
                d = match.groupdict("")
                return int(d["sign"] + d["non_decimal"], base=int(d["radix"]))
        raise ValueError

    def decode_datetime(self, value: str):
        """Takes a string and attempts to convert it to the appropriate
        Python ``datetime`` ``time``, ``date``, or ``datetime``
        type based on this decoder's grammar, or in one case, a ``str``.

        The PVL standard allows for the seconds value to range
        from zero to 60, so that the 60 can accomodate leap
        seconds.  However, the Python ``datetime`` classes don't
        support second values for more than 59 seconds.

        Since the PVL Blue Book says that all PVl Date/Time Values
        are represented in Universal Coordinated Time, then all
        datetime objects that are returned datetime Python objects
        should be timezone "aware."  A datetime.date object is always
        "naive" but any datetime.time or datetime.datetime objects
        returned from this function will be "aware."

        If a time with 60 seconds is encountered, it will not be
        returned as a datetime object (since that is not representable
        via Python datetime objects), but simply as a string.

        The user can then then try and use the ``time`` module
        to parse this string into a ``time.struct_time``.  We
        chose not to do this with pvl because ``time.struct_time``
        is a full *datetime* like object, even if it parsed
        only a *time* like object, the year, month, and day
        values in the ``time.struct_time`` would default, which
        could be misleading.

        Alternately, the pvl.grammar.PVLGrammar class contains
        two regexes: ``leap_second_Ymd_re`` and ``leap_second_Yj_re``
        which could be used along with the ``re.match`` object's
        ``groupdict()`` function to extract the string representations
        of the various numerical values, cast them to the appropriate
        numerical types, and do something useful with them.
        """
        try:
            # datetime.date objects will always be naive, so just return:
            return for_try_except(
                ValueError,
                datetime.strptime,
                repeat(value),
                self.grammar.date_formats,
            ).date()
        except ValueError:
            # datetime.time and datetime.datetime might be either:
            d = None
            try:
                d = for_try_except(
                    ValueError,
                    datetime.strptime,
                    repeat(value),
                    self.grammar.time_formats,
                ).time()
            except ValueError:
                try:
                    d = for_try_except(
                        ValueError,
                        datetime.strptime,
                        repeat(value),
                        self.grammar.datetime_formats,
                    )
                except ValueError:
                    pass
            if d is not None:
                if d.utcoffset() is None:
                    return d.replace(tzinfo=timezone.utc)
                else:
                    return d

        # if we can regex a 60-second time, return str
        if self.is_leap_seconds(value):
            return str(value)
        else:
            raise ValueError

    def is_leap_seconds(self, value: str) -> bool:
        """Returns True if *value* is a time that matches the
        grammar's definition of a leap seconds time (a time string with
        a value of 60 for the seconds value).  False otherwise."""
        for r in (
            self.grammar.leap_second_Ymd_re,
            self.grammar.leap_second_Yj_re,
        ):
            if r is not None and r.fullmatch(value) is not None:
                return True
        else:
            return False

    def decode_quantity(self, value, unit):
        """Returns a Python object that represents a value with
           an associated unit, based on the values provided via
           *value* and *unit*.  This function creates an object
           based on the decoder's *quantity_cls*.
        """
        try:
            return self.quantity_cls(value, str(unit))
        except ValueError as err:
            raise QuantityError(err)


class ODLDecoder(PVLDecoder):
    """A decoder based on the rules in the PDS3 Standards Reference
    (version 3.8, 27 Feb 2009) Chapter 12: Object Description
    Language Specification and Usage.

    Extends PVLDecoder, and if *grammar* is not specified, it will
    default to an ODLGrammar() object.
    """

    def __init__(self, grammar=None, quantity_cls=None):
        self.errors = []

        if grammar is None:
            super().__init__(grammar=ODLGrammar(), quantity_cls=quantity_cls)
        else:
            super().__init__(grammar=grammar, quantity_cls=quantity_cls)

    def decode_datetime(self, value: str):
        """Extends parent function to also deal with datetimes
        and times with a time zone offset.

        If it cannot, it will raise a ValueError.
        """

        try:
            return super().decode_datetime(value)
        except ValueError:
            # if there is a +HH:MM or a -HH:MM suffix that
            # can be stripped, then we're in business.
            # Otherwise ...
            match = re.fullmatch(
                r"(?P<dt>.+?)"  # the part before the sign
                r"(?P<sign>[+-])"  # required sign
                r"(?P<hour>0?[0-9]|1[0-2])"  # 0 to 12
                fr"(?:{self.grammar._M_frag})?",  # Minutes
                value,
            )
            if match is not None:
                gd = match.groupdict(default=0)
                dt = super().decode_datetime(gd["dt"])
                offset = timedelta(
                    hours=int(gd["hour"]), minutes=int(gd["minute"])
                )
                if gd["sign"] == "-":
                    offset = -1 * offset
                return dt.replace(tzinfo=timezone(offset))
            raise ValueError

    def decode_non_decimal(self, value: str) -> int:
        """Extends parent function by allowing the wider variety of
        radix values that ODL permits over PVL.
        """
        match = self.grammar.nondecimal_re.fullmatch(value)
        if match is not None:
            d = match.groupdict("")
            return int(d["sign"] + d["non_decimal"], base=int(d["radix"]))
        raise ValueError

    def decode_quoted_string(self, value: str) -> str:
        """Extends parent function because the
        ODL specification allows for a dash (-) line continuation
        character that results in the dash, the line end, and any
        leading whitespace on the next line to be removed.  It also
        allows for a sequence of format effectors surrounded by
        spacing characters to be collapsed to a single space.
        """
        s = super().decode_quoted_string(value)

        # Deal with dash (-) continuation:
        # sp = ''.join(self.grammar.spacing_characters)
        fe = "".join(self.grammar.format_effectors)
        ws = "".join(self.grammar.whitespace)
        nodash = re.sub(fr"-[{fe}][{ws}]*", "", s)

        # Originally thought that only format effectors surrounded
        # by whitespace was to be collapsed
        # foo = re.sub(fr'[{sp}]*[{fe}]+[{sp}]*', ' ', nodash)

        # But really it collapses all whitespace and strips lead and trail.
        return re.sub(fr"[{ws}]+", " ", nodash.strip(ws))


class OmniDecoder(ODLDecoder):
    """A permissive decoder that attempts to parse all forms of
    "PVL" that are thrown at it.

    Extends ODLDecoder.
    """

    def decode_non_decimal(self, value: str) -> int:
        """Extends parent function by allowing a plus or
        minus sign to be in two different positions
        in a non-decimal number, since PVL has one
        specification, and ODL has another.
        """
        # Non-Decimal with a variety of radix values and sign
        # positions.
        match = self.grammar.nondecimal_re.fullmatch(value)
        if match is not None:
            d = match.groupdict("")
            if "second_sign" in d:
                if d["sign"] != "" and d["second_sign"] != "":
                    raise ValueError(
                        f'The non-decimal value, "{value}", ' "has two signs."
                    )
                elif d["sign"] != "":
                    sign = d["sign"]
                else:
                    sign = d["second_sign"]
            else:
                sign = d["sign"]

            return int(sign + d["non_decimal"], base=int(d["radix"]))
        raise ValueError

    def decode_datetime(self, value: str):
        """Returns an appropriate Python datetime time, date, or datetime
        object by using the 3rd party dateutil library (if present)
        to parse an ISO 8601 datetime string in *value*.  If it cannot,
        or the dateutil library is not present, it will raise a
        ValueError.
        """

        try:
            return super().decode_datetime(value)
        except ValueError:
            try:
                from dateutil.parser import isoparser

                isop = isoparser()

                if len(value) > 3 and value[-2] == "+" and value[-1].isdigit():
                    # This technically means that we accept slightly more
                    # formats than ISO 8601 strings, since under that
                    # specification, two digits after the '+' are required
                    # for an hour offset, but ODL doesn't have this
                    # requirement.  If we find only one digit, we'll
                    # just assume it means an hour and insert a zero so
                    # that it can be parsed.
                    tokens = value.rpartition("+")
                    value = tokens[0] + "+0" + tokens[-1]

                try:
                    return isop.parse_isodate(value)
                except ValueError:
                    try:
                        return isop.parse_isotime(value)
                    except ValueError:
                        return isop.isoparse(value)

            except ImportError:
                warn(
                    "The dateutil library is not present, so more "
                    "exotic date and time formats beyond the PVL/ODL "
                    "set cannot be parsed.",
                    ImportWarning,
                )

            raise ValueError
