# -*- coding: utf-8 -*-
import datetime
import textwrap
import warnings

from ._collections import PVLAggregation, PVLObject, PVLGroup, Units
from .grammar import grammar as Grammar
from .grammar import ODLgrammar
from .token import token as Token
from .decoder import PVLDecoder, ODLDecoder


class PVLEncoder(object):

    def __init__(self, grammar=None, decoder=None,
                 indent=2, width=80, aggregation_end=True,
                 end_delimiter=True, newline='\n'):

        if grammar is None:
            self.grammar = Grammar()
        elif isinstance(grammar, Grammar):
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

    def format(self, s: str, level=0) -> str:

        prefix = level * (self.indent * ' ')

        if len(prefix + s + self.newline) > self.width and '=' in s:
            (preq, _, posteq) = s.partition('=')
            new_prefix = prefix + preq.strip() + ' = '

            lines = textwrap.wrap(posteq.strip(),
                                  width=(self.width - len(self.newline)),
                                  replace_whitespace=False,
                                  initial_indent=new_prefix,
                                  subsequent_indent=(' ' * len(new_prefix)),
                                  break_long_words=False,
                                  break_on_hyphens=False)
            return self.newline.join(lines)
        else:
            return prefix + s

    def encode(self, module) -> str:
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
                raise ValueError('Encountered a character that was not '
                                 'a valid character according to the '
                                 f'grammar: "{c}", it is in: '
                                 '"{}"'.format(s[i - 5, i + 5]))

        return self.newline.join(lines)

    def encode_module(self, module, level=0):
        lines = list()

        # To align things on the equals sign, just need to normalize
        # the non-aggregation key length:

        non_agg_key_lengths = list()
        for k, v in module.items():
            if not isinstance(v, PVLAggregation):
                non_agg_key_lengths.append(len(k))
        longest_key_len = max(non_agg_key_lengths, default=0)

        for k, v in module.items():
            if isinstance(v, PVLAggregation):
                lines.append(self.encode_aggregation_block(k, v, level))
            else:
                lines.append(self.encode_assignment(k.ljust(longest_key_len),
                                                    v, level))
        return self.newline.join(lines)

    def encode_aggregation_block(self, key, value, level=0):
        lines = list()

        agg_keywords = None
        if isinstance(value, PVLGroup):
            agg_keywords = self.grammar.group_pref_keywords
        elif isinstance(value, PVLObject):
            agg_keywords = self.grammar.object_pref_keywords
        else:
            raise Exception

        agg_begin = '{} = {}'.format(agg_keywords[0], key)
        if self.end_delimiter:
            agg_begin += self.grammar.delimiters[0]
        lines.append(self.format(agg_begin, level))

        lines.append(self.encode_module(value, (level + 1)))

        agg_end = ''
        if self.aggregation_end:
            agg_end += '{} = {}'.format(agg_keywords[1], key)
        else:
            agg_end += agg_keywords[1]
        if self.end_delimiter:
            agg_end += self.grammar.delimiters[0]
        lines.append(self.format(agg_end, level))

        return self.newline.join(lines)

    def encode_assignment(self, key, value, level=0) -> str:
        s = ''
        s += f'{key} = '

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

    def encode_value(self, value):
        if isinstance(value, Units):
            val = self.encode_simple_value(value.value)
            units = self.encode_units(value.units)
            return f'{val} {units}'
        else:
            return self.encode_simple_value(value)

    def encode_simple_value(self, value):
        if value is None:
            return self.grammar.none_keyword
        if isinstance(value, set):
            return self.encode_set(value)
        elif isinstance(value, list):
            return self.encode_sequence(value)
        elif isinstance(value, datetime.datetime):
            return self.encode_datetime(value)  #
        elif isinstance(value, datetime.date):
            return self.encode_date(value)  #
        elif isinstance(value, datetime.time):
            return self.encode_time(value)  #
        elif isinstance(value, bool):
            if value:
                return self.grammar.true_keyword
            else:
                return self.grammar.false_keyword
        elif isinstance(value, (int, float)):
            return repr(value)
        else:
            return self.encode_string(value)  #

    def encode_setseq(self, values):
        return ', '.join([self.encode_value(v) for v in values])

    def encode_sequence(self, value) -> str:
        return '(' + self.encode_setseq(value) + ')'

    def encode_set(self, value) -> str:
        return '{' + self.encode_setseq(value) + '}'

    def encode_date(self, value: datetime.date) -> str:
        return f'{value:%Y-%m-%d}'

    @staticmethod
    def encode_time(value: datetime.time) -> str:
        s = f'{value:%H:%M}'

        if value.microsecond:
            s += f':{value:%S.%f}'
        elif value.second:
            s += f':{value:%S}'

        return s

    def encode_datetime(self, value: datetime.datetime) -> str:
        date = self.encode_date(value)
        time = self.encode_time(value)
        return date + 'T' + time

    def needs_quotes(self, s: str) -> bool:
        tok = Token(s, grammar=self.grammar, decoder=self.decoder)
        return not tok.is_unquoted_string()

    def encode_string(self, value):
        s = str(value)

        if(self.needs_quotes(s)
           or any(c in self.grammar.whitespace for c in s)):
            for q in self.grammar.quotes:
                if q not in s:
                    return q + s + q
            else:
                raise ValueError('All of the quote characters, '
                                 f'{self.grammar.quotes}, were in the '
                                 f'string ("s"), so it could not be quoted.')
        else:
            return s

    def encode_units(self, value):
        return (self.grammar.units_delimiters[0] +
                value +
                self.grammar.units_delimiters[1])


