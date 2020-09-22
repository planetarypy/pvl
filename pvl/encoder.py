# -*- coding: utf-8 -*-
"""Parameter Value Langage encoder.

An encoder deals with converting Python objects into
string values that conform to a PVL specification.
"""

# Copyright 2015, 2019-2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import datetime
import re
import textwrap

from collections import abc, namedtuple
from warnings import warn

from .collections import PVLObject, PVLGroup, Quantity
from .grammar import PVLGrammar, ODLGrammar, ISISGrammar
from .token import Token
from .decoder import PVLDecoder, ODLDecoder


class QuantTup(namedtuple("QuantTup", ["cls", "value_prop", "units_prop"])):
    """
    This class is just a convenient namedtuple for internally keeping track
    of quantity classes that encoders can deal with.  In general, users
    should not be instantiating this, instead use your encoder's
    add_quantity_cls() function.
    """


class PVLEncoder(object):
    """An encoder based on the rules in the CCSDS-641.0-B-2 'Blue Book'
    which defines the PVL language.

    :param grammar: A pvl.grammar object, if None or not specified, it will
                    be set to the grammar parameter of *decoder* (if
                    *decoder* is not None) or will default to PVLGrammar().
    :param grammar: defaults to pvl.grammar.PVLGrammar().
    :param decoder: defaults to pvl.decoder.PVLDecoder().
    :param indent: specifies the number of spaces that will be used to
        indent each level of the PVL document, when Groups or Objects
        are encountered, defaults to 2.
    :param width: specifies the number of characters in width that each
        line should have, defaults to 80.
    :param aggregation_end: when True the encoder will print the value
        of the aggregation's Block Name in the End Aggregation Statement
        (e.g. END_GROUP = foo), and when false, it won't (e.g. END_GROUP).
        Defaults to True.
    :param end_delimiter: when True the encoder will print the grammar's
        delimiter (e.g. ';' for PVL) after each statement, when False
        it won't.  Defaults to True.
    :param newline: is the string that will be placed at the end of each
        'line' of output (and counts against *width*), defaults to '\\\\n'.
    :param group_class: must this class will be tested against with
        isinstance() to determine if various elements of the dict-like
        passed to encode() should be encoded as a PVL Group or PVL Object,
        defaults to PVLGroup.
    :param object_class: must be a class that can take a *group_class*
        object in its constructor (essentially converting a *group_class*
        to an *object_class*), otherwise will raise TypeError.  Defaults
        to PVLObject.
    """

    def __init__(
        self,
        grammar=None,
        decoder=None,
        indent: int = 2,
        width: int = 80,
        aggregation_end: bool = True,
        end_delimiter: bool = True,
        newline: str = "\n",
        group_class=PVLGroup,
        object_class=PVLObject,
    ):

        if grammar is None:
            if decoder is not None:
                self.grammar = decoder.grammar
            else:
                self.grammar = PVLGrammar()
        elif isinstance(grammar, PVLGrammar):
            self.grammar = grammar
        else:
            raise Exception

        if decoder is None:
            self.decoder = PVLDecoder(self.grammar)
        elif isinstance(decoder, PVLDecoder):
            self.decoder = decoder
        else:
            raise Exception

        self.indent = indent
        self.width = width
        self.end_delimiter = end_delimiter
        self.aggregation_end = aggregation_end
        self.newline = newline

        # This list of 3-tuples *always* has our own pvl quantity object,
        # and should *only* be added to with self.add_quantity_cls().
        self.quantities = [QuantTup(Quantity, "value", "units")]
        self._import_quantities()

        if issubclass(group_class, abc.Mapping):
            self.grpcls = group_class
        else:
            raise TypeError("The group_class must be a Mapping type.")

        if issubclass(object_class, abc.Mapping):
            self.objcls = object_class
        else:
            raise TypeError("The object_class must be a Mapping type.")

        try:
            self.objcls(self.grpcls())
        except TypeError:
            raise TypeError(
                f"The object_class type ({object_class}) cannot be "
                f"instantiated with an argument that is of type "
                f"group_class ({group_class})."
            )

    def _import_quantities(self):
        warn_str = (
            "The {} library is not present, so {} objects will "
            "not be properly encoded."
        )
        try:
            from astropy import units as u

            self.add_quantity_cls(u.Quantity, "value", "unit")
        except ImportError:
            warn(
                warn_str.format("astropy", "astropy.units.Quantity"),
                ImportWarning,
            )

        try:
            from pint import Quantity as q

            self.add_quantity_cls(q, "magnitude", "units")
        except ImportError:
            warn(warn_str.format("pint", "pint.Quantity"), ImportWarning)

    def add_quantity_cls(self, cls, value_prop: str, units_prop: str):
        """Adds a quantity class to the list of possible
        quantities that this encoder can handle.

        :param cls: The name of a quantity class that can be tested
            with ``isinstance()``.
        :param value_prop: A string that is the property name of
            *cls* that contains the value or magnitude of the quantity
            object.
        :param units_prop: A string that is the property name of
            *cls* that contains the units element of the quantity
            object.
        """
        if not isinstance(cls, type):
            raise TypeError(f"The cls given ({cls}) is not a Python class.")

        # If a quantity object can't encode "one meter" its probably not
        # going to work for us.
        test_cls = cls(1, "m")
        for prop in (value_prop, units_prop):
            if not hasattr(test_cls, prop):
                raise AttributeError(
                    f"The class ({cls}) does not have an "
                    f" attribute named {prop}."
                )

        self.quantities.append(QuantTup(cls, value_prop, units_prop))

    def format(self, s: str, level: int = 0) -> str:
        """Returns a string derived from *s*, which
        has leading space characters equal to
        *level* times the number of spaces specified
        by this encoder's indent property.

        It uses the textwrap library to wrap long lines.
        """

        prefix = level * (self.indent * " ")

        if len(prefix + s + self.newline) > self.width and "=" in s:
            (preq, _, posteq) = s.partition("=")
            new_prefix = prefix + preq.strip() + " = "

            lines = textwrap.wrap(
                posteq.strip(),
                width=(self.width - len(self.newline)),
                replace_whitespace=False,
                initial_indent=new_prefix,
                subsequent_indent=(" " * len(new_prefix)),
                break_long_words=False,
                break_on_hyphens=False,
            )
            return self.newline.join(lines)
        else:
            return prefix + s

    def encode(self, module: abc.Mapping) -> str:
        """Returns a ``str`` formatted as a PVL document based
        on the dict-like *module* object
        according to the rules of this encoder.
        """
        lines = list()
        lines.append(self.encode_module(module, 0))

        end_line = self.grammar.end_statements[0]
        if self.end_delimiter:
            end_line += self.grammar.delimiters[0]

        lines.append(end_line)

        # Final check to ensure we're sending out the right character set:
        s = self.newline.join(lines)

        for i, c in enumerate(s):
            if not self.grammar.char_allowed(c):
                raise ValueError(
                    "Encountered a character that was not "
                    "a valid character according to the "
                    'grammar: "{}", it is in: '
                    '"{}"'.format(c, s[i - 5, i + 5])
                )

        return self.newline.join(lines)

    def encode_module(self, module: abc.Mapping, level: int = 0) -> str:
        """Returns a ``str`` formatted as a PVL module based
        on the dict-like *module* object according to the
        rules of this encoder, with an indentation level
        of *level*.
        """
        lines = list()

        # To align things on the equals sign, just need to normalize
        # the non-aggregation key length:

        non_agg_key_lengths = list()
        for k, v in module.items():
            if not isinstance(v, abc.Mapping):
                non_agg_key_lengths.append(len(k))
        longest_key_len = max(non_agg_key_lengths, default=0)

        for k, v in module.items():
            if isinstance(v, abc.Mapping):
                lines.append(self.encode_aggregation_block(k, v, level))
            else:
                lines.append(
                    self.encode_assignment(k, v, level, longest_key_len)
                )
        return self.newline.join(lines)

    def encode_aggregation_block(
        self, key: str, value: abc.Mapping, level: int = 0
    ) -> str:
        """Returns a ``str`` formatted as a PVL Aggregation Block with
        *key* as its name, and its contents based on the
        dict-like *value* object according to the
        rules of this encoder, with an indentation level
        of *level*.
        """
        lines = list()

        if isinstance(value, self.grpcls):
            agg_keywords = self.grammar.group_pref_keywords
        elif isinstance(value, abc.Mapping):
            agg_keywords = self.grammar.object_pref_keywords
        else:
            raise ValueError("The value {value} is not dict-like.")

        agg_begin = "{} = {}".format(agg_keywords[0], key)
        if self.end_delimiter:
            agg_begin += self.grammar.delimiters[0]
        lines.append(self.format(agg_begin, level))

        lines.append(self.encode_module(value, (level + 1)))

        agg_end = ""
        if self.aggregation_end:
            agg_end += "{} = {}".format(agg_keywords[1], key)
        else:
            agg_end += agg_keywords[1]
        if self.end_delimiter:
            agg_end += self.grammar.delimiters[0]
        lines.append(self.format(agg_end, level))

        return self.newline.join(lines)

    def encode_assignment(
        self, key: str, value, level: int = 0, key_len: int = None
    ) -> str:
        """Returns a ``str`` formatted as a PVL Assignment Statement
        with *key* as its Parameter Name, and its value based
        on *value* object according to the rules of this encoder,
        with an indentation level of *level*.  It also allows for
        an optional *key_len* which indicates the width in characters
        that the Assignment Statement should be set to, defaults to
        the width of *key*.
        """
        if key_len is None:
            key_len = len(key)

        s = ""
        s += "{} = ".format(key.ljust(key_len))

        enc_val = self.encode_value(value)

        if enc_val.startswith(self.grammar.quotes):
            # deal with quoted lines that need to preserve
            # newlines
            s = self.format(s, level)
            s += enc_val

            if self.end_delimiter:
                s += self.grammar.delimiters[0]

            return s
        else:
            s += enc_val

            if self.end_delimiter:
                s += self.grammar.delimiters[0]

            return self.format(s, level)

    def encode_value(self, value) -> str:
        """Returns a ``str`` formatted as a PVL Value based
        on the *value* object according to the rules of this encoder.
        """
        try:
            return self.encode_quantity(value)
        except ValueError:
            return self.encode_simple_value(value)

    def encode_quantity(self, value) -> str:
        """Returns a ``str`` formatted as a PVL Value followed by
        a PVL Units Expression if the *value* object can be
        encoded this way, otherwise raise ValueError."""
        for (cls, v_prop, u_prop) in self.quantities:
            if isinstance(value, cls):
                return self.encode_value_units(
                    getattr(value, v_prop), getattr(value, u_prop)
                )

        raise ValueError(
            f"The value object {value} could not be "
            "encoded as a PVL Value followed by a PVL "
            f"Units Expression, it is of type {type(value)}"
        )

    def encode_value_units(self, value, units) -> str:
        """Returns a ``str`` formatted as a PVL Value from *value*
        followed by a PVL Units Expressions from *units*."""
        value_str = self.encode_simple_value(value)
        units_str = self.encode_units(str(units))
        return f"{value_str} {units_str}"

    def encode_simple_value(self, value) -> str:
        """Returns a ``str`` formatted as a PVL Simple Value based
        on the *value* object according to the rules of this encoder.
        """
        if value is None:
            return self.grammar.none_keyword
        elif isinstance(value, (set, frozenset)):
            return self.encode_set(value)
        elif isinstance(value, list):
            return self.encode_sequence(value)
        elif isinstance(
            value, (datetime.datetime, datetime.date, datetime.time)
        ):
            return self.encode_datetype(value)
        elif isinstance(value, bool):
            if value:
                return self.grammar.true_keyword
            else:
                return self.grammar.false_keyword
        elif isinstance(value, (int, float)):
            return repr(value)
        elif isinstance(value, str):
            return self.encode_string(value)
        else:
            raise TypeError(f"{value!r} is not serializable.")

    def encode_setseq(self, values: abc.Collection) -> str:
        """This function provides shared functionality for
        encode_sequence() and encode_set().
        """
        return ", ".join([self.encode_value(v) for v in values])

    def encode_sequence(self, value: abc.Sequence) -> str:
        """Returns a ``str`` formatted as a PVL Sequence based
        on the *value* object according to the rules of this encoder.
        """
        return "(" + self.encode_setseq(value) + ")"

    def encode_set(self, value: abc.Set) -> str:
        """Returns a ``str`` formatted as a PVL Set based
        on the *value* object according to the rules of this encoder.
        """
        return "{" + self.encode_setseq(value) + "}"

    def encode_datetype(self, value) -> str:
        """Returns a ``str`` formatted as a PVL Date/Time based
        on the *value* object according to the rules of this encoder.
        If *value* is not a datetime date, time, or datetime object,
        it will raise TypeError.
        """
        if isinstance(value, datetime.datetime):
            return self.encode_datetime(value)
        elif isinstance(value, datetime.date):
            return self.encode_date(value)
        elif isinstance(value, datetime.time):
            return self.encode_time(value)
        else:
            raise TypeError(f"{value!r} is not a datetime type.")

    @staticmethod
    def encode_date(value: datetime.date) -> str:
        """Returns a ``str`` formatted as a PVL Date based
        on the *value* object according to the rules of this encoder.
        """
        return f"{value:%Y-%m-%d}"

    @staticmethod
    def encode_time(value: datetime.time) -> str:
        """Returns a ``str`` formatted as a PVL Time based
        on the *value* object according to the rules of this encoder.
        """
        s = f"{value:%H:%M}"

        if value.microsecond:
            s += f":{value:%S.%f}"
        elif value.second:
            s += f":{value:%S}"

        return s

    def encode_datetime(self, value: datetime.datetime) -> str:
        """Returns a ``str`` formatted as a PVL Date/Time based
        on the *value* object according to the rules of this encoder.
        """
        date = self.encode_date(value)
        time = self.encode_time(value)
        return date + "T" + time

    def needs_quotes(self, s: str) -> bool:
        """Returns true if *s* must be quoted according to this
        encoder's grammar, false otherwise.
        """
        if any(c in self.grammar.whitespace for c in s):
            return True

        if s in self.grammar.reserved_keywords:
            return True

        tok = Token(s, grammar=self.grammar, decoder=self.decoder)
        return not tok.is_unquoted_string()

    def encode_string(self, value) -> str:
        """Returns a ``str`` formatted as a PVL String based
        on the *value* object according to the rules of this encoder.
        """
        s = str(value)

        if self.needs_quotes(s):
            for q in self.grammar.quotes:
                if q not in s:
                    return q + s + q
            else:
                raise ValueError(
                    "All of the quote characters, "
                    f"{self.grammar.quotes}, were in the "
                    f'string ("{s}"), so it could not be quoted.'
                )
        else:
            return s

    def encode_units(self, value: str) -> str:
        """Returns a ``str`` formatted as a PVL Units Value based
        on the *value* object according to the rules of this encoder.
        """
        return (
            self.grammar.units_delimiters[0]
            + value
            + self.grammar.units_delimiters[1]
        )


