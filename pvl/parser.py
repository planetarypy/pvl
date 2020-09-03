# -*- coding: utf-8 -*-
"""Parameter Value Language parser.

The definition of PVL used in this module is based on the Consultive
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

Throughout this module, various parser functions will take a *tokens:
collections.abc.Generator* parameter.  In all cases, *tokens* is
expected to be a *generator iterator* which provides ``pvl.token.Token``
objects.  It should allow for a generated object to be 'returned'
via the generator's send() function.  When parsing the first object
from *tokens*, if an unexpected object is encountered, it will
'return' the object to *tokens*, and raise a ``ValueError``, so
that ``try``-``except`` blocks can be used, and the *generator
iterator* is left in a good state. However, if a parsing anomaly
is discovered deeper in parsing a PVL sequence, then a ``ValueError``
will be thrown into the *tokens* generator iterator (via .throw()).
"""

# Copyright 2015, 2017, 2019-2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import collections.abc as abc
import re

from .collections import MutableMappingSequence, PVLModule, PVLGroup, PVLObject
from .token import Token
from .grammar import PVLGrammar, OmniGrammar
from .decoder import PVLDecoder, OmniDecoder
from .lexer import lexer as Lexer
from .exceptions import LexerError, ParseError, linecount


class EmptyValueAtLine(str):
    """Empty string to be used as a placeholder for a parameter without
    a value.

    When a label contains a parameter without a value, it is normally
    considered a broken label in PVL. To allow parsing to continue,
    we can rectify the broken parameter-value pair by setting the
    value to have a value of EmptyValueAtLine, which is an empty
    string (and can be treated as such) with some additional properties.

    The argument *lineno* should be the line number of the error from
    the original document, which will be available as a property.

    Examples::
      >>> from pvl.parser import EmptyValueAtLine
      >>> EV1 = EmptyValueAtLine(1)
      >>> EV1
      EmptyValueAtLine(1 does not have a value. Treat as an empty string)
      >>> EV1.lineno
      1
      >>> print(EV1)
      <BLANKLINE>

      >>> EV1 + 'foo'
      'foo'
      >>> # Can be turned into an integer and float as 0:
      >>> int(EV1)
      0
      >>> float(EV1)
      0.0
    """

    def __new__(cls, lineno, *args, **kwargs):
        self = super(EmptyValueAtLine, cls).__new__(cls, "")
        self.lineno = lineno
        return self

    def __int__(self):
        return 0

    def __float__(self):
        return 0.0

    def __repr__(self):
        return (
            "{}({} does not ".format(type(self).__name__, self.lineno)
            + "have a value. Treat as an empty string)"
        )


