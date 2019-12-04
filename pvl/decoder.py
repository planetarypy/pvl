# -*- coding: utf-8 -*-
'''Parameter Value Language decoder.

   The definition of PVL used in this module is from the Consultive
   Committee for Space Data Systems, and their Parameter Value
   Language Specification (CCSD0006 and CCSD0008), CCSDS 6441.0-B-2,
   referred to as the Blue Book with a date of June 2000.

   The decoder deals with converting strings given to it (typically
   by the parser) to the appropriate Python type.
'''
import re
from datetime import datetime
from itertools import repeat, chain
from time import strptime
from warnings import warn

from .grammar import grammar as Grammar


def for_try_except(exception, function, *iterable):
    '''Return the result of the first successful application of *function*
       to an element of *iterable*.  If the *function* raises an Exception
       of type *exception*, it will continue to the next item of *iterable*.
       If there are no successful applications an Exception of type
       *exception* will be raised.

       If additional *iterable* arguments are passed, *function* must
       take that many arguments and is applied to the items from
       all iterables in parallel (like ``map()``). With multiple iterables,
       the iterator stops when the shortest iterable is exhausted.
    '''
    for tup in zip(*iterable):
        try:
            return function(*tup)
        except exception:
            pass

    raise exception


class EmptyValueAtLine(str):
    """Empty string to be used as a placeholder for a parameter without a value

    When a label is contains a parameter without a value, it is considered a
    broken label. To rectify the broken parameter-value pair, the parameter is
    set to have a value of EmptyValueAtLine. The empty value is an empty
    string and can be treated as such. It also contains and requires as an
    argument the line number of the error.

    Parameters
    ----------
    lineno : int
        The line number of the broken parameter-value pair

    Attributes
    ----------
    lineno : int
        The line number of the broken parameter-value pai

    Examples
    --------
    >>> from pvl.decoder import EmptyValueAtLine
    >>> EV1 = EmptyValueAtLine(1)
    >>> EV1
    EmptyValueAtLine(1 does not have a value. Treat as an empty string)
    >>> EV1.lineno
    1
    >>> print(EV1)

    >>> EV1 + 'foo'
    'foo'
    >>> # Can be turned into an integer and float as 0:
    >>> int(EV1)
    0
    >>> float(EV1)
    0.0
    """

    def __new__(cls, lineno, *args, **kwargs):
        self = super(EmptyValueAtLine, cls).__new__(cls, '')
        self.lineno = lineno
        return self

    def __int__(self):
        return 0

    def __float__(self):
        return 0.0

    def __repr__(self):
        return ('{}({} does not '.format(type(self).__name__, self.lineno) +
                'have a value. Treat as an empty string)')