class ODLEncoder(PVLEncoder):
    """An encoder based on the rules in the PDS3 Standards Reference
    (version 3.8, 27 Feb 2009) Chapter 12: Object Description
    Language Specification and Usage for ODL only.  This is
    almost certainly not what you want.  There are very rarely
    cases where you'd want to use ODL that you wouldn't also want
    to use the PDS Label restrictions, so you probably really want
    the PDSLabelEncoder class, not this one.  Move along.

    It extends PVLEncoder.

    :param grammar: defaults to pvl.grammar.ODLGrammar().
    :param decoder: defaults to pvl.decoder.ODLDecoder().
    :param end_delimiter: defaults to False.
    :param newline: defaults to '\\\\r\\\\n'.
    """

    def __init__(
        self,
        grammar=None,
        decoder=None,
        indent=2,
        width=80,
        aggregation_end=True,
        end_delimiter=False,
        newline="\r\n",
    ):

        if grammar is None:
            grammar = ODLGrammar()

        if decoder is None:
            decoder = ODLDecoder(grammar)

        super().__init__(
            grammar,
            decoder,
            indent,
            width,
            aggregation_end,
            end_delimiter,
            newline,
        )

    def encode(self, module: abc.Mapping) -> str:
        """Extends parent function, but ODL requires that there must be
        a spacing or format character after the END statement and this
        adds the encoder's ``newline`` sequence.
        """
        s = super().encode(module)
        return s + self.newline

    def is_scalar(self, value) -> bool:
        """Returns a boolean indicating whether the *value* object
        qualifies as an ODL 'scalar_value'.

        ODL defines a 'scalar-value' as a numeric_value, a
        date_time_string, a text_string_value, or a symbol_value.

        For Python, these correspond to the following:

        * numeric_value: int, float, and Quantity whose value
          is int or float
        * date_time_string: datetime objects
        * text_string_value: str
        * symbol_value: str

        """
        for quant in self.quantities:
            if isinstance(value, quant.cls):
                if isinstance(getattr(value, quant.value_prop), (int, float)):
                    return True

        if isinstance(
            value,
            (int, float, datetime.date, datetime.datetime, datetime.time, str),
        ):
            return True

        return False

    def is_symbol(self, value) -> bool:
        """Returns true if *value* is an ODL Symbol String, false otherwise.

        An ODL Symbol String is enclosed by single quotes
        and may not contain any of the following characters:

        1. The apostrophe, which is reserved as the symbol string delimiter.
        2. ODL Format Effectors
        3. Control characters

        This means that an ODL Symbol String is a subset of the PVL
        quoted string, and will be represented in Python as a ``str``.
        """
        if isinstance(value, str):
            if "'" in value:  # Item 1
                return False

            for fe in self.grammar.format_effectors:  # Item 2
                if fe in value:
                    return False

            if value.isprintable() and len(value) > 0:  # Item 3
                return True
        else:
            return False

    @staticmethod
    def is_identifier(value):
        """Returns true if *value* is an ODL Identifier, false otherwise.

        An ODL Identifier is composed of letters, digits, and underscores.
        The first character must be a letter, and the last must not
        be an underscore.
        """
        if isinstance(value, str):
            if len(value) == 0:
                return False

            try:
                # Ensure we're dealing with ASCII
                value.encode(encoding="ascii")

                # value can't start with a letter or end with an underbar
                if not value[0].isalpha() or value.endswith("_"):
                    return False

                for c in value:
                    if not (c.isalpha() or c.isdigit() or c == "_"):
                        return False
                else:
                    return True

            except UnicodeError:
                return False
        else:
            return False

    def needs_quotes(self, s: str) -> bool:
        """Return true if *s* is an ODL Identifier, false otherwise.

        Overrides parent function.
        """
        return not self.is_identifier(s)

    def is_assignment_statement(self, s) -> bool:
        """Returns true if *s* is an ODL Assignment Statement, false otherwise.

        An ODL Assignment Statement is either an
        element_identifier or a namespace_identifier
        joined to an element_identifier with a colon.
        """
        if self.is_identifier(s):
            return True

        (ns, _, el) = s.partition(":")

        if self.is_identifier(ns) and self.is_identifier(el):
            return True

        return False

    def encode_assignment(self, key, value, level=0, key_len=None) -> str:
        """Overrides parent function by restricting the length of
        keywords and enforcing that they be ODL Identifiers
        and uppercasing their characters.
        """

        if key_len is None:
            key_len = len(key)

        if len(key) > 30:
            raise ValueError(
                "ODL keywords must be 30 characters or less "
                f"in length, this one is longer: {key}"
            )

        if (
            key.startswith("^") and self.is_assignment_statement(key[1:])
        ) or self.is_assignment_statement(key):
            ident = key.upper()
        else:
            raise ValueError(
                f'The keyword "{key}" is not a valid ODL ' "Identifier."
            )

        s = "{} = ".format(ident.ljust(key_len))
        s += self.encode_value(value)

        if self.end_delimiter:
            s += self.grammar.delimiters[0]

        return self.format(s, level)

    def encode_sequence(self, value) -> str:
        """Extends parent function, as ODL only allows one- and
        two-dimensional sequences of ODL scalar_values.
        """
        if len(value) == 0:
            raise ValueError("ODL does not allow empty Sequences.")

        for v in value:  # check the first dimension (list of elements)
            if isinstance(v, list):
                for i in v:  # check the second dimension (list of lists)
                    if isinstance(i, list):
                        # Shouldn't be lists of lists of lists.
                        raise ValueError(
                            "ODL only allows one- and two- "
                            "dimensional Sequences, but "
                            f"this has more: {value}"
                        )
                    elif not self.is_scalar(i):
                        raise ValueError(
                            "ODL only allows scalar_values "
                            f"within sequences: {v}"
                        )

            elif not self.is_scalar(v):
                raise ValueError(
                    "ODL only allows scalar_values within " f"sequences: {v}"
                )

        return super().encode_sequence(value)

    def encode_set(self, values) -> str:
        """Extends parent function, ODL only allows sets to contain
        scalar values.
        """

        if not all(map(self.is_scalar, values)):
            raise ValueError(
                f"ODL only allows scalar values in sets: {values}"
            )

        return super().encode_set(values)

    def encode_value(self, value):
        """Extends parent function by only allowing Units Expressions for
        numeric values.
        """
        for quant in self.quantities:
            if isinstance(value, quant.cls):
                if isinstance(getattr(value, quant.value_prop), (int, float)):
                    return super().encode_value(value)
                else:
                    raise ValueError(
                        "Unit expressions are only allowed "
                        f"following numeric values: {value}"
                    )

        return super().encode_value(value)

    def encode_string(self, value):
        """Extends parent function by appropriately quoting Symbol
        Strings.
        """
        if self.is_identifier(value):
            return value
        elif self.is_symbol(value):
            return "'" + value + "'"
        else:
            return super().encode_string(value)

    def encode_time(self, value: datetime.time) -> str:
        """Extends parent function since ODL allows a time zone offset
        from UTC to be included, and otherwise recommends that times
        be suffixed with a 'Z' to clearly indicate that they are in UTC.
        """

        t = super().encode_time(value)

        if value.tzinfo is None or value.tzinfo == 0:
            return t + "Z"
        else:
            td_str = str(value.utcoffset())
            (h, m, s) = td_str.split(":")
            if s != "00":
                raise ValueError(
                    "The datetime value had a timezone offset "
                    f"with seconds values ({value}) which is "
                    "not allowed in ODL."
                )
            if m == "00":
                return t + "+" + h
            else:
                return t + f"+{h}:{m}"

    def encode_units(self, value) -> str:
        """Overrides parent function since ODL limits what characters
        and operators can be present in Units Expressions.
        """

        # if self.is_identifier(value.strip('*/()-')):
        if self.is_identifier(re.sub(r"[\s*/()-]", "", value)):

            if "**" in value:
                exponents = re.findall(r"\*\*.+?", value)
                for e in exponents:
                    if re.search(r"\*\*-?\d+", e) is None:
                        raise ValueError(
                            "The exponentiation operator (**) in "
                            f'this Units Expression "{value}" '
                            "is not a decimal integer."
                        )

            return (
                self.grammar.units_delimiters[0]
                + value
                + self.grammar.units_delimiters[1]
            )
        else:
            raise ValueError(
                f'The value, "{value}", does not conform to '
                "the specification for an ODL Units Expression."
            )