class PVLParser(object):
    """A parser based on the rules in the CCSDS-641.0-B-2 'Blue Book'
    which defines the PVL language.

    :param grammar: A pvl.grammar object, if None or not specified, it will
                    be set to the grammar parameter of *decoder* (if
                    *decoder* is not None) or will default to
                    :class:`pvl.grammar.OmniGrammar()`.
    :param decoder: defaults to :class:`pvl.decoder.OmniDecoder()`.
    :param lexer_fn: must be a lexer function that takes a ``str``,
        a grammar, and a decoder, as :func:`pvl.lexer.lexer()` does,
        which is the default if none is given.
    :param module_class: must be a subclass of PVLModule, and is the type
        of object that will be returned from this parser's :func:`parse()`
        function.
    :param group_class: must be a subclass of PVLGroup, and is the type
        that will be used to hold PVL elements when a PVL Group is
        encountered during parsing, and must be able to be added to
        via an ``.append()`` function which should take a two-tuple
        of name and value.
    :param object_class: must be a subclass of PVLObject, and is the type
        that will be used to hold PVL elements when a PVL Object is
        encountered during parsing, otherwise similar to *group_class*.
    """

    def __init__(
        self,
        grammar=None,
        decoder=None,
        lexer_fn=None,
        module_class=PVLModule,
        group_class=PVLGroup,
        object_class=PVLObject,
    ):

        self.errors = []
        self.doc = ""

        if lexer_fn is None:
            self.lexer = Lexer
        else:
            self.lexer = lexer_fn

        if grammar is None:
            if decoder is not None:
                self.grammar = decoder.grammar
            else:
                self.grammar = OmniGrammar()
        elif isinstance(grammar, PVLGrammar):
            self.grammar = grammar
        else:
            raise TypeError("The grammar must be an instance of pvl.grammar.")

        if decoder is None:
            self.decoder = OmniDecoder(grammar=self.grammar)
        elif isinstance(decoder, PVLDecoder):
            self.decoder = decoder
        else:
            raise TypeError(
                "The decode must be an instance of pvl.PVLDecoder."
            )

        if issubclass(module_class, MutableMappingSequence):
            self.modcls = module_class
        else:
            raise TypeError(
                "The module_class must be a "
                "pvl.collections.MutableMappingSequence."
            )

        if issubclass(group_class, MutableMappingSequence):
            self.grpcls = group_class
        else:
            raise TypeError(
                "The group_class must be a "
                "pvl.collections.MutableMappingSequence."
            )

        if issubclass(object_class, MutableMappingSequence):
            self.objcls = object_class
        else:
            raise TypeError(
                "The object_class must be a "
                "pvl.collections.MutableMappingSequence."
            )

    def parse(self, s: str):
        """Converts the string, *s* to a PVLModule."""
        self.doc = s
        tokens = self.lexer(s, g=self.grammar, d=self.decoder)
        module = self.parse_module(tokens)
        module.errors = sorted(self.errors)
        return module

    def aggregation_cls(self, begin: str):
        """Returns an initiated object of the group_class or object_class
        as specified on this parser's creation, according to the value
        of *begin*.  If *begin* does not match the Group or Object
        keywords for this parser's grammar, then it will raise a
        ValueError.
        """
        begin_fold = begin.casefold()
        for gk in self.grammar.group_keywords.keys():
            if begin_fold == gk.casefold():
                return self.grpcls()

        for ok in self.grammar.object_keywords.keys():
            if begin_fold == ok.casefold():
                return self.objcls()

        raise ValueError(
            f'The value "{begin}" did not match a Begin '
            "Aggregation Statement."
        )

    def parse_module(self, tokens: abc.Generator):
        """Parses the tokens for a PVL Module.

         <PVL-Module-Contents> ::=
          ( <Assignment-Statement> | <WSC>* | <Aggregation-Block> )*
          [<End-Statement>]

        """
        m = self.modcls()

        parsing = True
        while parsing:
            # print(f'top of while parsing: {m}')
            parsing = False
            for p in (
                self.parse_aggregation_block,
                self.parse_assignment_statement,
                self.parse_end_statement,
            ):
                try:
                    self.parse_WSC_until(None, tokens)
                    # t = next(tokens)
                    # print(f'next token: {t}, {t.pos}')
                    # tokens.send(t)
                    parsed = p(tokens)
                    # print(f'parsed: {parsed}')
                    if parsed is None:  # because parse_end_statement returned
                        return m
                    else:
                        m.append(*parsed)
                        parsing = True
                except LexerError:
                    raise
                except ValueError:
                    pass
            try:
                (m, keep_parsing) = self.parse_module_post_hook(m, tokens)
                if keep_parsing:
                    parsing = True
                else:
                    return m
            except Exception:
                pass

        # print(f'got to bottom: {m}')
        t = next(tokens)
        tokens.throw(
            ValueError,
            "Expecting an Aggregation Block, an Assignment "
            "Statement, or an End Statement, but found "
            f'"{t}" ',
        )

    def parse_module_post_hook(
        self, module: MutableMappingSequence, tokens: abc.Generator
    ):
        """This function is meant to be overridden by subclasses
        that may want to perform some extra processing if
        'normal' parse_module() operations fail to complete.
        See OmniParser for an example.

        This function shall return a two-tuple, with the first item
        being the *module* (altered by processing or unaltered), and
        the second item being a boolean that will signal whether
        the tokens should continue to be parsed to accumulate more
        elements into the returned *module*, or whether the
        *module* is in a good state and should be returned by
        parse_module().

        If the operations within this function are unsuccessful,
        it should raise an exception (any exception descended from
        Exception), which will result in the operation of parse_module()
        as if it were not overridden.
        """
        raise Exception

    def parse_aggregation_block(self, tokens: abc.Generator):
        """Parses the tokens for an Aggregation Block, and returns
        the modcls object that is the result of the parsing and
        decoding.

         <Aggregation-Block> ::= <Begin-Aggegation-Statement>
             (<WSC>* (Assignment-Statement | Aggregation-Block) <WSC>*)+
             <End-Aggregation-Statement>

        The Begin-Aggregation-Statement Name must match the Block-Name
        in the paired End-Aggregation-Statement if a Block-Name is
        present in the End-Aggregation-Statement.
        """
        (begin, block_name) = self.parse_begin_aggregation_statement(tokens)

        agg = self.aggregation_cls(begin)

        while True:
            self.parse_WSC_until(None, tokens)
            try:
                agg.append(*self.parse_aggregation_block(tokens))
            except ValueError:
                try:
                    agg.append(*self.parse_assignment_statement(tokens))
                    # print(f'agg: {agg}')
                    # t = next(tokens)
                    # print(f'next token is: {t}')
                    # tokens.send(t)
                except LexerError:
                    raise
                except ValueError:
                    # t = next(tokens)
                    # print(f'parsing agg block, next token is: {t}')
                    # tokens.send(t)
                    self.parse_end_aggregation(begin, block_name, tokens)
                    break

        return block_name, agg

    def parse_around_equals(self, tokens: abc.Generator) -> None:
        """Parses white space and comments on either side
        of an equals sign.

        *tokens* is expected to be a *generator iterator* which
        provides ``pvl.token`` objects.

        This is shared functionality for Begin Aggregation Statements
        and Assignment Statements.  It basically covers parsing
        anything that has a syntax diagram like this:

          <WSC>* '=' <WSC>*

        """
        if not self.parse_WSC_until("=", tokens):
            try:
                t = next(tokens)
                tokens.send(t)
                raise ValueError(f'Expecting "=", got: {t}')
            except StopIteration:
                raise ParseError('Expecting "=", but ran out of tokens.')

        self.parse_WSC_until(None, tokens)
        return

    def parse_begin_aggregation_statement(
        self, tokens: abc.Generator
    ) -> tuple:
        """Parses the tokens for a Begin Aggregation Statement, and returns
        the name Block Name as a ``str``.

        <Begin-Aggregation-Statement-block> ::=
             <Begin-Aggegation-Statement> <WSC>* '=' <WSC>*
             <Block-Name> [<Statement-Delimiter>]

        Where <Block-Name> ::= <Parameter-Name>

        """
        try:
            begin = next(tokens)
            if not begin.is_begin_aggregation():
                tokens.send(begin)
                raise ValueError(
                    "Expecting a Begin-Aggegation-Statement, but "
                    f"found: {begin}"
                )
        except StopIteration:
            raise ValueError(
                "Ran out of tokens before starting to parse "
                "a Begin-Aggegation-Statement."
            )

        try:
            self.parse_around_equals(tokens)
        except ValueError:
            tokens.throw(
                ValueError, f'Expecting an equals sign after "{begin}" '
            )

        block_name = next(tokens)
        if not block_name.is_parameter_name():
            tokens.throw(
                ValueError,
                f'Expecting a Block-Name after "{begin} =" '
                f'but found: "{block_name}"',
            )

        self.parse_statement_delimiter(tokens)

        return begin, str(block_name)

    def parse_end_aggregation(
        self, begin_agg: str, block_name: str, tokens: abc.Generator
    ) -> None:
        """Parses the tokens for an End Aggregation Statement.

        <End-Aggregation-Statement-block> ::=
             <End-Aggegation-Statement> [<WSC>* '=' <WSC>*
             <Block-Name>] [<Statement-Delimiter>]

        Where <Block-Name> ::= <Parameter-Name>

        """
        end_agg = next(tokens)

        # Need to do a little song and dance to case-independently
        # match the keys:
        for k in self.grammar.aggregation_keywords.keys():
            if k.casefold() == begin_agg.casefold():
                truecase_begin = k
                break
        if (
            end_agg.casefold()
            != self.grammar.aggregation_keywords[truecase_begin].casefold()
        ):
            tokens.send(end_agg)
            raise ValueError(
                "Expecting an End-Aggegation-Statement that "
                "matched the Begin-Aggregation_Statement, "
                f'"{begin_agg}" but found: {end_agg}'
            )

        try:
            self.parse_around_equals(tokens)
        except (ParseError, ValueError):  # No equals statement, which is fine.
            self.parse_statement_delimiter(tokens)
            return None

        t = next(tokens)
        if t != block_name:
            tokens.send(t)
            tokens.throw(
                ValueError,
                f'Expecting a Block-Name after "{end_agg} =" '
                f'that matches "{block_name}", but found: '
                f'"{t}"',
            )

        self.parse_statement_delimiter(tokens)

        return None

    def parse_end_statement(self, tokens: abc.Generator) -> None:
        """Parses the tokens for an End Statement.

        <End-Statement> ::= "END" ( <WSC>* | [<Statement-Delimiter>] )

        """
        try:
            end = next(tokens)
            if not end.is_end_statement():
                tokens.send(end)
                raise ValueError(
                    "Expecting an End Statement, like "
                    f'"{self.grammar.end_statements}" but found '
                    f'"{end}"'
                )

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

         <Assignment-Statement> ::= <Parameter-Name> <WSC>* '=' <WSC>*
                                     <Value> [<Statement-Delimiter>]

        """
        try:
            t = next(tokens)
            if t.is_parameter_name():
                parameter_name = str(t)
            else:
                tokens.send(t)
                raise ValueError(
                    "Expecting a Parameter Name, but " f'found: "{t}"'
                )
        except StopIteration:
            raise ValueError(
                "Ran out of tokens before starting to parse "
                "an Assignment-Statement."
            )

        self.parse_around_equals(tokens)

        try:
            # print(f'parameter name: {parameter_name}')
            value = self.parse_value(tokens)
        except StopIteration:
            raise ParseError(
                "Ran out of tokens to parse after the equals "
                "sign in an Assignment-Statement: "
                f'"{parameter_name} =".',
                t,
            )

        self.parse_statement_delimiter(tokens)

        return parameter_name, value

    @staticmethod
    def parse_WSC_until(token: str, tokens: abc.Generator) -> bool:
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
        """The internal parsing of PVL Sets and Sequences are very
        similar, and this function provides that shared logic.

        *delimiters* are a two-tuple containing the start and end
        characters for the PVL Set or Sequence.
        """
        t = next(tokens)
        if t != delimiters[0]:
            tokens.send(t)
            raise ValueError(
                f'Expecting a begin delimiter "{delimiters[0]}" '
                f'but found: "{t}"'
            )
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
            if t == ",":
                self.parse_WSC_until(None, tokens)  # consume WSC after ','
                set_seq.append(self.parse_value(tokens))
                if self.parse_WSC_until(delimiters[1], tokens):
                    return set_seq
            else:
                tokens.send(t)
                tokens.throw(
                    ValueError,
                    "While parsing, expected a comma (,)" f'but found: "{t}"',
                )

    def parse_set(self, tokens: abc.Generator) -> frozenset:
        """Parses a PVL Set.

         <Set> ::= "{" <WSC>*
                   [ <Value> <WSC>* ( "," <WSC>* <Value> <WSC>* )* ]
                   "}"

        Returns the decoded <Set> as a Python ``frozenset``.  The PVL
        specification doesn't seem to indicate that a PVL Set
        has distinct values (like a Python ``set``), only that the
        ordering of the values is unimportant.  For now, we will
        implement PVL Sets as Python ``frozenset`` objects.

        They are returned as ``frozenset`` objects because PVL Sets
        can contain as their elements other PVL Sets, but since Python
        ``set`` objects are non-hashable, they cannot be members of a set,
        however, ``frozenset`` objects can.
        """
        return frozenset(
            self._parse_set_seq(self.grammar.set_delimiters, tokens)
        )

    def parse_sequence(self, tokens: abc.Generator) -> list:
        """Parses a PVL Sequence.

         <Set> ::= "(" <WSC>*
                   [ <Value> <WSC>* ( "," <WSC>* <Value> <WSC>* )* ]
                   ")"

        Returns the decoded <Sequence> as a Python ``list``.
        """
        return self._parse_set_seq(self.grammar.sequence_delimiters, tokens)

    @staticmethod
    def parse_statement_delimiter(tokens: abc.Generator) -> bool:
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
        """
        value = None

        try:
            t = next(tokens)
            value = self.decoder.decode_simple_value(t)
        except ValueError:
            tokens.send(t)
            for p in (
                self.parse_set,
                self.parse_sequence,
                self.parse_value_post_hook,
            ):
                try:
                    value = p(tokens)
                    break
                except LexerError:
                    # A LexerError is a subclass of ValueError, but
                    # if we get a LexerError, that's a problem and
                    # we need to raise it, and not let it pass.
                    raise
                except ValueError:
                    # Getting a ValueError is a normal conseqence of
                    # one of the parsing strategies not working,
                    # this pass allows us to go to the next one.
                    pass
            else:
                tokens.throw(
                    ValueError,
                    "Was expecting a Simple Value, or the "
                    "beginning of a Set or Sequence, but "
                    f'found: "{t}"',
                )

        # print(f'in parse_value, value is: {value}')
        self.parse_WSC_until(None, tokens)
        try:
            return self.parse_units(value, tokens)
        except (ValueError, StopIteration):
            return value

    def parse_value_post_hook(self, tokens):
        """This function is meant to be overridden by subclasses
        that may want to perform some extra processing if
        'normal' parse_value() operations fail to yield a value.
        See OmniParser for an example.

        This function shall return an appropriate Python value,
        similar to what parse_value() would return.

        If the operations within this function are unsuccessful,
        it should raise a ValueError which will result in the
        operation of parse_value() as if it were not overridden.
        """
        raise ValueError

    def parse_units(self, value, tokens: abc.Generator) -> str:
        """Parses PVL Units Expression.

         <Units-Expression> ::= "<" [<white-space>] <Units-Value>
                                    [<white-space>] ">"

        and

         <Units-Value> ::= <units-character>
                             [ [ <units-character> | <white-space> ]*
                                 <units-character> ]

        Returns the *value* and the <Units-Value> as a ``Units()``
        object.
        """
        t = next(tokens)

        if not t.startswith(self.grammar.units_delimiters[0]):
            tokens.send(t)
            raise ValueError(
                "Was expecting the start units delimiter, "
                + '"{}" '.format(self.grammar.units_delimiters[0])
                + f'but found "{t}"'
            )

        if not t.endswith(self.grammar.units_delimiters[1]):
            tokens.send(t)
            raise ValueError(
                "Was expecting the end units delimiter, "
                + '"{}" '.format(self.grammar.units_delimiters[1])
                + f'at the end, but found "{t}"'
            )

        delim_strip = t.strip("".join(self.grammar.units_delimiters))

        units_value = delim_strip.strip("".join(self.grammar.whitespace))

        for d in self.grammar.units_delimiters:
            if d in units_value:
                tokens.throw(
                    ValueError,
                    "Was expecting a units character, but found a "
                    f'unit delimiter, "{d}" instead.',
                )

        return self.decoder.decode_quantity(value, units_value)


