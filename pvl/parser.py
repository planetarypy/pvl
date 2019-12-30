# -*- coding: utf-8 -*-
'''Parameter Value Language parser.

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

    <Statement-Delimiter> ::= <WSC>* [ ';' | <EOF> ]

   However, since all elements are optional, we will typically
   show it as [<Statement-Delimiter>].

   The parser deals with managing the tokens that come out of the lexer.
   Once the parser gets to a state where it has something that needs to
   be converted to a Python object and returned, it uses the decoder to
   make that conversion.
'''
import collections.abc as abc
import re

from datetime import datetime
from itertools import cycle
from warnings import warn

from ._collections import PVLModule, PVLGroup, PVLObject, Units
from .token import token as Token
from .grammar import grammar as Grammar
from .grammar import Omnigrammar
from .decoder import PVLDecoder, OmniDecoder
from .lexer import lexer as Lexer
from .lexer import LexerError


_tokens_docstring = """*tokens* is expected to be a *generator iterator*
                       which provides ``pvl.token`` objects.  It should
                       allow for a generated object to be 'returned' via
                       the generator's send() function.  When parsing the
                       first object from *tokens*, if an unexpected object
                       is encountered, it will 'return' the object to
                       *tokens*, and raise a ``ValueError``, so that
                       ``try``-``except`` bloks can be used, and the
                       *generator iterator* is left in a good state. However,
                       if a parsing anomaly is discovered deeper in
                       parsing a PVL sequence, then a ``ValueError`` will
                       be thrown into the *tokens* generator
                       iterator (via .throw()).
                    """


class ParseError(Exception):
    '''A simple parser exception.
    '''
    pass