class PDSLabelEncoder(ODLEncoder):
    """An encoder based on the rules in the PDS3 Standards Reference
    (version 3.8, 27 Feb 2009) Chapter 12: Object Description
    Language Specification and Usage and writes out labels that
    conform to the PDS 3 standards.

    It extends ODLEncoder.

    You are not allowed to chose *end_delimiter* or *newline*
    as the parent class allows, because to be PDS-compliant,
    those are fixed choices.

    In PVL and ODL, the OBJECT and GROUP aggregations are
    interchangable, but the PDS applies restrictions to what can
    appear in a GROUP.  If *convert_group_to_object* is True,
    and a GROUP does not conform to the PDS definition of a GROUP,
    then it will be written out as an OBJECT.  If it is False,
    then an exception will be thrown if incompatible GROUPs are
    encountered.

    *tab_replace* should indicate the number of space characters
    to replace horizontal tab characters with (since tabs aren't
    allowed in PDS labels).  If this is set to zero, tabs will not
    be replaced with spaces.  Defaults to 4.
    """

    def __init__(
        self,
        grammar=None,
        decoder=None,
        indent=2,
        width=80,
        aggregation_end=True,
        convert_group_to_object=True,
        tab_replace=4,
    ):

        super().__init__(
            grammar,
            decoder,
            indent,
            width,
            aggregation_end,
            end_delimiter=False,
            newline="\r\n",
        )

        self.convert_group_to_object = convert_group_to_object
        self.tab_replace = tab_replace

    def count_aggs(
        self, module: abc.Mapping, obj_count: int = 0, grp_count: int = 0
    ) -> tuple((int, int)):
        """Returns the count of OBJECT and GROUP aggregations
        that are contained within the *module* as a two-tuple
        in that order.
        """
        # This currently just counts the values in the passed
        # in module, it does not 'recurse' if those aggregations also
        # may contain aggregations.

        for k, v in module.items():
            if isinstance(v, abc.Mapping):
                if isinstance(v, self.grpcls):
                    grp_count += 1
                elif isinstance(v, self.objcls):
                    obj_count += 1
                else:
                    # We treat other dict-like Python objects as
                    # PVL Objects for the purposes of this count,
                    # because that is how they will be encoded.
                    obj_count += 1

        return obj_count, grp_count

    def encode(self, module: abc.MutableMapping) -> str:
        """Extends the parent function, by adding a restriction.
        For PDS, if there are any GROUP elements, there must be at
        least one OBJECT element in the label.  Behavior here
        depends on the value of this encoder's convert_group_to_object
        property.
        """
        (obj_count, grp_count) = self.count_aggs(module)

        if grp_count > 0 and obj_count < 1:
            if self.convert_group_to_object:
                for k, v in module.items():
                    # First try to convert any GROUPs that would not
                    # be valid PDS GROUPs.
                    if isinstance(v, self.grpcls) and not self.is_PDSgroup(v):
                        module[k] = self.objcls(v)
                        break
                else:
                    # Then just convert the first GROUP
                    for k, v in module.items():
                        if isinstance(v, self.grpcls):
                            module[k] = self.objcls(v)
                            break
                    else:
                        raise ValueError(
                            "Couldn't convert any of the GROUPs " "to OBJECTs."
                        )
            else:
                raise ValueError(
                    "This module has a GROUP element, but no "
                    "OBJECT elements, which is not allowed by "
                    "the PDS.  You could set "
                    "*convert_group_to_object* to *True* on the "
                    "encoder to try and convert a GROUP "
                    "to an OBJECT."
                )

        s = super().encode(module)
        if self.tab_replace > 0:
            return s.replace("\t", (" " * self.tab_replace))
        else:
            return s

    def is_PDSgroup(self, group: abc.Mapping) -> bool:
        """Returns true if the dict-like *group* qualifies as a PDS Group,
        false otherwise.

        PDS applies the following restrictions to GROUPS:

        1. The GROUP structure may only be used in a data product
           label which also contains one or more data OBJECT definitions.
        2. The GROUP statement must contain only attribute assignment
           statements, include pointers, or related information pointers
           (i.e., no data location pointers). If there are multiple
           values, a single statement must be used with either sequence
           or set syntax; no attribute assignment statement or pointer
           may be repeated.
        3. GROUP statements may not be nested.
        4. GROUP statements may not contain OBJECT definitions.
        5. Only PSDD elements may appear within a GROUP statement.
           *PSDD is not defined anywhere in the PDS document, so don't
           know how to test for it.*
        6. The keyword contents associated with a specific GROUP
           identifier must be identical across all labels of a single data
           set (with the exception of the “PARAMETERS” GROUP, as
           explained).

        Use of the GROUP structure must be coordinated with the
        responsible PDS discipline Node.

        Items 1 & 6 and the final sentence above, can't really be tested
        by examining a single group, but must be dealt with in a larger
        context.  The ODLEncoder.encode_module() handles #1, at least.
        You're on your own for the other two issues.

        Item 5: *PSDD* is not defined anywhere in the ODL PDS document,
        so don't know how to test for it.
        """
        (obj_count, grp_count) = self.count_aggs(group)

        # Items 3 and 4:
        if obj_count != 0 or grp_count != 0:
            return False

        # Item 2, no data location pointers:
        for k, v in group.items():
            if k.startswith("^"):
                if isinstance(v, int):
                    return False
                else:
                    for quant in self.quantities:
                        if isinstance(v, quant.cls) and isinstance(
                            getattr(v, quant.value_prop), int
                        ):
                            return False

        # Item 2, no repeated keys:
        keys = list(group.keys())
        if len(keys) != len(set(keys)):
            return False

        return True

    def encode_aggregation_block(self, key, value, level=0):
        """Extends parent function because PDS has restrictions on
        what may be in a GROUP.

        If the encoder's *convert_group_to_object* parameter is True,
        and a GROUP does not conform to the PDS definition of a GROUP,
        then it will be written out as an OBJECT.  If it is False,
        then an exception will be thrown.
        """

        # print('value at top:')
        # print(value)

        if isinstance(value, self.grpcls) and not self.is_PDSgroup(value):
            if self.convert_group_to_object:
                value = self.objcls(value)
            else:
                raise ValueError(
                    "This GROUP element is not a valid PDS "
                    "GROUP.  You could set "
                    "*convert_group_to_object* to *True* on the "
                    "encoder to try and convert the GROUP"
                    "to an OBJECT."
                )

        # print('value at bottom:')
        # print(value)

        return super().encode_aggregation_block(key, value, level)

    def encode_set(self, values) -> str:
        """Extends parent function because PDS only allows symbol values
        and integers within sets.
        """
        for v in values:
            if not self.is_symbol(v) and not isinstance(v, int):
                raise ValueError(
                    "The PDS only allows integers and symbols "
                    f"in sets: {values}"
                )

        return super().encode_set(values)

    def encode_time(self, value: datetime.time) -> str:
        """Extends the PVLEncoder's encode_time() function because
        even though ODL allows for timezones, PDS does not.

        Not in the section on times, but at the end of the PDS
        ODL document, in section 12.7.3, para 14, it indicates that
        alternate time zones may not be used in a PDS label, only
        UTC.
        """
        t = PVLEncoder.encode_time(value)

        if value.tzinfo is None or value.tzinfo.utcoffset(
            None
        ) == datetime.timedelta(0):
            return t + "Z"
        else:
            raise ValueError(
                "PDS labels should only have UTC times, but "
                f"this time has a timezone: {value}"
            )


