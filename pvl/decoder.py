# -*- coding: utf-8 -*-
from six import b

import re
import itertools
import datetime
import pytz

from .stream import BufferedStream, ByteStream
from ._collections import Label, LabelGroup, LabelObject, Units


class ParseError(ValueError):
    """Subclass of ValueError with the following additional properties:
    msg: The unformatted error message
    pos: The start index of where parsing failed
    lineno: The line corresponding to pos
    colno: The column corresponding to pos
    """
    def __init__(self, msg, pos, lineno, colno):
        errmsg = '%s: line %d column %d (char %d)' % (msg, lineno, colno, pos)
        super(ParseError, self).__init__(errmsg)
        self.msg = msg
        self.pos = pos
        self.lineno = lineno
        self.colno = colno


RE_FRAGMENTS = {
    'int': r'(?:[-+]?[0-9]+)',
    'float': r'(?:[-+]?(?:[0-9]+\.[0-9]*|[0-9]*\.[0-9]+))',
    'day_of_month': r'(0[1-9]|[1-2][0-9]|3[0-1])',
    'day_of_year': r'(00[1-9]|0[1-9][0-9]|[1-2][0-9][0-9]|3[0-5][0-9]|36[0-6])',
    'hour': r'([0-1][0-9]|2[0-3])',
    'minute': r'([0-5][0-9])',
    'month': r'(0[1-9]|1[0-2])',
    # 60 is allowed for leap seconds
    'seconds': r'(?:([0-5][0-9]|60)(?:\.([0-9]*))?)',
    'year': r'([0-9][0-9][0-9][0-9])',
    'tz': r'(Z|z|[+-][0-1]?[0-9]|[+-]2[0-3])'
}

RE_FRAGMENTS['date_month_day'] = r'%(year)s-%(month)s-%(day_of_month)s' % RE_FRAGMENTS  # noqa
RE_FRAGMENTS['date_day_of_year'] = r'%(year)s-%(day_of_year)s' % RE_FRAGMENTS
RE_FRAGMENTS['time'] = r'%(hour)s:%(minute)s(?:\:%(seconds)s)?%(tz)s?' % RE_FRAGMENTS  # noqa

INTEGER_RE = r'^%(int)s$' % RE_FRAGMENTS
FLOAT_RE = r'^%(float)s$' % RE_FRAGMENTS
EXPONENT_RE = r'(?:%(int)s|%(float)s)(?:e|E)(?:%(int)s)' % RE_FRAGMENTS
LINE_CONTINUATION_RE = r'-(?:\r\n|\n|\r)[ \t\v\f]*'
TIME_RE = r'^%(time)s$' % RE_FRAGMENTS
DATE_MONTH_DAY_RE = r'^%(date_month_day)s$' % RE_FRAGMENTS
DATE_DAY_OF_YEAR_RE = r'^%(date_day_of_year)s$' % RE_FRAGMENTS
DATETIME_MONTH_DAY_RE = r'^%(date_month_day)sT%(time)s$' % RE_FRAGMENTS
DATETIME_DAY_OF_YEAR_RE = r'^%(date_day_of_year)sT%(time)s$' % RE_FRAGMENTS


def char_set(chars):
    return set([b(c) for c in chars])