class PVLParser(object):

    def __init__(self, grammar=None, decoder=None, lexer=None,
                 module_class=PVLModule, group_class=PVLGroup,
                 object_class=PVLObject, strict=False):

        if lexer is None:
            self.lexer = Lexer
        else:
            self.lexer = lexer

        if grammar is None:
            self.grammar = Omnigrammar()
        elif isinstance(grammar, Grammar):
            self.grammar = grammar
        else:
            raise TypeError('The grammar must be an instance of pvl.grammar.')

        if decoder is None:
            self.decoder = OmniDecoder(grammar=self.grammar, strict=strict)
        elif isinstance(decoder, PVLDecoder):
            self.decoder = decoder
        else:
            raise TypeError('The decode must be an instance of pvl.PVLDecoder.')

        if issubclass(module_class, PVLModule):
            self.modcls = module_class
        else:
            raise TypeError('The module_class must be a subclass of PVLModule.')

        if issubclass(group_class, PVLGroup):
            self.grpcls = group_class
        else:
            raise TypeError('The group_class must be a subclass of PVLGroup.')

        if issubclass(object_class, PVLObject):
            self.objcls = object_class
        else:
            raise TypeError('The object_class must be a subclass of PVLObject.')

    def parse(self, s: str):
        '''Converts the string to a PVLModule.
        '''
        tokens = self.lexer(s, g=self.grammar, d=self.decoder)
        return self.parse_module(tokens)

    def aggregation_cls(self, begin: str):
        begin_fold = begin.casefold()
        for gk in self.grammar.group_keywords.keys():
            if begin_fold == gk.casefold():
                return self.grpcls()

        for ok in self.grammar.object_keywords.keys():
            if begin_fold == ok.casefold():
                return self.objcls()

        raise ValueError(f'The value "{begin}" did not match a Begin '
                         'Aggregation Statement.')

    def parse_module(self, tokens: abc.Generator):
        """Parses the tokens for a PVL Module.

           {}

            <PVL-Module-Contents> ::=
             ( <Assignment-Statement> | <WSC>* | <Aggregation-Block> )*
             [<End-Statement>]

        """.format(_tokens_docstring)
        m = self.modcls()

        parsing = True
        while parsing:
            parsing = False
            for p in (self.parse_aggregation_block,
                      self.parse_assignment_statement,
                      self.parse_end_statement):
                try:
                    self.parse_WSC_until(None, tokens)
                    parsed = p(tokens)
                    # print(parsed)
                    if parsed is None:  # because parse_end_statement returned
                        return m
                    else:
                        m.append(*parsed)
                        parsing = True
                except LexerError:
                    raise
                except ValueError:
                    pass

        t = next(tokens)
        tokens.throw(ValueError,
                     'Expecting an Aggregation Block, an Assignment '
                     'Statement, or an End Statement, but found '
                     f'"{t}" ')

    def parse_aggregation_block(self, tokens: abc.Generator):
        """Parses the tokens for an Aggregation Block, and returns
           the modcls object that is the result of the parsing and
           decoding.

           {}

            <Aggregation-Block> ::= <Begin-Aggegation-Statement>
                (<WSC>* (Assignment-Statement | Aggregation-Block) <WSC>*)+
                <End-Aggregation-Statement>

           The Begin-Aggregation-Statement Name must match the Block-Name
           in the paired End-Aggregation-Statement if a Block-Name is
           present in the End-Aggregation-Statement.
        """.format(_tokens_docstring)

        (begin, block_name) = self.parse_begin_aggregation_statement(tokens)

        agg = self.aggregation_cls(begin)

        while True:
            self.parse_WSC_until(None, tokens)
            try:
                agg.append(*self.parse_aggregation_block(tokens))
            except ValueError:
                try:
                    agg.append(*self.parse_assignment_statement(tokens))
                except ValueError:
                    self.parse_end_aggregation(begin, block_name, tokens)
                    break

        return (block_name, agg)

    def _parse_around_equals(self, tokens: abc.Generator) -> None:
        """Parses white space and comments on either side
           of an equals sign.

           *tokens* is expected to be a *generator iterator* which
           provides ``pvl.token`` objects.

           This is shared functionality for Begin Aggregation Statements
           and Assignment Statements.  It basically covers parsing
           anything that has a syntax diagram like this:

             <WSC>* '=' <WSC>*

        """

        if not self.parse_WSC_until('=', tokens):
            try:
                t = next(tokens)
                tokens.send(t)
                raise ValueError(f'Expecting "=", got: {t}')
            except StopIteration:
                raise ParseError(f'Expecting "=", but ran out of tokens.')

        self.parse_WSC_until(None, tokens)
        return

    def parse_begin_aggregation_statement(self, tokens: abc.Generator) -> tuple:
        """Parses the tokens for a Begin Aggregation Statement, and returns
           the name Block Name as a ``str``.

           {}

           <Begin-Aggregation-Statement-block> ::=
                <Begin-Aggegation-Statement> <WSC>* '=' <WSC>*
                <Block-Name> [<Statement-Delimiter>]

           Where <Block-Name> ::= <Parameter-Name>

        """.format(_tokens_docstring)
        try:
            begin = next(tokens)
            if not begin.is_begin_aggregation():
                tokens.send(begin)
                raise ValueError('Expecting a Begin-Aggegation-Statement, but '
                                 f'found: {begin}')
        except StopIteration:
            raise ValueError('Ran out of tokens before starting to parse '
                             'a Begin-Aggegation-Statement.')

        try:
            self._parse_around_equals(tokens)
        except ValueError:
            tokens.throw(ValueError,
                         f'Expecting an equals sign after "{begin}" ')

        block_name = next(tokens)
        if not block_name.is_parameter_name():
            tokens.throw(ValueError,
                         f'Expecting a Block-Name after "{begin} =" '
                         f'but found: "{block_name}"')

        self.parse_statement_delimiter(tokens)

        return(begin, str(block_name))

    def parse_end_aggregation(self, begin_agg: str, block_name: str,
                              tokens: abc.Generator) -> None:
        """Parses the tokens for an End Aggregation Statement.

           {}

           <End-Aggregation-Statement-block> ::=
                <End-Aggegation-Statement> [<WSC>* '=' <WSC>*
                <Block-Name>] [<Statement-Delimiter>]

           Where <Block-Name> ::= <Parameter-Name>

        """.format(_tokens_docstring)
        end_agg = next(tokens)

        # Need to do a little song and dance to case-independently
        # match the keys:
        for k in self.grammar.aggregation_keywords.keys():
            if k.casefold() == begin_agg.casefold():
                truecase_begin = k
                break
        if(end_agg.casefold() !=
           self.grammar.aggregation_keywords[truecase_begin].casefold()):
            tokens.send(end_agg)
            raise ValueError('Expecting an End-Aggegation-Statement that '
                             'matched the Begin-Aggregation_Statement, '
                             f'"{begin_agg}" but found: {end_agg}')

        try:
            self._parse_around_equals(tokens)
        except (ParseError, ValueError):  # No equals statement, which is fine.
            self.parse_statement_delimiter(tokens)
            return None

        t = next(tokens)
        if t != block_name:
            tokens.send(t)
            tokens.throw(ValueError,
                         f'Expecting a Block-Name after "{end_agg} =" '
                         f'that matches "{block_name}", but found: '
                         f'"{t}"')

        self.parse_statement_delimiter(tokens)

        return None

    def parse_end_statement(self, tokens: abc.Generator) -> None:
        """Parses the tokens for an End Statement.

           {}

           <End-Statement> ::= "END" ( <WSC>* | [<Statement-Delimiter>] )

        """.format(_tokens_docstring)

        try:
            end = next(tokens)
            if not end.is_end_statement():
                tokens.send(end)
                raise ValueError('Expecting an End Statement, like '
                                 f'"{self.grammar.end_statements}" but found '
                                 f'"{end}"')

            try:
                t = next(tokens)
                if t.is_WSC():
                    # maybe process comment
                    return
                else:
                    tokens.send(t)
                    return
            except LexerError:
                pass
        except StopIteration:
            pass

        return

    def parse_assignment_statement(self, tokens: abc.Generator) -> tuple:
        """Parses the tokens for an Assignment Statement.

           The returned two-tuple contains the Parameter Name in the
           first element, and the Value in the second.

           {}

            <Assignment-Statement> ::= <Parameter-Name> <WSC>* '=' <WSC>*
                                        <Value> [<Statement-Delimiter>]

        """.format(_tokens_docstring)
        parameter_name = None
        try:
            t = next(tokens)
            if t.is_parameter_name():
                parameter_name = str(t)
            else:
                tokens.send(t)
                raise ValueError('Expecting a Parameter Name, but '
                                 f'found: "{t}"')
        except StopIteration:
            raise ParseError('Ran out of tokens before starting to parse '
                             'an Assignment-Statement.')

        Value = None
        self._parse_around_equals(tokens)

        try:
            Value = self.parse_value(tokens)
        except StopIteration:
            raise ParseError('Ran out of tokens to parse after the equals '
                             'sign in an Assignment-Statement: '
                             f'"{parameter_name} =".')

        self.parse_statement_delimiter(tokens)

        return(parameter_name, Value)

    def parse_WSC_until(self, token: str, tokens: abc.Generator) -> bool:
        """Consumes objects from *tokens*, if the object's *.is_WSC()*
           function returns *True*, it will continue until *token* is
           encountered and will return *True*.  If it encounters an object
           that does not meet these conditions, it will 'return' that
           object to *tokens* and will return *False*.

           *tokens* is expected to be a *generator iterator* which
           provides ``pvl.token`` objects.
        """
        for t in tokens:
            if t == token:
                return True
            elif t.is_WSC():
                # If there's a comment, could parse here.
                    pass
            else:
                tokens.send(t)
                return False

    def _parse_set_seq(self, delimiters, tokens: abc.Generator) -> list:
        '''The internal parsing of PVL Sets and Sequences are very
           similar, and this function provides that shared logic.

           *delimiters* are a two-tuple containing the start and end
           characters for the PVL Set or Sequence.

           {}
        '''.format(_tokens_docstring)
        t = next(tokens)
        if t != delimiters[0]:
            tokens.send(t)
            raise ValueError(f'Expecting a begin delimiter "{delimiters[0]} =" '
                             f'but found: "{t}"')
        set_seq = list()
        # Initial WSC and/or empty
        if self.parse_WSC_until(delimiters[1], tokens):
            return set_seq

        # First item:
        set_seq.append(self.parse_value(tokens))
        if self.parse_WSC_until(delimiters[1], tokens):
            return set_seq

        # Remaining items, if any
        for t in tokens:
            # print(f'in loop, t: {t}, set_seq: {set_seq}')
            if t == ',':
                self.parse_WSC_until(None, tokens)  # consume WSC after ','
                set_seq.append(self.parse_value(tokens))
                if self.parse_WSC_until(delimiters[1], tokens):
                    return set_seq
            else:
                tokens.send(t)
                tokens.throw(ValueError,
                             'While parsing, expected a comma (,)'
                             f'but found: "{t}"')

    def parse_set(self, tokens: abc.Generator) -> set:
        """Parses a PVL Set.

            <Set> ::= "{{" <WSC>*
                       [ <Value> <WSC>* ( "," <WSC>* <Value> <WSC>* )* ]
                      "}}"

           Returns the decoded <Set> as a Python ``frozenset``.  The PVL
           specification doesn't seem to indicate that a PVL Set
           has distinct values (like a Python ``set``), only that the
           ordering of the values is unimportant.  For now, we will
           implement PVL Sets as Python ``frozenset`` objects.

           They are returned as ``frozenset`` objects because PVL Sets
           can contain as their elements other PVL Sets, but since Python
           ``set``s are non-hashable, they cannot be members of a set,
           however, ``frozenset``s can.

           {}
        """.format(_tokens_docstring)
        return frozenset(self._parse_set_seq(self.grammar.set_delimiters,
                                             tokens))

    def parse_sequence(self, tokens: abc.Generator) -> list:
        """Parses a PVL Sequence.

            <Set> ::= "(" <WSC>*
                       [ <Value> <WSC>* ( "," <WSC>* <Value> <WSC>* )* ]
                      ")"

           Returns the decoded <Sequence> as a Python ``list``.

           {}
        """.format(_tokens_docstring)

        return self._parse_set_seq(self.grammar.sequence_delimiters, tokens)

    def parse_statement_delimiter(self, tokens: abc.Generator) -> bool:
        """Parses the tokens for a Statement Delimiter.

           *tokens* is expected to be a *generator iterator* which
           provides ``pvl.token`` objects.

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
                return True
            else:
                tokens.send(t)  # Put the next token back into the generator
                return False

    def parse_value(self, tokens: abc.Generator):
        """Parses PVL Values.

            <Value> ::= (<Simple-Value> | <Set> | <Sequence>)
                        [<WSC>* <Units Expression>]

           Returns the decoded <Value> as an appropriate Python object.

           {}
        """.format(_tokens_docstring)
        value = None

        try:
            t = next(tokens)
            value = self.decoder.decode_simple_value(t)
        except ValueError:
            tokens.send(t)
            try:
                value = self.parse_set(tokens)
            except ValueError:
                try:
                    value = self.parse_sequence(tokens)
                except ValueError as err:
                    tokens.throw(ValueError,
                                 'Was expecting a Simple Value, or the '
                                 'beginning of a Set or Sequence, but '
                                 f'found: "{t}"')

        # print(f'in parse_value, value is: {value}')
        units = None
        self.parse_WSC_until(None, tokens)
        try:
            units = self.parse_units(tokens)
            return Units(value, units)
        except (ValueError, StopIteration):
            return value

    def parse_units(self, tokens: abc.Generator) -> str:
        """Parses PVL Units Expression.

            <Units-Expression> ::= "<" [<white-space>] <Units-Value>
                                       [<white-space>] ">"

           and

            <Units-Value> ::= <units-character>
                                [ [ <units-character> | <white-space> ]*
                                    <units-character> ]

           Returns a <Units-Value> as a ``str``.

           {}
        """.format(_tokens_docstring)
        t = next(tokens)

        if not t.startswith(self.grammar.units_delimiters[0]):
            tokens.send(t)
            raise ValueError('Was expecting the start units delimiter, ' +
                             '"{}" '.format(self.grammar.units_delimiters[0]) +
                             f'but found "{t}"')

        if not t.endswith(self.grammar.units_delimiters[1]):
            tokens.send(t)
            raise ValueError('Was expecting the end units delimiter, ' +
                             '"{}" '.format(self.grammar.units_delimiters[1]) +
                             f'at the end, but found "{t}"')

        delim_strip = t.strip(''.join(self.grammar.units_delimiters))

        units_value = delim_strip.strip(''.join(self.grammar.whitespace))

        for d in self.grammar.units_delimiters:
            if d in units_value:
                tokens.throw(ValueError,
                             'Was expecting a units character, but found a '
                             f'unit delimiter, "{d}" instead.')

        return str(units_value)


class OmniParser(PVLParser):

    def parse(self, s: str):
        '''Converts the string to a PVLModule.

           If *any* line ends with a dash (-) followed by a carriage
           return, form-feed, or newline, plus one or more whitespace
           characters on the following line, then those characters, and
           all whitespace characters that begin the next line will
           be removed.
        '''
        nodash = re.sub(r'-[\n\r\f]\s+', '', s)

        return super().parse(nodash)