class ISISEncoder(PVLEncoder):
    """An encoder for writing PVL text that can be parsed by the
    ISIS PVL text parser.

    The ISIS3 implementation (as of 3.9) of PVL/ODL (like) does not
    strictly follow any of the published standards. It was based
    on PDS3 ODL from the 1990s, but has several extensions adopted
    from existing and prior data sets from ISIS2, PDS, JAXA, ISRO,
    ..., and extensions used only within ISIS files (cub, net). This
    is one of the reasons using ISIS cube files or PVL text written by
    ISIS as an archive format has been strongly discouraged.

    Since there is no specification, only a detailed analysis of
    the ISIS software that parses and writes its PVL text would
    yield a strategy for parsing it.  This encoder is most likely the
    least reliable for that reason.  We welcome bug reports to help
    extend our coverage of this flavor of PVL text.

    :param grammar: defaults to pvl.grammar.ISISGrammar().
    :param decoder: defaults to pvl.decoder.PVLDecoder().
    :param end_delimiter: defaults to False.
    :param newline: defaults to '\\\\n'.
    """

    def __init__(
        self,
        grammar=None,
        decoder=None,
        indent=2,
        width=80,
        aggregation_end=True,
        end_delimiter=False,
        newline="\n",
    ):

        if grammar is None:
            grammar = ISISGrammar()

        if decoder is None:
            decoder = PVLDecoder(grammar)

        super().__init__(
            grammar,
            decoder,
            indent,
            width,
            aggregation_end,
            end_delimiter,
            newline,
        )