class LabelDecoder(object):
    whitespace = char_set(' \r\n\t\v\f')
    newline_chars = char_set('\r\n')
    reserved_chars = char_set('&<>\'{},[]=!#()%";|')
    delimiter_chars = whitespace | reserved_chars
    eof_chars = (b'', b'\0')

    quote_marks = (b'"', b"'")
    null_tokens = (b'Null', b'NULL')
    end_tokens = (b'End', b'END')

    true_tokens = (b'TRUE', b'True', b'true')
    false_tokens = (b'FALSE', b'False', b'false')
    boolean_tokens = true_tokens + false_tokens

    begin_group_tokens = (b'Group', b'GROUP', b'BEGIN_GROUP')
    end_group_tokens = (b'End_Group', b'END_GROUP')

    begin_object_tokens = (b'Object', b'OBJECT', b'BEGIN_OBJECT')
    end_object_tokens = (b'End_Object', b'END_OBJECT')

    seporator = b','
    radix_symbole = b'#'
    statement_delimiter = b';'
    continuation_symbole = b'-'
    assignment_symbole = b'='

    begin_comment = b'/*'
    end_comment = b'*/'
    line_comment = b'#'

    begin_sequence = b'('
    end_sequence = b')'

    begin_set = b'{'
    end_set = b'}'

    begin_units = b'<'
    end_units = b'>'

    plus_sign = b'+'
    minus_sign = b'-'
    signs = set([plus_sign, minus_sign])

    binary_chars = (b'0', b'1')
    octal_chars = char_set('01234567')
    decimal_chars = char_set('0123456789')
    hex_chars = char_set('0123456789ABCDEFabcdef')

    integer_re = re.compile(b(INTEGER_RE))
    float_re = re.compile(b(FLOAT_RE))
    exponent_re = re.compile(b(EXPONENT_RE))
    line_continuation_re = re.compile(b(LINE_CONTINUATION_RE))
    time_re = re.compile(b(TIME_RE))
    date_month_day_re = re.compile(b(DATE_MONTH_DAY_RE))
    date_day_of_year_re = re.compile(b(DATE_DAY_OF_YEAR_RE))
    datetime_month_day_re = re.compile(b(DATETIME_MONTH_DAY_RE))
    datetime_day_of_year_re = re.compile(b(DATETIME_DAY_OF_YEAR_RE))

    formatting_chars = {
        b'\\n': b'\n',
        b'\\t': b'\t',
        b'\\f': b'\f',
        b'\\v': b'\v',
        b'\\\\': b'\\',
    }

    def peek(self, stream, n, offset=0):
        return stream.peek(n + offset)[offset:n]

    def raise_error(self, msg, stream):
        raise ParseError(msg, stream.pos, stream.lineno, stream.colno)

    def optional(self, stream, token):
        if not self.has_next(token, stream):
            return
        self.expect(stream, token)

    def expect(self, stream, expected):
        actual = stream.read(len(expected))
        if actual == expected:
            return
        msg = 'Unexpected token %r (expected %r)'
        self.raise_error(msg % (actual, expected), stream)

    def expect_in(self, stream, tokens):
        for token in tokens:
            if self.has_next(token, stream):
                break
        self.expect(stream, token)

    def raise_unexpected(self, stream, token=None):
        if token is None:
            token = self.peek(stream, 1)
        self.raise_error('Unexpected token %r' % token, stream)

    def raise_unexpected_eof(self, stream):
        self.raise_error('Unexpected EOF', stream)

    def has_eof(self, stream, offset=0):
        return self.peek(stream, 1, offset) in self.eof_chars

    def has_next(self, token, stream, offset=0):
        return self.peek(stream, len(token), offset) == token

    def has_delimiter(self, stream, offset=0):
        if self.has_eof(stream, offset):
            return True

        if self.has_comment(stream, offset):
            return True

        if self.peek(stream, 1, offset) in self.delimiter_chars:
            return True

    def has_token_in(self, tokens, stream):
        for token in tokens:
            if not self.has_token(token, stream):
                continue
            return token

    def has_token(self, token, stream):
        if not self.has_next(token, stream):
            return False
        return self.has_delimiter(stream, len(token))

    def next_token(self, stream):
        token = b''
        while not self.has_delimiter(stream):
            token += stream.read(1)
        return token

    def peek_next_token(self, stream):
        for offset in itertools.count():
            if self.has_delimiter(stream, offset):
                break
        return self.peek(stream, offset)

    def decode(self, stream):
        if isinstance(stream, bytes):
            stream = ByteStream(stream)
        else:
            stream = BufferedStream(stream)

        label = Label(self.parse_block(stream, self.has_end))
        self.skip_end(stream)
        return label

    def parse_block(self, stream, has_end):
        """
        PVLModuleContents ::= (Statement | WSC)* EndStatement?
        AggrObject ::= BeginObjectStmt AggrContents EndObjectStmt
        AggrGroup ::= BeginGroupStmt AggrContents EndGroupStmt
        AggrContents := WSC Statement (WSC | Statement)*
        """
        statements = []
        while 1:
            self.skip_whitespace_or_comment(stream)

            if has_end(stream):
                return statements

            statements.append(self.parse_statement(stream))

    def skip_whitespace_or_comment(self, stream):
        while 1:
            if self.has_whitespace(stream):
                self.skip_whitespace(stream)
                continue

            if self.has_comment(stream):
                self.skip_comment(stream)
                continue

            return

    def skip_statement_delimiter(self, stream):
        """Ensure that a Statement Delimiter consists of one semicolon,
        optionally preceded by multiple White Spaces and/or Comments, OR one or
        more Comments and/or White Space sequences.

        StatementDelim ::= WSC (SemiColon | WhiteSpace | Comment)
                         | EndProvidedOctetSeq

        """
        self.skip_whitespace_or_comment(stream)
        self.optional(stream, self.statement_delimiter)

    def parse_statement(self, stream):
        """
        Statement ::= AggrGroup
                    | AggrObject
                    | AssignmentStmt
        """
        if self.has_group(stream):
            return self.parse_group(stream)

        if self.has_object(stream):
            return self.parse_object(stream)

        if self.has_assignment(stream):
            return self.parse_assignment(stream)

        self.raise_unexpected(stream)

    def has_whitespace(self, stream, offset=0):
        return self.peek(stream, 1, offset) in self.whitespace

    def skip_whitespace(self, stream):
        while self.peek(stream, 1) in self.whitespace:
            stream.read(1)

    def has_multiline_comment(self, stream, offset=0):
        return self.has_next(self.begin_comment, stream, offset)

    def has_line_comment(self, stream, offset=0):
        return self.has_next(self.line_comment, stream, offset)

    def has_comment(self, stream, offset=0):
        return (
            self.has_line_comment(stream, offset) or
            self.has_multiline_comment(stream, offset)
        )

    def skip_comment(self, stream):
        if self.has_line_comment(stream):
            end_comment = b'\n'
        else:
            end_comment = self.end_comment

        while 1:
            next = self.peek(stream, len(end_comment))
            if not next:
                self.raise_unexpected_eof(stream)

            if next == end_comment:
                break

            stream.read(1)
        stream.read(len(end_comment))

    def has_end(self, stream):
        """
        EndStatement ::=
            EndKeyword (SemiColon | WhiteSpace | Comment | EndProvidedOctetSeq)
        """
        for token in self.end_tokens:
            if not self.has_next(token, stream):
                continue

            offset = len(token)

            if self.has_eof(stream, offset):
                return True

            if self.has_whitespace(stream, offset):
                return True

            if self.has_comment(stream, offset):
                return True

            if self.has_next(self.statement_delimiter, stream, offset):
                return True

        return self.has_eof(stream)

    def skip_end(self, stream):
        if self.has_eof(stream):
            return

        self.expect_in(stream, self.end_tokens)
        self.skip_whitespace_or_comment(stream)
        self.optional(stream, self.statement_delimiter)

    def has_group(self, stream):
        return self.has_token_in(self.begin_group_tokens, stream)

    def parse_end_assignment(self, stream, expected):
        self.skip_whitespace_or_comment(stream)

        if not self.has_next(self.assignment_symbole, stream):
            return

        self.ensure_assignment(stream)

        name = self.next_token(stream)
        if name == expected:
            return

        self.raise_unexpected(stream, name)

    def parse_group(self, stream):
        """Block Name must match Block Name in paired End Group Statement if
        Block Name is present in End Group Statement.

        BeginGroupStmt ::=
            BeginGroupKeywd WSC AssignmentSymbol WSC BlockName StatementDelim
        """
        self.expect_in(stream, self.begin_group_tokens)

        self.ensure_assignment(stream)
        name = self.next_token(stream)

        self.skip_statement_delimiter(stream)
        statements = self.parse_block(stream, self.has_end_group)

        self.expect_in(stream, self.end_group_tokens)
        self.parse_end_assignment(stream, name)
        self.skip_statement_delimiter(stream)

        return name.decode('utf-8'), LabelGroup(statements)

    def has_end_group(self, stream):
        """
        EndGroupLabel :=  AssignmentSymbol WSC BlockName
        EndGroupStmt := EndGroupKeywd WSC EndGroupLabel? StatementDelim
        """
        return self.has_token_in(self.end_group_tokens, stream)

    def has_object(self, stream):
        return self.has_token_in(self.begin_object_tokens, stream)

    def parse_object(self, stream):
        """Block Name must match Block Name in paired End Object Statement
        if Block Name is present in End Object Statement StatementDelim.

        BeginObjectStmt ::=
            BeginObjectKeywd WSC AssignmentSymbol WSC BlockName StatementDelim
        """
        self.expect_in(stream, self.begin_object_tokens)

        self.ensure_assignment(stream)
        name = self.next_token(stream)

        self.skip_statement_delimiter(stream)
        statements = self.parse_block(stream, self.has_end_object)

        self.expect_in(stream, self.end_object_tokens)
        self.parse_end_assignment(stream, name)
        self.skip_statement_delimiter(stream)

        return name.decode('utf-8'), LabelObject(statements)

    def has_end_object(self, stream):
        """
        EndObjectLabel ::= AssignmentSymbol WSC BlockName
        EndObjectStmt ::= EndObjectKeywd WSC EndObjectLabel? StatementDelim
        """
        return self.has_token_in(self.end_object_tokens, stream)

    def has_assignment(self, stream):
        return not self.has_delimiter(stream)

    def ensure_assignment(self, stream):
        self.skip_whitespace_or_comment(stream)
        self.expect(stream, self.assignment_symbole)
        self.skip_whitespace_or_comment(stream)

    def parse_assignment(self, stream):
        """
        AssignmentStmt ::= Name WSC AssignmentSymbol WSC Value StatementDelim
        """
        name = self.next_token(stream)
        self.ensure_assignment(stream)
        value = self.parse_value(stream)
        self.skip_statement_delimiter(stream)
        return name.decode('utf-8'), value

    def parse_value(self, stream):
        """
        Value ::= (SimpleValue | Set | Sequence) WSC UnitsExpression?
        """
        if self.has_sequence(stream):
            value = self.parse_sequence(stream)
        elif self.has_set(stream):
            value = self.parse_set(stream)
        else:
            value = self.parse_simple_value(stream)

        self.skip_whitespace_or_comment(stream)

        if self.has_units(stream):
            return Units(value, self.parse_units(stream))

        return value

    def parse_iterable(self, stream, start, end):
        """
        Sequence ::= SequenceStart WSC SequenceValue? WSC SequenceEnd
        Set := SetStart WSC SequenceValue? WSC SetEnd
        SequenceValue ::= Value (WSC SeparatorSymbol WSC Value)*
        """
        values = []

        self.expect(stream, start)
        self.skip_whitespace_or_comment(stream)

        if self.has_next(end, stream):
            self.expect(stream, end)
            return values

        while 1:
            self.skip_whitespace_or_comment(stream)
            values.append(self.parse_value(stream))
            self.skip_whitespace_or_comment(stream)

            if self.has_next(end, stream):
                self.expect(stream, end)
                return values

            self.expect(stream, self.seporator)

    def has_sequence(self, stream):
        return self.has_next(self.begin_sequence, stream)

    def parse_sequence(self, stream):
        return self.parse_iterable(
            stream,
            self.begin_sequence,
            self.end_sequence
        )

    def has_set(self, stream):
        return self.has_next(self.begin_set, stream)

    def parse_set(self, stream):
        return set(self.parse_iterable(stream, self.begin_set, self.end_set))

    def has_units(self, stream):
        return self.has_next(self.begin_units, stream)

    def parse_units(self, stream):
        """
        UnitsExpression ::=
            UnitsStart WhiteSpace* UnitsValue WhiteSpace* UnitsEnd
        """
        value = b''
        self.expect(stream, self.begin_units)

        while not self.has_next(self.end_units, stream):
            if self.has_eof(stream):
                self.raise_unexpected_eof(stream)
            value += stream.read(1)

        self.expect(stream, self.end_units)
        return value.strip(b''.join(self.whitespace)).decode('utf-8')

    def parse_simple_value(self, stream):
        """
        SimpleValue ::= Integer
                      | FloatingPoint
                      | Exponential
                      | BinaryNum
                      | OctalNum
                      | HexadecimalNum
                      | DateTimeValue
                      | QuotedString
                      | UnquotedString
        """
        if self.has_quoted_string(stream):
            return self.parse_quoted_string(stream)

        if self.has_binary_number(stream):
            return self.parse_binary_number(stream)

        if self.has_octal_number(stream):
            return self.parse_octal_number(stream)

        if self.has_decimal_number(stream):
            return self.parse_decimal_number(stream)

        if self.has_hex_number(stream):
            return self.parse_hex_number(stream)

        if self.has_unquoated_string(stream):
            return self.parse_unquoated_string(stream)

        self.raise_unexpected(stream)

    def has_radix(self, radix, stream):
        prefix = b(str(radix)) + self.radix_symbole
        if self.has_next(prefix, stream):
            return True

        for sign in self.signs:
            if self.has_next(sign + prefix, stream):
                return True

        return False

    def parse_sign(self, stream):
        if self.has_next(self.plus_sign, stream):
            self.expect(stream, self.plus_sign)
            return 1

        if self.has_next(self.minus_sign, stream):
            self.expect(stream, self.minus_sign)
            return -1

        return 1

    def parse_radix(self, radix, chars, stream):
        """
        BinaryNum ::= [+-]? '2' RadixSymbol [0-1]+ RadixSymbol
        OctalChar ::= [+-]? '8' RadixSymbol [0-7]+ RadixSymbol
        HexadecimalNum ::= [+-]? '16' RadixSymbol [0-9a-zA-Z]+ RadixSymbol
        """
        value = b''
        sign = self.parse_sign(stream)
        self.expect(stream, b(str(radix)) + self.radix_symbole)
        sign *= self.parse_sign(stream)

        while not self.has_next(self.radix_symbole, stream):
            next = stream.read(1)
            if not next:
                self.raise_unexpected_eof(stream)

            if next not in chars:
                self.raise_unexpected(stream, chars)

            value += next

        if not value:
            self.raise_unexpected(stream, self.radix_symbole)

        self.expect(stream, self.radix_symbole)
        return sign * int(value, radix)

    def has_binary_number(self, stream):
        return self.has_radix(2, stream)

    def parse_binary_number(self, stream):
        return self.parse_radix(2, self.binary_chars, stream)

    def has_octal_number(self, stream):
        return self.has_radix(8, stream)

    def parse_octal_number(self, stream):
        return self.parse_radix(8, self.octal_chars, stream)

    def has_decimal_number(self, stream):
        return self.has_radix(10, stream)

    def parse_decimal_number(self, stream):
        return self.parse_radix(10, self.decimal_chars, stream)

    def has_hex_number(self, stream):
        return self.has_radix(16, stream)

    def parse_hex_number(self, stream):
        return self.parse_radix(16, self.hex_chars, stream)

    def has_quoted_string(self, stream):
        for mark in self.quote_marks:
            if self.has_next(mark, stream):
                return True
        return False

    def parse_quoted_string(self, stream):
        for mark in self.quote_marks:
            if self.has_next(mark, stream):
                break

        self.expect(stream, mark)
        value = b''

        while not self.has_next(mark, stream):
            next = stream.read(1)
            if not next:
                self.raise_unexpected_eof(stream)
            value += next

        self.expect(stream, mark)
        return self.format_quoated_string(value)

    def format_quoated_string(self, value):
        value = self.line_continuation_re.sub(b'', value)
        value = b' '.join(value.split()).strip()

        for escape, char in self.formatting_chars.items():
            value = value.replace(escape, char)

        return value.decode('utf-8')

    def has_unquoated_string(self, stream):
        next = self.peek(stream, 1)
        if not next:
            return False

        if next in self.delimiter_chars:
            return False

        return not self.has_comment(stream)

    def parse_unquoated_string(self, stream):
        value = b''
        while 1:
            value += self.next_token(stream)

            if not value.endswith(self.continuation_symbole):
                break

            if self.peek(stream, 1) not in self.newline_chars:
                break

            self.skip_whitespace_or_comment(stream)

            if not self.has_unquoated_string(stream):
                break

            value = value[:-1]

        return self.cast_unquoated_string(value)

    def cast_unquoated_string(self, value):
        if self.is_null(value):
            return self.parse_null(value)

        if self.is_boolean(value):
            return self.parse_boolean(value)

        if self.is_integer(value):
            return self.parse_integer(value)

        if self.is_float(value):
            return self.parse_float(value)

        if self.is_exponent(value):
            return self.parse_exponent(value)

        if self.is_time(value):
            return self.parse_time(value)

        if self.is_date_month_day(value):
            return self.parse_date_month_day(value)

        if self.is_date_day_of_year(value):
            return self.parse_date_day_of_year(value)

        if self.is_datetime_month_day(value):
            return self.parse_datetime_month_day(value)

        if self.is_datetime_day_of_year(value):
            return self.parse_datetime_day_of_year(value)

        return value.decode('utf-8')

    def is_null(self, value):
        return value in self.null_tokens

    def parse_null(self, value):
        return None

    def is_boolean(self, value):
        return value in self.boolean_tokens

    def parse_boolean(self, value):
        return value in self.true_tokens

    def is_integer(self, value):
        return bool(self.integer_re.match(value))

    def parse_integer(self, value):
        return int(value, 10)

    def is_float(self, value):
        return bool(self.float_re.match(value))

    def parse_float(self, value):
        return float(value)

    def is_exponent(self, value):
        return bool(self.exponent_re.match(value))

    def parse_exponent(self, value):
        return float(value)

    def is_time(self, value):
        return bool(self.time_re.match(value))

    def parse_time(self, value):
        match = self.time_re.match(value)
        hour, minute, second, microsecond, timezone = match.groups()
        second = second or '0'
        microsecond = (microsecond or b'0').ljust(6, b'0')[:6]
        return datetime.time(
            hour=int(hour, 10),
            minute=int(minute, 10),
            second=int(second, 10),
            microsecond=int(microsecond, 10),
            tzinfo=self.parse_timezone(timezone),
        )

    def is_date_month_day(self, value):
        return bool(self.date_month_day_re.match(value))

    def parse_date_month_day(self, value):
        year, month, day = self.date_month_day_re.match(value).groups()
        return datetime.date(
            year=int(year, 10),
            month=int(month, 10),
            day=int(day, 10),
        )

    def is_date_day_of_year(self, value):
        return bool(self.date_day_of_year_re.match(value))

    def parse_date_day_of_year(self, value):
        year, days = self.date_day_of_year_re.match(value).groups()
        year = int(year)
        days = int(days) - 1
        return datetime.date(year, 1, 1) + datetime.timedelta(days=days)

    def is_datetime_month_day(self, value):
        return bool(self.datetime_month_day_re.match(value))

    def parse_datetime_month_day(self, value):
        date, time = value.split(b'T')
        return datetime.datetime.combine(
            self.parse_date_month_day(date),
            self.parse_time(time),
        )

    def is_datetime_day_of_year(self, value):
        return bool(self.datetime_day_of_year_re.match(value))

    def parse_datetime_day_of_year(self, value):
        date, time = value.split(b'T')
        return datetime.datetime.combine(
            self.parse_date_day_of_year(date),
            self.parse_time(time),
        )

    def parse_timezone(self, timezone):
        if not timezone:
            return None

        if timezone.upper() == b'Z':
            return pytz.utc

        offset = int(timezone, 10)
        if offset == 0:
            return pytz.utc

        return pytz.FixedOffset(60 * offset)
