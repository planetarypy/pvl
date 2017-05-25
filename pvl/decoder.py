# -*- coding: utf-8 -*-
from six import b

from .stream import BufferedStream, ByteStream
from ._collections import PVLModule, PVLGroup, PVLObject, Units
from ._datetimes import parse_datetime
from ._numbers import parse_number
from ._strings import FORMATTING_CHARS


class ParseError(ValueError):
    """Subclass of ValueError with the following additional properties:
    msg: The unformatted error message
    pos: The start index of where parsing failed
    lineno: The line corresponding to pos
    colno: The column corresponding to pos
    """
    def __init__(self, msg, pos, lineno, colno):
        if None not in (pos, colno):
            errmsg = '%s: line %d column %d (char %d)' % (
                msg, lineno, colno, pos)
        else:
            errmsg = '%s: line %d' % (msg, lineno)
        super(ParseError, self).__init__(errmsg)
        self.msg = msg
        self.pos = pos
        self.lineno = lineno
        self.colno = colno


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
        message = '%s(%d does not have a value.'
        message = message % (type(self).__name__, self.lineno)
        message += ' Treat as an empty string)'
        return message


def char_set(chars):
    return set([b(c) for c in chars])


class PVLDecoder(object):
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

    def __init__(self):
        self.strict = True
        self.errors = []

    def set_strict(self, strict):
        self.strict = strict

    def peek(self, stream, n, offset=0):
        return stream.peek(n + offset)[offset:offset + n]

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

    def broken_assignment(self, lineno):
        if self.strict:
            msg = (
                "Broken Parameter-Value. Using 'strict=False' when calling" +
                " 'pvl.load' may help you parse the label, it could also" +
                " inadvertently mask other errors"
            )
            raise ParseError(msg, None, lineno, None)
        else:
            self.errors.append(lineno)
            return EmptyValueAtLine(lineno)

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

    def decode(self, stream):
        if isinstance(stream, bytes):
            stream = ByteStream(stream)
        else:
            stream = BufferedStream(stream)

        module = PVLModule(self.parse_block(stream, self.has_end))
        module.errors = sorted(self.errors)
        self.skip_end(stream)
        return module

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

            statement = self.parse_statement(stream)
            if isinstance(statement, EmptyValueAtLine):
                if len(statements) == 0:
                    self.raise_unexpected(stream)
                self.skip_whitespace_or_comment(stream)
                value = self.parse_value(stream)
                last_statement = statements.pop(-1)
                fixed_last = (
                    last_statement[0],
                    statement
                )
                statements.append(fixed_last)
                statements.append((last_statement[1], value))

            else:
                statements.append(statement)

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

        if self.has_assignment_symbol(stream):
            return self.broken_assignment(stream.lineno - 1)

        self.raise_unexpected(stream)

    def has_assignment_symbol(self, stream):
        self.skip_whitespace(stream)
        self.expect(stream, self.assignment_symbole)
        return True

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

        return name.decode('utf-8'), PVLGroup(statements)

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

        return name.decode('utf-8'), PVLObject(statements)

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
        lineno = stream.lineno
        name = self.next_token(stream)
        self.ensure_assignment(stream)
        at_an_end = any((
            self.has_end_group(stream),
            self.has_end_object(stream),
            self.has_end(stream),
            self.has_next(self.statement_delimiter, stream, 0)))
        if at_an_end:
            value = self.broken_assignment(lineno)
            self.skip_whitespace_or_comment(stream)
        else:
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

        if self.has_end(stream):
            return self.broken_assignment(stream.lineno)

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
                self.raise_unexpected(stream, next)

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

    def unescape_next_char(self, stream):
        esc = stream.read(1)

        if esc in self.quote_marks:
            return esc

        try:
            return FORMATTING_CHARS[esc]
        except KeyError:
            msg = "Invalid \\escape: " + repr(esc)
            self.raise_error(msg, stream)

    def parse_quoted_string(self, stream):
        for mark in self.quote_marks:
            if self.has_next(mark, stream):
                break

        self.expect(stream, mark)
        self.skip_whitespace(stream)

        value = b''

        while not self.has_next(mark, stream):
            next = stream.read(1)
            if not next:
                self.raise_unexpected_eof(stream)

            if next == b'\\':
                next = self.unescape_next_char(stream)

            elif next in self.whitespace:
                self.skip_whitespace(stream)
                if self.has_next(mark, stream):
                    break
                next = b' '

            elif next == b'-' and self.has_token_in(self.newline_chars, stream):
                self.skip_whitespace(stream)
                continue

            value += next

        self.expect(stream, mark)
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

        try:
            return self.parse_number(value)
        except ValueError:
            pass

        try:
            return self.parse_datetime(value)
        except ValueError:
            pass

        return value.decode('utf-8')

    def is_null(self, value):
        return value in self.null_tokens

    def parse_null(self, value):
        return None

    def is_boolean(self, value):
        return value in self.boolean_tokens

    def parse_boolean(self, value):
        return value in self.true_tokens

    def parse_number(self, value):
        return parse_number(value)

    def parse_datetime(self, value):
        return parse_datetime(value)