class ODLParser(PVLParser):
    """A parser based on the rules in the PDS3 Standards Reference
       (version 3.8, 27 Feb 2009) Chapter 12: Object Description
       Language Specification and Usage.

       It extends PVLParser.
    """

    def parse_set(self, tokens: abc.Generator) -> set:
        """Overrides the parent function to return
        the decoded <Set> as a Python ``set``.

        The ODL specification only allows scalar_values in Sets,
        since ODL Sets cannot contain other ODL Sets, an ODL Set
        can be represented as a Python ``set`` (unlike PVL Sets,
        which must be represented as a Python ``frozenset`` objects).
        """
        return set(self._parse_set_seq(self.grammar.set_delimiters, tokens))

    def parse_units(self, value, tokens: abc.Generator) -> str:
        """Extends the parent function, since ODL only allows units
        on numeric values, any others will result in a ValueError.
        """

        if isinstance(value, int) or isinstance(value, float):
            return super().parse_units(value, tokens)

        else:
            raise ValueError(
                "ODL Units Expressions can only follow " "numeric values."
            )


class OmniParser(PVLParser):
    """A permissive PVL/ODL/ISIS label parser that attempts to parse
    all forms of "PVL" that are thrown at it.
    """

    def _empty_value(self, pos):
        eq_pos = self.doc.rfind("=", 0, pos)
        lc = linecount(self.doc, eq_pos)
        self.errors.append(lc)
        return EmptyValueAtLine(lc)

    def parse(self, s: str):
        """Extends the parent function.

        If *any* line ends with a dash (-) followed by a carriage
        return, form-feed, or newline, plus one or more whitespace
        characters on the following line, then those characters, and
        all whitespace characters that begin the next line will
        be removed.
        """
        nodash = re.sub(r"-[\n\r\f]\s*", "", s)
        self.doc = nodash

        return super().parse(nodash)

    def parse_module_post_hook(
        self, module: MutableMappingSequence, tokens: abc.Generator
    ):
        """Overrides the parent function to allow for more
        permissive parsing.  If an Assignment-Statement
        is blank, then the value will be assigned an
        EmptyValueAtLine object.
        """
        # It enables this by checking to see if the next thing is an
        # '=' which means there was an empty assigment at the previous
        # equals sign, and then unwinding the stack to give the
        # previous assignment the EmptyValueAtLine() object and trying
        # to continue parsing.

        # print('in hook')
        try:
            t = next(tokens)
            if t == "=" and len(module) != 0:
                (last_k, last_v) = module[-1]
                last_token = Token(
                    last_v, grammar=self.grammar, decoder=self.decoder
                )
                if last_token.is_parameter_name():
                    # Fix the previous entry
                    module.pop()
                    module.append(last_k, self._empty_value(t.pos))
                    # Now use last_token as the parameter name
                    # for the next assignment, and we must
                    # reproduce the last part of parse-assignment:
                    try:
                        # print(f'parameter name: {last_token}')
                        self.parse_WSC_until(None, tokens)
                        value = self.parse_value(tokens)
                        self.parse_statement_delimiter(tokens)
                        module.append(str(last_token), value)
                    except StopIteration:
                        module.append(
                            str(last_token), self._empty_value(t.pos + 1)
                        )
                        return module, False  # return through parse_module()
                else:
                    tokens.send(t)
            else:
                # The next token isn't an equals sign or the module is
                # empty, so we want return the token and signal
                # parse_module() that it should ignore us.
                tokens.send(t)
                raise Exception

            # Peeking at the next token gives us the opportunity to
            # see if we're at the end of tokens, which we want to handle.
            t = next(tokens)
            tokens.send(t)
            return module, True  # keep parsing
        except StopIteration:
            # If we're out of tokens, that's okay.
            return module, False  # return through parse_module()

    def parse_assignment_statement(self, tokens: abc.Generator) -> tuple:
        """Extends the parent function to allow for more
        permissive parsing.  If an Assignment-Statement
        is blank, then the value will be assigned an
        EmptyValueAtLine object.
        """
        try:
            return super().parse_assignment_statement(tokens)
        except ParseError as err:
            if err.token is not None:
                after_eq = self.doc.find("=", err.token.pos) + 1
                return str(err.token), self._empty_value(after_eq)
            else:
                raise

    def parse_value_post_hook(self, tokens: abc.Generator):
        """Overrides the parent function to allow for more
        permissive parsing.

        If the next token is a reserved word or delimiter,
        then it is returned to the *tokens* and an
        EmptyValueAtLine object is returned as the value.
        """

        t = next(tokens)
        # print(f't: {t}')
        truecase_reserved = [
            x.casefold() for x in self.grammar.reserved_keywords
        ]
        trucase_delim = [x.casefold() for x in self.grammar.delimiters]
        if t.casefold() in (truecase_reserved + trucase_delim):
            # print(f'kw: {kw}')
            # if kw.casefold() == t.casefold():
            # print('match')
            tokens.send(t)
            return self._empty_value(t.pos)
        else:
            raise ValueError
