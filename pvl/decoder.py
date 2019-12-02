# -*- coding: utf-8 -*-
'''Parameter Value Language decoder and parser.

   The definition of PVL used in this module is from the Consultive
   Committee for Space Data Systems, and their Parameter Value
   Language Specification (CCSD0006 and CCSD0008), CCSDS 6441.0-B-2,
   referred to as the Blue Book with a date of June 2000.

   Some of the documention in this module represents the structure
   diagrams from the Blue Book for parsing PVL in a Backus–Naur
   form.

   So Figure 1-1 from the Blue Book would be represented as :

    <Item-A> ::= ( [ <Item-B>+ | <Item-C> ] <Item-D> )*

   Finally, the Blue Book defines <WSC> as a possibly empty collection
   of white space characters or comments:

    <WSC> ::= ( <white-space-character> | <comment> )*

   However, to help remember that <WSC> could be empty, we will typically
   always show it as <WSC>*.

   Likewise the <Statement-Delimiter> is defined as:

    <Statement-Delimiter> ::= [WSC]* [ ';' | <EOF> ]

   However, since all elements are optional, we will typically
   show it as [<Statement-Delimiter>].


'''
from warnings import warn
from .stream import BufferedStream, ByteStream
from ._collections import PVLModule, PVLGroup, PVLObject, Units
from ._strings import FORMATTING_CHARS

import re
from datetime import datetime

from .lang import token as Token
from .lang import grammar as Grammar


class ParseError(ValueError):
    """Subclass of ValueError with the following additional properties:
    msg: The unformatted error message
    pos: The start index of where parsing failed
    lineno: The line corresponding to pos
    colno: The column corresponding to pos
    """

    def __init__(self, msg, pos, lineno, colno):
        if None not in (pos, colno):
            errmsg = f'{msg}: line {lineno} column {colno} (char {pos})'
        else:
            errmsg = f'{msg}: line {lineno}'
        super(ParseError, self).__init__(errmsg)
        self.msg = msg
        self.pos = pos
        self.lineno = lineno
        self.colno = colno


class DecodeError(ValueError):
    """Subclass of ValueError with the following additional properties:

       msg: The unformatted error message
       doc: The PVL document being parsed
       pos: The start index of doc where parsing failed
       lineno: The line corresponding to pos
       colno: The column corresponding to pos
    """

    def __init__(self, msg, doc, pos):
        lineno = doc.count('\n', 0, pos) + 1
        colno = pos - doc.rfind('\n', 0, pos)
        errmsg = f'{msg}: line {lineno} column {colno} (char {pos})'
        ValueError.__init__(self, errmsg)
        self.msg = msg
        self.doc = doc
        self.pos = pos
        self.lineno = lineno
        self.colno = colno

    def __reduce__(self):
        return self.__class__, (self.msg, self.doc, self.pos)


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


def char_set(chars: str) -> set:
    return set(c for c in chars)