class PVLDecoder(object):

    def __init__(self, grammar=None):
        self.strict = True
        self.errors = []

        if grammar is None:
            self.grammar = Grammar()
        elif isinstance(grammar, Grammar):
            self.grammar = grammar
        else:
            raise Exception

    def decode(self, value: str):
        '''With no hints about what ``value`` might be, try everything.'''
        return decode_simple_value(value)

    def decode_simple_value(self, value: str):
        '''Takes a Simple Value and attempts to convert it to the appropriate
           Python type.

            <Simple-Value> ::= (<Date-Time> | <Numeric> | <String>)
        '''
        try:  # Quoted String
            return self.decode_quoted_string(value)
        except ValueError:
            pass

        try:  # Non-Decimal
            return self.decode_non_decimal(value)
        except ValueError:
            pass

        try:  # Decimal
            return self.decode_decimal(value)
        except ValueError:
            pass

        try:  # Date/Time
            return self.decode_datetime(value)
        except ValueError:
            pass

        return self.decode_unquoted_string(value)  # Unquoted String

    def decode_unquoted_string(self, value: str) -> str:
        '''Takes a Simple Value and attempts to convert it to a plain
           ``str``.
        '''
        for c in chain.from_iterable(self.grammar.comments):
            if c in value:
                raise ValueError('Expected a Simple Value, but encountered a '
                                 f'comment in "{self}"')

        for ws in self.grammar.whitespace:
            if ws in value:
                raise ValueError('Expected a Simple Value, but encountered '
                                 f'some whitespace in "{self}"')

        for sp in self.grammar.reserved_characters:
            if sp in value:
                raise ValueError('Expected a Simple Value, but encountered '
                                 f'a spcial character "{sp}" in "{self}"')

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
        '''Removes the allowed PVL quote characters from the either
           end of the input str and returns the resulting str.
        '''
        for q in self.grammar.quotes:
            if(value.startswith(q) and
               value.endswith(q) and
               len(value) > 1):
                return str(value[1:-1])
        raise ValueError(f'The object "{value}" is not a PVL Quoted String.')

    @staticmethod
    def decode_decimal(value: str):
        # Returns int or float
        try:
            return int(value, base=10)
        except ValueError:
            return float(value)

    def decode_non_decimal(self, value: str) -> int:
        # Non-Decimal (Binary, Hex, and Octal)
        for nd_re in (self.grammar.binary_re,
                      self.grammar.octal_re,
                      self.grammar.hex_re):
            match = nd_re.fullmatch(value)
            if match is not None:
                d = match.groupdict('')
                return int(d['sign'] + d['non_decimal'], base=int(d['radix']))
        raise ValueError

    def decode_datetime(self, value: str):
        '''Takes a string and attempts to convert it to the appropriate
           Python ``datetime`` ``time``, ``date``, or ``datetime``
           type based on the PVL standard, or in one case, a ``str``.

           The PVL standard allows for the seconds value to range
           from zero to 60, so that the 60 can accomodate leap
           seconds.  However, the Python ``datetime`` classes don't
           support second values for more than 59 seconds.

           If a time with 60 seconds is encountered, it will not be
           returned as a datetime object, but simply as a string.

           The user can then then try and use the ``time`` module
           to parse this string into a ``time.struct_time``.  We
           chose not to do this with pvl because ``time.struct_time``
           is a full *datetime* like object, even if it parsed
           only a *time* like object, the year, month, and day
           values in the ``time.struct_time`` would default, which
           could be misleading.

           Alternately, the pvl.grammar.grammar class contains
           two regexes: ``leap_second_Ymd_re`` and ``leap_second_Yj_re``
           which could be used along with the ``re.match`` object's
           ``groupdict()`` function to extract the string representations
           of the various numerical values, cast them to the appropriate
           numerical types, and do something useful with them.
        '''
        try:
            return for_try_except(ValueError, datetime.strptime,
                                  repeat(value),
                                  self.grammar.date_formats).date()
        except ValueError:
            try:
                return for_try_except(ValueError, datetime.strptime,
                                      repeat(value),
                                      self.grammar.time_formats).time()
            except ValueError:
                try:
                    return for_try_except(ValueError, datetime.strptime,
                                          repeat(value),
                                          self.grammar.datetime_formats)
                except ValueError:
                    pass

        # if we can regex a 60-second time, return str
        for r in (self.grammar.leap_second_Ymd_re,
                  self.grammar.leap_second_Yj_re):
            if r.fullmatch(value) is not None:
                return str(value)

        if self.strict:
            raise ValueError
        else:
            return self.decode_dateutil(value)

    @staticmethod
    def decode_dateutil(value: str):
        '''Takes a string and attempts to convert it to the appropriate
           Python datetime time, date, or datetime by using the 3rd party
           dateutil library (if present) to parse ISO 8601 datetime strings,
           which have more variety than those allowed by the PVL
           specification.
        '''
        try:
            from dateutil.parser import isoparser
            isop = isoparser()

            if(len(value) > 3
               and value[-2] == '+'
               and value[-1].isdigit()):
                # This technically means that we accept slight more formats
                # than ISO 8601 strings, since under that specification, two
                # digits after the '+' are required for an hour offset, but if
                # we find only one digit, we'll just assume it means an hour
                # and insert a zero so that it can be parsed.
                tokens = value.rpartition('+')
                value = tokens[0] + '+0' + tokens[-1]

            try:
                return isop.parse_isodate(value)
            except ValueError:
                try:
                    return isop.parse_isotime(value)
                except ValueError:
                    return isop.isoparse(value)

        except ImportError:
            warn('The dateutil library is not present, so date and time '
                 'formats beyond the PVL set will be left as strings '
                 'instead of being parsed and returned as datetime objects.',
                 ImportWarning)

        raise ValueError