class ODLEncoder(PVLEncoder):

    def __init__(self, grammar=None, decoder=None,
                 indent=2, width=80, aggregation_end=True,
                 end_delimiter=False, newline='\r\n'):

        if grammar is None:
            grammar = ODLgrammar()

        if decoder is None:
            decoder = ODLDecoder(grammar)

        super().__init__(grammar, decoder, indent, width, aggregation_end,
                         end_delimiter, newline)

    def encode(self, module) -> str:
        '''ODL requires that there must be a spacing or format
           character after the END statement.
        '''
        s = super().encode(module)
        return s + self.newline

    @staticmethod
    def is_scalar(value) -> bool:
        '''Returns a boolean indicating whether the *value* object
           qualifies as an ODL 'scalar_value'.

           ODL defines a 'scalar-value' as a numeric_value, a
           date_time_string, a text_string_value, or a symbol_value.

           For Python, these correspond to the following:
               numeric_value: int, float,
                              and Units() whose value is int or float
               date_time_string: datetime objects
               text_string_value: str
               symbol_value: str
        '''
        if isinstance(value, Units):
            if isinstance(value.value, (int, float)):
                return True
        elif isinstance(value, (int, float, datetime.date, datetime.datetime,
                                datetime.time, str)):
            return True

        return False

    def is_symbol(self, value) -> bool:
        '''Tests whether *value* is an ODL Symbol String.

           An ODL Symbol String is enclosed by single quotes
           and may not contain any of the following characters:

           1. The apostrophe, which is reserved as the symbol string delimiter.
           2. ODL Format Effectors
           3. Control characters

           This means that an ODL Symbol String is a subset of the PVL
           quoted string, and will be represented in Python as a ``str``.
        '''
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

    def is_identifier(self, value):
        '''Tests whether *value* is an ODL Identifier.

           An ODL Identifier is compsed of letters, digits, and underscores.
           The first character must be a letter, and the last must not
           be an underscore.
        '''
        if isinstance(value, str):
            try:
                # Ensure we're dealing with ASCII
                value.encode(encoding='ascii')

                if(not value[0].isalpha()    # start with letter
                   or value.endswith('_')):  # can't end with '_'
                    return False

                for c in value:
                    if not (c.isalpha() or c.isdigit() or c == '_'):
                        return False
                else:
                    return True

            except UnicodeError:
                return False
        else:
            return False

        return False

    def needs_quotes(self, s: str) -> bool:
        return not self.is_identifier(s)

    def encode_assignment(self, key, value, level=0) -> str:

        if len(key) > 30:
            raise ValueError('ODL keywords must be 30 characters or less '
                             f'in length, this one is longer: {key}')

        ident = ''
        if((key.startswith('^') and self.is_identifier(key[1:]))
           or self.is_identifier(key)):
            ident = key.upper()
        else:
            raise ValueError('The keyword "{key}" is not a valid ODL '
                             'Identifier.')

        s = ''
        s += f'{ident} = '
        s += self.encode_value(value)

        if self.end_delimiter:
            s += self.grammar.delimiters[0]

        return self.format(s, level)

    def encode_sequence(self, value) -> str:
        '''ODL only allows one- and two-dimensional sequences
           of ODL scalar_values.
        '''
        if len(value) == 0:
            raise ValueError('ODL does not allow empty Sequences.')

        for v in value:  # check the first dimension (list of elements)
            if isinstance(v, list):
                for i in v:  # check the second dimension (list of lists)
                    if isinstance(i, list):
                        # Shouldn't be lists of lists of lists.
                        raise ValueError('ODL only allows one- and two- '
                                         'dimensional Sequences, but '
                                         f'this has more: {value}')
                    elif not self.is_scalar(i):
                        raise ValueError('ODL only allows scalar_values '
                                         f'within sequences: {v}')

            elif not self.is_scalar(v):
                raise ValueError('ODL only allows scalar_values within '
                                 f'sequences: {v}')

        return super().encode_sequence(value)

    def encode_set(self, values) -> str:
        '''ODL only allows sets to contain scalar values.
        '''

        if not all(map(self.is_scalar, values)):
            raise ValueError('The PDS only allows integers and symbols '
                             'in sets: {value}')

        return super().encode_set(values)

    def encode_value(self, value):
        if(isinstance(value, Units) and
           not isinstance(value.value, (int, float))):
            raise ValueError('Unit expressions are only allowed '
                             f'following numeric values: {value}')

        return super().encode_value(value)

    def encode_string(self, value):
        if self.is_identifier(value):
            return value
        elif self.is_symbol(value):
            return "'" + value + "'"
        else:
            return super().encode_string(value)

    def encode_time(self, value: datetime.time) -> str:
        '''ODL allows a time zone offset from UTC to be included,
           and otherwise recommends that times be suffixed with a 'Z'
           to clearly indicate that they are in UTC.
        '''

        t = super().encode_time(value)

        if value.tzinfo is None:
            return t + 'Z'
        else:
            delta = str(value.utcoffset())
            return t + delta

    def encode_units(self, value):

        if self.is_identifier(value.strip('*/()-')):

            if '**' in value:
                exponents = re.findall(r'\*\*.*?', value)
                for e in exponents:
                    if re.search(r'\*\*-?\d+', e) is None:
                        raise ValueError('The exponentiation operator (**) in '
                                         f'this Units Expression "{value}" '
                                         'is not a decimal integer.')

            return (self.grammar.units_delimiters[0] +
                    value +
                    self.grammar.units_delimiters[1])
        else:
            raise ValueError(f'The value, "{value}", does not conform to '
                             'the specification for an ODL Units Expression.')


