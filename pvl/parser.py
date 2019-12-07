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


_tokens_docstring = """*tokens* is expected to be a *generator iterator*
                       which provides ``pvl.token`` objects.  It should
                       allow for a generated object to be 'returned' via
                       the generator's send() function.  Will throw
                       a ``ValueError`` into the *token's* generator
                       iterator (via throw()) if there are any parsing
                       anomalies.
                    """


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

           {}
        '''.format(_tokens_docstring)
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

           {}

            <PVL-Module-Contents> ::=
             ( <Assignment-Statement> | <WSC>* | <Aggregation-Block> )*
             [<End-Statement>]
        """.format(_tokens_docstring)
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

    def parse_aggregation_block(self, tokens: abc.Generator):
        """Parses the tokens for an Aggregation Block, and returns
           the modcls object that is the result of the parsing and
           decoding.

           {}

            <Aggregation-Block> ::= <Begin-Aggegation-Statement>
                (<WSC>* (Assignment-Statement | Aggregation-Block) <WSC>*)+
                <End-Aggregation-Statement>

           The Begin-Aggregation-Statement Name must match the Block-Name in the
           paired End-Aggregation-Statement if a Block-Name is present in the
           End-Aggregation-Statement.
        """.format(_tokens_docstring)
        m = self.modcls()

        block_name = parse_begin_aggregation_statement(tokens)

        for t in tokens:
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

    def _parse_around_equals(self, tokens: abc.Generator) -> None:
        """Parses white space and comments on either side
           of an equals sign.

           {}

           This is shared functionality for Begin Aggregation Statements
           and Assignment Statements.  It basically covers parsing
           anything that has a syntax diagram like this:

             <WSC>* '=' <WSC>*

        """.format(_tokens_docstring)
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

        tokens.send(t)
        return

    def parse_begin_aggregation_statement(self, tokens: abc.Generator) -> str:
        """Parses the tokens for a Begin Aggregation Statement, and returns
           the name Block Name as a ``str``.

           {}

           <Begin-Aggregation-Statement-block> ::=
                <Begin-Aggegation-Statement> <WSC>* '=' <WSC>*
                <Block-Name> [<Statement-Delimiter>]

           Where <Block-Name> ::= <Parameter-Name>

        """.format(_tokens_docstring)
        b = next(tokens)
        if not b.is_begin_aggregation():
            raise ValueError('Expecting a Begin-Aggegation-Statement, but'
                             f'found: {b}')

        self._parse_around_equals(tokens)

        t = next(tokens)
        if t.is_parameter_name():
            block_name = t
        else:
            tokens.throw(ValueError,
                         f'Expecting a Block-Name after "{b} =" '
                         f'but found: "{t}"')

        self.parse_statement_delimiter(tokens)

        return(str(block_name))

    def parse_assignment_statement(self, tokens: abc.Generator) -> tuple:
        """Parses the tokens for an Assignment Statement.

           The returned two-tuple contains the Parameter Name in the
           first element, and the Value in the second.

           {}

            <Assignment-Statement> ::= <Parameter-Name> <WSC>* '=' <WSC>*
                                        <Value> [<Statement-Delimiter>]

        """.format(_tokens_docstring)
        parameter_name = None
        t = next(tokens)
        if t.is_parameter_name():
            parameter_name = str(t)
        else:
            raise ValueError('Expecting a Parameter Name, but'
                             f'found: "{t}"')

        Value = None
        self._parse_around_equals(tokens)

        t = next(tokens)
        if t.is_value():
            tokens.send(t)
            Value = self.parse_value(tokens)
        else:
            tokens.throw(ValueError,
                         f'Expecting a Block-Name after "{begin_agg_stmt} =" '
                         f'but found: "{t}"')

        self.parse_statement_delimiter(tokens)

        return(parameter_name, Value)

    def parse_WSC_until(self, token: str, tokens: abc.Generator) -> bool:
        """Consumes objects from *tokens*, if the object's *.is_WSC()*
           function returns *True*, it will continue until *token* is
           encountered and will return *True*.  If it encounters an object
           that does not meet these conditions, it will 'return' that
           object to *tokens* and will return *False*.

           {}
        """.format(_tokens_docstring)
        for t in tokens:
            if t == token:
                return True
            elif t.is_WSC():
                # If there's a comment, could parse here.
                    pass
            else:
                tokens.send(t)
                return False

    def parse_set(self, tokens: abc.Generator) -> tuple:
        """Parses a PVL Set.

            <Set> ::= "{{" <WSC>*
                       [ <Value> <WSC>* ( "," <WSC>* <Value> <WSC>* )* ]
                      "}}"

           Returns the decoded <Set> as a Python ``set``.

           {}
        """.format(_tokens_docstring)

        t = next(tokens)
        if t != self.grammar.set_delimiters[0]:
            tokens.throw(ValueError,
                         'Expecting a begin Set delimiter '
                         f'"{self.grammar.set_delimiter[0]} =" '
                         f'but found: "{t}"')
        the_set = set()
        # Initial WSC and/or empty set
        if self.parse_WSC_until(self.grammar.set_delimiters[1], tokens):
            return the_set

        # First item:
        the_set.add(self.parse_value(tokens))
        if self.parse_WSC_until(self.grammar.set_delimiters[1], tokens):
            return the_set

        # Remaining items, if any
        for t in tokens:
            if t == ',':
                self.parse_WSC_until(None, tokens)  # consume WSC after ','
                the_set.add(self.parse_value(tokens))
                if self.parse_WSC_until(self.grammar.set_delimiters[1], tokens):
                    return the_set
            else:
                tokens.throw(ValueError,
                             'While parsing a Set, expected a comma (,)'
                             f'but found: "{t}"')

    def parse_statement_delimiter(self, tokens: abc.Generator) -> None:
        """Parses the tokens for a Statement Delimiter.

           {}

            <Statement-Delimiter> ::= <WSC>*
                        (<white-space-character> | <comment> | ';' | <EOF>)

           Although the above structure comes from Figure 2-4
           of the Blue Book, the <white-space-character> and <comment>
           elements are redundant with the presence of [WSC]*
           so it can be simplified to:

            <Statement-Delimiter> ::= <WSC>* [ ';' | <EOF> ]

           Typically written [<Statement-Delimiter>].
        """.format(_tokens_docstring)
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

           Returns the decoded <Value> as an appropriate Python object.

           {}
        """.format(_tokens_docstring)
        value = None
        t = next(tokens)
        if t.is_simple_value:
            value = self.decoder.decode_simple_value(t)
        elif t.startswith(self.grammar.set_delimiters[0]):
            tokens.send(t)
            value = self.parse_set(tokens)
        elif t.startswith(self.grammar.sequence_delimiters[0]):
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
            elif t.startswith(self.grammar.units_delimiters):
                tokens.send(t)
                units = self.parse_units(tokens)
                break
            else:
                break

        if units is not None:
            value = Units(value, units)

        tokens.send(t)  # Put the next token back into the generator
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
            tokens.throw(ValueError,
                         'Was expecting the start units delimiter, ' +
                         '"{}" '.format(self.grammar.units_delimiters[0]) +
                         f'but found "{t}"')

        if not t.endswith(self.grammar.units_delimiters[1]):
            tokens.throw(ValueError,
                         'Was expecting the end units delimiter, ' +
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
