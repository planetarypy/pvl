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
from warnings import warn

from ._collections import PVLModule, PVLGroup, PVLObject, Units
from .token import token as Token
from .grammar import grammar as Grammar
from .decoder import PVLDecoder as Decoder


class PVLParser(object):

    def __init__(self, grammar=Grammar(), decoder=Decoder(),
                 module_class=PVLModule()):
        self.errors = []
        self.grammar = grammar
        self.decoder = decoder

        if isinstance(module_class, PVLModule):
            self.modcls = module_class
        else:
            raise Exception

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

    def parse(self, tokens: list):
        '''Accepts a list of Tokens, and returns a PVLModule.
        '''
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

    def parse_statement_delimiter(self, tokens: abc.Generator) -> None:
        """Parses the tokens for a Statement Delimiter.

           *tokens* is expected to be a *generator iterator* which
           provides ``pvl.token`` objects, and should allow for a
           generated object to be 'returned' via the generator's send()
           function.

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
                return
            else:
                tokens.send(t)  # Put the next token back into the generator
                return

    def parse_value(self, tokens: abc.Generator) -> tuple:
        """Parses PVL Values.

            <Value> ::= (<Simple-Value> | <Set> | <Sequence>)
                        [<WSC>* <Units Expression>]

           Returns the decoded <Value> as an appropriate Python object,
           *tokens* is expected to be a *generator iterator* which
           provides ``pvl.token`` objects, and should allow for a
           generated object to be 'returned' via the generator's send()
           function.  A ValueError will be thrown into the *generator
           iterator* if there was a parsing error.
        """
        value = None
        t = next(tokens)
        if t.is_simple_value:
            value = self.decoder.decode_simple_value(t)
        elif t.startswith(self.grammar.set_delimiter[0]):
            tokens.send(t)
            value = self.parse_set(tokens)
        elif t.startswith(self.grammar.sequence_delimiter[0]):
            tokens.send(t)
            value = self.parse_sequence(tokens)
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
                tokens.send(t)
                units = self.parse_units(tokens)
                break
            else:
                break

        if units is not None:
            value = Units(value, units)

        tokens.send(t)  # Put the next token back into the generator
        return value

    def parse_units(self, t: str, tokens: abc.Generator) -> str:
        """Parses PVL Units Expression.

            <Units-Expression> ::= "<" <WSC>* <Units-Value> <WSC>* ">"

           and

            <Units-Value> ::= <units-character>
                                [ ( <units-character> | <WSC>* )* ]

           Returns a <Units-Value> as a ``str``.  *t* is expected to
           be a ``str`` (but is likely to be a ``pvl.token``) that
           compares true to the start units delimiter (typically "<").
           *tokens* is expected to be a *generator iterator* which
           provides ``pvl.token`` objects.

           Only consumes *tokens* through the final end units delimiter
           (typically ">")  Will throw a ``ValueError`` back to the
           *tokens* generator iterator if there are any parsing anomalies.
        """
        if t != self.grammar.units_delimiters[0]:
            tokens.throw(ValueError,
                         'Was expecting the start units delimiter, ' +
                         '"{}" '.format(self.grammar.units_delimiters[0]) +
                         f'but found "{t}"')

        for t in tokens:
            if t.is_WSC():
                # If there's a comment, could parse here.
                pass

        if t in self.grammar.units_delimiters:
            tokens.throw(ValueError,
                         'Was expecting a units character, but found a'
                         f'unit delimiter, "{t}" instead.')

        units = ''
        for t in tokens:
            if t == self.grammar.units_delimiters[1]:
                return units
            elif t == self.grammar.units_delimiters[0]:
                tokens.throw(ValueError,
                             'Was parsing a Units-Expression "{units}", '
                             'but came across another starting unit '
                             f'delimiter: "{t}"')
            else:
                units + t