class PDSLabelEncoder(ODLEncoder):

    def __init__(self, grammar=None, decoder=None,
                 indent=2, width=80,
                 aggregation_end=True,
                 convert_group_to_object=True,
                 tab_replace=4):
        '''In PVL and ODL, the OBJECT and GROUP aggregations are
           interchangable, but the PDS applies restrictions to what can
           appear in a GROUP.  If *convert_group_to_object* is True,
           and a GROUP does not conform to the PDS definition of a GROUP,
           then it will be written out as an OBJECT.  If it is False,
           then an exception will be thrown if incompatible GROUPs are
           encountered.

           *tab_replace* should indicate the number of space characters
           to replace horizontal tab characters with.  If this is set
           to zero, tabs will not be replaced with spaces.
        '''

        super().__init__(grammar, decoder, indent, width, aggregation_end,
                         end_delimiter=False, newline='\r\n')

        self.convert_group_to_object = convert_group_to_object
        self.tab_replace = tab_replace

    @staticmethod
    def count_aggs(module, obj_count=0, grp_count=0) -> tuple:
        '''Returns the count of OBJECT and GROUP aggregations
           that are contained within the *module* as a two-tuple.
        '''
        # This currently just counts the values in the passed
        # in module, it does not 'recurse' if those aggregations also
        # may contain aggregations.

        for k, v in module.items():
            if isinstance(v, PVLAggregation):
                if isinstance(v, PVLGroup):
                    grp_count += 1
                elif isinstance(v, PVLObject):
                    obj_count += 1
                else:
                    # There currently aren't any other kinds of Aggregations
                    pass

        return (obj_count, grp_count)

    def encode(self, module) -> str:
        '''For PDS, if there are any GROUP elements, there must be at
           least one OBJECT element in the label.
        '''
        (obj_count, grp_count) = self.count_aggs(module)

        if grp_count > 0:
            if obj_count < 1 and self.convert_group_to_object:
                for k, v in module.items():
                    # First try to convert any GROUPs that would not
                    # be valid PDS GROUPs.
                    if isinstance(v, PVLGroup) and not self.is_PDSgroup(v):
                        module[k] = PVLObject(v)
                        break
                else:
                    # Then just convert the first GROUP
                    for k, v in module.items():
                        if isinstance(v, PVLGroup):
                            module[k] = PVLObject(v)
                            break
                    else:
                        raise ValueError("Couldn't convert any of the GROUPs "
                                         "to OBJECTs.")
            else:
                raise ValueError('This module has a GROUP element, but no '
                                 'OBJECT elements, which is not allowed by '
                                 'the PDS.  You could set '
                                 '*convert_group_to_object* to *True* on the '
                                 'encoder to try and convert a GROUP'
                                 'to an OBJECT.')

        s = super().encode(module)
        if self.tab_replace > 0:
            return s.replace('\t', (' ' * self.tab_replace))
        else:
            return s

    def is_PDSgroup(self, group) -> bool:
        '''PDS applies the following restrictions to GROUPS:

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
        '''
        (obj_count, grp_count) = self.count_aggs(group)

        # Items 3 and 4:
        if obj_count != 0 or grp_count != 0:
            return False

        # Item 2, no data location pointers:
        for k, v in group.items():
            if k.startswith('^'):
                if isinstance(v, int):
                    return False
                elif isinstance(v, Units) and isinstance(v.value, int):
                    return False

        # Item 2, no repeated keys:
        keys = list(group.keys())
        if len(keys) != len(set(keys)):
            return False

        return True

    def encode_aggregation_block(self, key, value, level=0):
        '''PDS has restrictions on what may be in a GROUP.

           If the encoder's *convert_group_to_object* parameter is True,
           and a GROUP does not conform to the PDS definition of a GROUP,
           then it will be written out as an OBJECT.  If it is False,
           then an exception will be thrown.
        '''

        # print('value at top:')
        # print(value)

        if(isinstance(value, PVLGroup) and not self.is_PDSgroup(value)):
            if self.convert_group_to_object:
                value = PVLObject(value)
            else:
                raise ValueError('This GROUP element is not a valid PDS '
                                 'GROUP.  You could set '
                                 '*convert_group_to_object* to *True* on the '
                                 'encoder to try and convert the GROUP'
                                 'to an OBJECT.')

        # print('value at bottom:')
        # print(value)

        return super().encode_aggregation_block(key, value, level)

    def encode_set(self, values) -> str:
        '''PDS only allows symbol values and integers within sets.
        '''
        for v in values:
            if not self.is_symbol(v) and not isinstance(v, int):
                raise ValueError('The PDS only allows integers and symbols '
                                 'in sets: {value}')

        return super().encode_set(values)

    def encode_time(self, value: datetime.time) -> str:
        '''Not in the section on times, but at the end of the PDS
           ODL document, in section 12.7.3, para 14, it indicates that
           alternate time zones may not be used in a PDS label, only
           UTC.
        '''

        t = PVLEncoder.encode_time(value)

        if value.tzinfo is None or value.tzinfo.utcoffset(None) == 0:
            return t + 'Z'
        else:
            raise ValueError('PDS labels should only have UTC times, but '
                             f'this time has a timezone: {value}')