class PVLDecoder(object):
    whitespace = char_set(' \r\n\t\v\f')
    newline_chars = char_set('\r\n')
    reserved_chars = char_set('&<>\'{},[]=!#()%";|')
    delimiter_chars = whitespace | reserved_chars
    eof_char = ('\0')

    whitespace_re = re.compile(r'[ \r\n\t\v\f]*')

    quote_marks = ('"', "'")
    null_tokens = ('Null', 'NULL')
    end_tokens = ('End', 'END')

    true_tokens = ('TRUE', 'True', 'true')
    false_tokens = ('FALSE', 'False', 'false')
    boolean_tokens = true_tokens + false_tokens

    begin_group_tokens = ('Group', 'GROUP', 'BEGIN_GROUP')
    end_group_tokens = ('End_Group', 'END_GROUP')

    begin_object_tokens = ('Object', 'OBJECT', 'BEGIN_OBJECT')
    end_object_tokens = ('End_Object', 'END_OBJECT')

    seporator = ','
    radix_symbole = '#'
    statement_delimiter = ';'
    continuation_symbole = '-'
    assignment_symbole = '='

    begin_comment = '/*'
    end_comment = '*/'
    line_comment = '#'

    line_comment_re = re.compile(fr'{line_comment}.*\n')
    multi_line_comment_re = re.compile(r'{}.*{}'.format(re.escape(begin_comment),
                                                        re.escape(end_comment)),
                                       re.DOTALL)

    begin_sequence = '('
    end_sequence = ')'

    begin_set = '{'
    end_set = '}'

    begin_units = '<'
    end_units = '>'

    plus_sign = '+'
    minus_sign = '-'
    signs = set([plus_sign, minus_sign])

    binary_chars = ('0', '1')
    octal_chars = char_set('01234567')
    decimal_chars = char_set('0123456789')
    hex_chars = char_set('0123456789ABCDEFabcdef')

    def __init__(self, grammar=Grammar(), module_class=PVLModule()):
        self.strict = True
        self.errors = []
        self.grammar = grammar

        if isinstance(module_class, PVLModule):
            self.modcls = module_class
        else:
            raise Exception

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

    def expect_in(self, s: str, idx: int, tokens: list, token_desc: str) -> int:
        for token in tokens:
            if s.startswith(token, idx):
                return idx + len(token)

        longest = len(max(tokens, key=len))
        raise DecodeError(f'Unexpected {token_desc} Token in ' +
                          '"{} ..."'.format(s[idx:(idx + longest + 3)]) +
                          f'(expected one of {tokens})',
                          s, idx)

    def raise_unexpected(self, stream, token=None):
        if token is None:
            token = self.peek(stream, 1)
        self.raise_error('Unexpected token %r' % token, stream)

    def raise_unexpected_eof(self, stream):
        self.raise_error('Unexpected EOF', stream)

    def broken_assignment(self, s: str, idx: int):
        if self.strict:
            raise DecodeError("Broken Parameter-Value. Using 'strict=False' "
                              "when calling 'pvl.load' may help you parse the "
                              "label, it could also inadvertently mask other "
                              "errors.", s, idx)
        else:
            lineno = s.count('\n', 0, idx) + 1
            self.errors.append(lineno)
            return EmptyValueAtLine(lineno)

    def has_eof(self, s: str, idx: int):
        '''Returns the int index at the end of the EOF sequence, or None.'''
        if idx == len(s):
            return idx

        if s.startswith(self.eof_char, idx):
            return idx + len(self.eof_char)
        else:
            return None

    def has_next(self, token, stream, offset=0):
        return self.peek(stream, len(token), offset) == token

    def has_delimiter(self, s: str, idx=0) -> bool:
        if self.has_eof(s, idx) is not None:
            return True

        if self.has_comment(s, idx):
            return True

        if s.startswith(tuple(self.delimiter_chars), idx):
            return True

        return False

    def has_token_in(self, tokens, stream):
        for token in tokens:
            if not self.has_token(token, stream):
                continue
            return token

    def has_token(self, token, stream):
        if not self.has_next(token, stream):
            return False
        return self.has_delimiter(stream, len(token))

    def next_token(self, s: str, idx: int) -> str:
        token = ''
        for c in s[idx:]:
            if self.has_delimiter(c, 0):
                break
            else:
                token += c
        if len(token) == 0:
            raise DecodeError('No parseable token found at' +
                              '"{} ..."'.format(s[idx:(idx + 7)]),
                              s, idx)
        else:
            return token

    def decode(self, tokens: list):
        # old:
        # module = PVLModule(self.parse_block(s, 0, self.has_end))
        # module.errors = sorted(self.errors)
        # self.skip_end(s)
        # return module

        module = self.parse_module(tokens)
        # module.errors = sorted(self.errors) need?
        # self.skip_end(s) need?
        return module

    def parse_module(self, tokens):
        """Parses the tokens for a PVL Module.

            <PVL-Module-Contents> ::=
             ( <Assignment-Statement> | <WSC>* | <Aggregation-Block> )*
             [<End-Statement>]
        """
        m = self.modcls()
        for t in tokens:
            if t.is_WSC():
                # If there's a comment, could parse here.
                pass
            elif t.is_begin_aggregation():
                m.add(parse_aggregation_block(t, tokens))
            elif t.is_parameter_name():
                m.add(parse_assignment_statement(t, tokens))
            elif t.is_end_statement():
                after = next(tokens, token())
                if after.is_comment():
                    # Maybe do something with the last comment.
                    pass
                break
            else:
                tokens.throw(ValueError, f'Unexpected Token: {t}')
        return m

    def parse_block(self, s, idx, has_end):
        """
        PVLModuleContents ::= (Statement | WSC)* EndStatement?
        AggrObject ::= BeginObjectStmt AggrContents EndObjectStmt
        AggrGroup ::= BeginGroupStmt AggrContents EndGroupStmt
        AggrContents := WSC Statement (WSC | Statement)*
        """
        statements = []
        while 1:
            idx = self.skip_whitespace_or_comment(s, idx)

            if has_end(s, idx):
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

    def skip_whitespace_or_comment(self, s: str, idx: int) -> int:
        while self.has_whitespace(s, idx) or self.has_comment(s, idx):
            if self.has_whitespace(s, idx):
                idx = self.skip_whitespace(s, idx)

            if self.has_comment(s, idx):
                idx = self.skip_comment(s, idx)

        return idx

    def skip_statement_delimiter(self, s: str, idx: int) -> int:
        """Ensure that a Statement Delimiter consists of one semicolon,
        optionally preceded by multiple White Spaces and/or Comments, OR one or
        more Comments and/or White Space sequences.

        StatementDelim ::= WSC (SemiColon | WhiteSpace | Comment)
                         | EndProvidedOctetSeq

        """
        idx = self.skip_whitespace_or_comment(s, idx)
        if s.startswith(self.statement_delimiter, idx):
            return idx + len(self.statement_delimiter)
        else:
            return idx

    def parse_statement(self, s: str, idx: int):
        """
        Statement ::= AggrGroup
                    | AggrObject
                    | AssignmentStmt
        """

        if self.has_group(s, idx):
            return self.parse_aggregation(s, idx,
                                          self.begin_group_tokens,
                                          self.end_group_tokens,
                                          self.has_end_group,
                                          PVLGroup)

        if self.has_object(stream):
            return self.parse_aggregation(s, idx,
                                          self.begin_object_tokens,
                                          self.end_object_tokens,
                                          self.has_end_object,
                                          PVLObject)

        if not self.has_delimiter(s, idx):
            return self.parse_assignment(stream)

        if self.has_assignment_symbol(stream):
            return self.broken_assignment(stream.lineno - 1)

        self.raise_unexpected(stream)

    def has_assignment_symbol(self, stream):
        self.skip_whitespace(stream)
        self.expect(stream, self.assignment_symbole)
        return True

    def has_whitespace(self, s: str, idx: int) -> bool:
        return s.startswith(tuple(self.whitespace), idx)

    def skip_whitespace(self, s: str, idx: int) -> int:
        return self.whitespace_re.match(s, idx).end()

    def has_multiline_comment(self, s: str, idx: int) -> int:
        return s.startswith(self.begin_comment, idx)

    def has_line_comment(self, s: str, idx: int) -> bool:
        return s.startswith(self.line_comment, idx)

    def has_comment(self, s: str, idx: int) -> bool:
        return (
            self.has_line_comment(s, idx) or
            self.has_multiline_comment(s, idx)
        )

    def skip_comment(self, s: str, idx: int) -> int:
        if self.has_line_comment(s, idx):
            return self.line_comment_re.match(s, idx).end()
        else:
            return self.multi_line_comment_re.match(s, idx).end()

    def has_end(self, s: str, idx: int):
        """
        EndStatement ::=
            EndKeyword (SemiColon | WhiteSpace | Comment | EndProvidedOctetSeq)
        """
        if self.has_eof(s, idx) is not None:
            return True

        for token in self.end_tokens:
            if s.startswith(token, idx):

                offset = idx + len(token)

                if self.has_eof(s, offset) is not None:
                    return True

                if self.has_whitespace(s, offset):
                    return True

                if self.has_comment(s, offset):
                    return True

                if s.startswith(self.statement_delimiter, offset):
                    return True

        return False

    def skip_end(self, stream):
        if self.has_eof(stream):
            return

        self.expect_in(stream, self.end_tokens)
        self.skip_whitespace_or_comment(stream)
        self.optional(stream, self.statement_delimiter)

    def has_group(self, s: str, idx: int) -> bool:
        return s.startswith(self.begin_group_tokens, idx)

    def parse_end_assignment(self, s: str, idx: int, name: str) -> int:
        idx = self.skip_whitespace_or_comment(s, idx)

        if not s.startswith(self.assignment_symbole, idx):
            return idx

        idx = self.ensure_assignment(s, idx)

        if s.startswith(name, idx):
            return idx + len(name)
        else:
            raise DecodeError(f'Expected to find {name} after the equals sign '
                              'at "... {} ..."'.format(s[idx - 5:idx + 5]),
                              s, idx)

    def parse_group(self, s: str, idx: int):
        """Block Name must match Block Name in paired End Group Statement if
        Block Name is present in End Group Statement.

        BeginGroupStmt ::=
            BeginGroupKeywd WSC AssignmentSymbol WSC BlockName StatementDelim
        """
        idx = self.expect_in(s, idx, self.begin_group_tokens, 'Begin Group')

        idx = self.skip_whitespace_or_comment(s, idx)
        name = self.next_token(s, idx)
        idx += len(name)

        idx = self.ensure_assignment(s, idx)

        idx = self.skip_statement_delimiter(s, idx)
        statements = self.parse_block(s, idx, self.has_end_group)

        idx = self.expect_in(s, idx, self.end_group_tokens, 'End Group')

        idx = self.parse_end_assignment(s, idx, name)
        idx = self.skip_statement_delimiter(s, idx)

        return name, PVLGroup(statements), idx

    def parse_aggregation_block(self, begin_agg_stmt: Token,
                                tokens: list) -> tuple:
        """Parses the tokens for an Aggregation Block.

            <Aggregation-Block> ::= <Begin-Aggegation-Statement>
                (<WSC>* (Assignment-Statement | Aggregation-Block) <WSC>*)+
                <End-Aggregation-Statement>

           The Begin-Aggregation-Statement Name must match the Block-Name in the
           paired End-Aggregation-Statement if a Block-Name is present in the
           End-Aggregation-Statement.

        """
        m = self.modcls()

        block_name, next_t = parse_begin_aggregation_statement(begin_agg_stmt,
                                                               tokens)

        for t in itertools.chain(next_t, tokens):
            if t.is_WSC():
                # If there's a comment, could parse here.
                pass
            elif t.is_begin_aggregation():
                m.add(parse_begin_aggregation_block(t, tokens))
            elif t.is_parameter_name():
                m.add(parse_assignment_statement(t, tokens))
            elif t.is_WSC():
                # If there's a comment, could parse here.
                pass
            elif t.is_end_aggregation_statement():
                after = next(tokens, token())
                if after.is_comment():
                    # Maybe do something with the last comment.
                    pass
                break
            else:
                tokens.throw(ValueError, f'Unexpected Token: {t}')
        return m

    def _parse_around_equals(self, tokens: list) -> Token:
        """Parses white space and comments on either side
           of an equals sign.

           This is shared functionality for Begin Aggregation Statements
           and Assignment Statements.  It basically covers parsing
           anything that has a syntax diagram like this:

             <WSC>* '=' <WSC>*

           It returns the next token (o) to be parsed.
        """
        for t in tokens:
            if t.is_WSC():
                # If there's a comment, could parse here and below.
                pass
            else:
                break

        if t != '=':
            tokens.throw(ValueError, f'Expecting "=", got: {t}')

        for t in tokens:
            if not t.is_WSC():
                break

        return t

    def parse_begin_aggregation_statement(self, begin_agg_stmt: Token,
                                          tokens: list) -> tuple:
        """Parses the tokens for a Begin Aggregation Statement.

           <Begin-Aggregation-Statement-block> ::=
                <Begin-Aggegation-Statement> <WSC>* '=' <WSC>*
                <Block-Name> [<Statement-Delimiter>]

           Where <Block-Name> ::= <Parameter-Name>

        """
        if not begin_agg_stmt.is_begin_aggregation():
            raise ValueError('Expecting a Begin-Aggegation-Statement, but'
                             f'found: {begin_agg_stmt}')

        t = self._parse_around_equals(tokens)

        if t.is_parameter_name():
            block_name = t
        else:
            tokens.throw(ValueError,
                         f'Expecting a Block-Name after "{begin_agg_stmt} =" '
                         f'but found: "{t}"')

        t = self.parse_statement_delimiter(tokens)

        return(block_name, t)

    def parse_assignment_statement(self, parameter_name: Token,
                                   tokens: list) -> tuple:
        """Parses the tokens for an Assignment Statement.

            <Assignment-Statement> ::= <Parameter-Name> <WSC>* '=' <WSC>*
                                        <Value> [<Statement-Delimiter>]

        """
        if not parameter_name.parameter_name():
            raise ValueError('Expecting a Parameter Name, but'
                             f'found: {parameter_name}')

        Value = ''
        t = self._parse_around_equals(tokens)

        if t.is_value():
            Value = self.parse_value(t, tokens)
        else:
            tokens.throw(ValueError,
                         f'Expecting a Block-Name after "{begin_agg_stmt} =" '
                         f'but found: "{t}"')

        t = self.parse_statement_delimiter(tokens)

        return(block_name, t)

    def parse_statement_delimiter(self, tokens: list) -> Token:
        """Parses the tokens for a Statement Delimiter.

           Returns the next token *after* the Statement Delimiter.

            <Statement-Delimiter> ::= <WSC>*
                        (<white-space-character> | <comment> | ';' | <EOF>)

           Although the above structure comes from Figure 2-4
           of the Blue Book, the <white-space-character> and <comment>
           elements are redundant with the presence of [WSC]*
           so it can be simplified to:

            <Statement-Delimiter> ::= <WSC>* [ ';' | <EOF> ]

           Typically written [<Statement-Delimiter>].
        """
        for t in tokens:
            if t.is_WSC():
                # If there's a comment, could parse here.
                    pass
            elif t.is_delimiter():
                return next(tokens)
            else:
                return t
        # The token, t, is now the next thing past this Statement-Delimiter
        # so we need to return it.

    def has_end_group(self, s: str, idx: int) -> bool:
        """
        EndGroupLabel :=  AssignmentSymbol WSC BlockName
        EndGroupStmt := EndGroupKeywd WSC EndGroupLabel? StatementDelim
        """
        return s.startswith(self.end_group_tokens, idx)

    def has_object(self, s: str, idx: int) -> bool:
        return s.startswith(self.begin_group_tokens, idx)

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

    def has_end_object(self, s: str, idx: int) -> bool:
        """
        EndObjectLabel ::= AssignmentSymbol WSC BlockName
        EndObjectStmt ::= EndObjectKeywd WSC EndObjectLabel? StatementDelim
        """
        return s.startswith(self.end_object_tokens, idx)

    def has_assignment(self, stream):
        return not self.has_delimiter(stream)

    def ensure_assignment(self, s: str, idx: int) -> int:
        idx = self.skip_whitespace_or_comment(s, idx)

        if s.startswith(self.assignment_symbole, idx):
            idx += len(self.assignment_symbole)
        else:
            end_i = idx + len(self.assignment_symbole) + 3
            raise DecodeError(f'Expected {self.assignment_symbole}, but found '
                              '"{}"'.format(s[idx:end_i]), s, idx)

        return self.skip_whitespace_or_comment(s, idx)

    def parse_assignment(self, s: str, idx: int):
        """
        AssignmentStmt ::= Name WSC AssignmentSymbol WSC Value StatementDelim
        """
        name = self.next_token(s, idx)
        idx += len(name)

        idx = self.ensure_assignment(s, idx)
        if any((self.has_end_group(s, idx),
                self.has_end_object(s, idx),
                self.has_end(s, idx),
                s.startswith(self.statement_delimiter, idx))):
            value = self.broken_assignment(s, idx)
            # I think I need to update idx here, but not sure.
            idx = self.skip_whitespace_or_comment(s, idx)
        else:
            value, idx = self.parse_value(s, idx)
        self.skip_statement_delimiter(stream)

        return name, value, idx

    def parse_value(self, t: Token, tokens: list) -> tuple:
        """Parses PVL Values.

            <Value> ::= (<Simple-Value> | <Set> | <Sequence>)
                        [<WSC>* <Units Expression>]

        """
        value = None
        if t.is_simple_value:
            value = self.decode_simple_value(t)
        elif t.startswith(self.grammar.set_delimiter[0]):
            value = self.parse_set(t, tokens)
        elif t.startswith(self.grammar.sequence_delimiter[0]):
            value = self.parse_sequence(t, tokens)
        else:
            tokens.throw(ValueError,
                         'Was expecting a Simple Value, or the beginning of '
                         f'a Set or Sequence, but found: "{t}"')

        units = None
        for t in tokens:
            if t.is_WSC():
                # If there's a comment, could parse
                pass
            elif t.starswith(self.grammar.units_delimiter):
                units, t = self.parse_units(t, tokens)
                break
            else:
                break

        if units is not None:
            value = Units(value, units)

        return value, t

    def parse_iterable(self, s: str, idx: int, start: str, end: str):
        """
        Sequence ::= SequenceStart WSC SequenceValue? WSC SequenceEnd
        Set := SetStart WSC SequenceValue? WSC SetEnd
        SequenceValue ::= Value (WSC SeparatorSymbol WSC Value)*
        """
        values = []

        if not s.startswith(start, idx):
            raise DecodeError(f'Expected {start} Token in ' +
                              '"{} ..."'.format(s[idx:(idx + 3)]),
                              s, idx)

        idx += len(start)

        while True:
            idx = self.skip_whitespace_or_comment(s, idx)
            (v, i) = self.parse_value(s, idx)
            values.append(v)
            idx = i
            idx = self.skip_whitespace_or_comment(s, idx)

            if s.startswith(end, idx):
                idx += len(end)
                break
            elif s.startswith(self.seporator, idx):
                idx += len(self.seporator)
                continue
            else:
                print(values)
                raise DecodeError('While parsing a set or sequence, expected ' +
                                  f'"{self.seporator}" or "{end}" '
                                  'but found "{}".'.format(s[idx:idx + 5]),
                                  s, idx)

        return values, idx

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

    def decode_simple_value(self, value: Token):
        '''Takes a Simple Value and attempts to convert it to the appropriate
           Python type.

            <Simple-Value> ::= (<Date-Time> | <Numeric> | <String>)
        '''
        # Quoted String
        if value.is_quoted_string():
            return str(value[1:-1])

        # Non-Decimal (Binary, Hex, and Octal)
        for nd_re in (self.grammar.binary_re,
                      self.grammar.octal_re,
                      self.grammar.hex_re):
            match = nd_re.fullmatch(value)
            if match is not None:
                d = match.groupdict('')
                return int(d['sign'] + d['non_decimal'], base=d['radix'])

        # Decimal Numbers (int and float)
        try:
            return int(value, base=10)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                pass

        try:
            return decode_datetime(value)
        except ValueError:
            return str(value)

    def parse_simple_value(self, s: str, idx: int) -> tuple:
        """
        SimpleValue ::= Integer
                      | FloatingPoint
                      | Exponential
                      | BinaryNum
                      | OctalNum
                      | HexadecimalNum
                      | DateTimeValue
                      | QuotedStrin UnquotedString
        """
        if s.startswith(self.quote_marks, idx):
            return self.parse_quoted_string(s, idx)

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
        prefix = str(radix).encode() + self.radix_symbole
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
        self.expect(stream, str(radix).encode() + self.radix_symbole)
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

    def unescape_next_char(self, s: str, idx: int) -> tuple:
        c = s[idx]
        if c in self.quote_marks:
            return c, idx + 1

        try:
            return FORMATTING_CHARS[c], idx + 1
        except KeyError:
            raise DecodeError(f'Invalid \\escape: {c}', s, idx)

    def parse_quoted_string(self, s: str, idx: int):
        for mark in self.quote_marks:
            if s.startswith(mark, idx):
                idx += len(mark)
                break
        else:
            longest = len(max(self.quote_marks, key=len))
            raise DecodeError(f'Was expecting one of {self.quote_marks} '
                              ' but found '
                              '"{} ..."'.format(s[idx:(idx + longest + 3)]),
                              s, idx)

        value = ''

        while not s.startswith(mark, idx):
            c = s[idx]
            idx += 1

            if c == '\\':
                (c, idx) = self.unescape_next_char(s, idx)

            # I don't think you're supposed to collapse whitespace,
            # so I'm commenting this out.
            # elif next in self.whitespace:
            #     self.skip_whitespace(stream)
            #     if self.has_next(mark, stream):
            #         break
            #     next = b' '

            # This ignores '-' line continuations, but I don't think
            # this is part of the PVL spec, maybe a PDS or ISIS thing?
            # leaving it for now, until I can look it up.
            elif c == '-' and s.startswith(tuple(self.newline_chars), idx):
                idx = self.skip_whitespace(s, idx)
                continue

            value += c
        else:
            idx += len(mark)

        return value, idx

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
        try:
            return int(value, 10)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                raise ValueError('Could not parse an int or a '
                                 f'float from {value}')

    def _get_datetime(self, value, formats):
        dt = None
        for f in formats:
            try:
                dt = datetime.strptime(value, f)
            except ValueError:
                pass

        raise ValueError

    def decode_datetime(self, value: str):
        '''Takes a string and attempts to convert it to the appropriate
           Python datetime time, date, or datetime type based on the
           PVL standard.
        '''
        try:
            return _get_datetime(value, self.grammar.date_formats).date()
        except ValueError:
            try:
                return _get_datetime(value, self.grammar.time_formats).time()
            except ValueError:
                try:
                    return _get_datetime(value, self.grammar.datetime_formats)
                except ValueError:
                    pass

        return self.decode_dateutil(value)

    def decode_dateutil(self, value: str):
        '''Takes a string and attempts to convert it to the appropriate
           Python datetime by using the 3rd party dateutil library (if
           present) to parse ISO 8601 datetime strings, which have more
           variety than those allowed by the PVL specification.
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
