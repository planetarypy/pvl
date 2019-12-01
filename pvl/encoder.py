# -*- coding: utf-8 -*-
import datetime
from ._collections import PVLGroup, Units
from ._strings import needs_quotes, quote_string


class PVLEncoder(object):
    begin_group = 'BEGIN_GROUP'
    end_group = 'END_GROUP'
    begin_object = 'BEGIN_OBJECT'
    end_object = 'END_OBJECT'
    end_statement = 'END'
    null = 'NULL'
    true = 'TRUE'
    false = 'FALSE'
    assignment = ' = '
    indentation = '  '
    newline = '\r\n'

    def indent(self, level, stream):
        stream.write(level * self.indentation)

    def encode(self, module, stream):
        self.encode_block(module, 0, stream)
        stream.write(self.end_statement)

    def encode_block(self, block, level, stream):
        for key, value in block.items():
            self.encode_statement(key, value, level, stream)

    def encode_statement(self, key, value, level, stream):
        if isinstance(value, PVLGroup):
            return self.encode_group(key, value, level, stream)

        if isinstance(value, dict):
            return self.encode_object(key, value, level, stream)

        self.encode_assignment(key, value, level, stream)

    def encode_group(self, key, value, level, stream):
        self.encode_group_begin(key, value, level, stream)
        self.encode_block(value, level + 1, stream)
        self.encode_group_end(key, value, level, stream)

    def encode_group_begin(self, key, value, level, stream):
        self.encode_raw_assignment(
            key=self.begin_group,
            value=key,
            level=level,
            stream=stream
        )

    def encode_group_end(self, key, value, level, stream):
        self.encode_raw_assignment(
            key=self.end_group,
            value=key,
            level=level,
            stream=stream
        )

    def encode_object(self, key, value, level, stream):
        self.encode_object_begin(key, value, level, stream)
        self.encode_block(value, level + 1, stream)
        self.encode_object_end(key, value, level, stream)

    def encode_object_begin(self, key, value, level, stream):
        self.encode_raw_assignment(
            key=self.begin_object,
            value=key,
            level=level,
            stream=stream
        )

    def encode_object_end(self, key, value, level, stream):
        self.encode_raw_assignment(
            key=self.end_object,
            value=key,
            level=level,
            stream=stream
        )

    def encode_assignment(self, key, value, level, stream):
        self.encode_raw_assignment(
            key=key,
            value=self.encode_value(value),
            level=level,
            stream=stream
        )

    def encode_raw_assignment(self, key, value, level, stream):
        self.indent(level, stream)
        stream.write(key)
        stream.write(self.assignment)
        stream.write(value)
        stream.write(self.newline)

    def encode_value(self, value):
        if isinstance(value, Units):
            units = self.encode_units(value.units)
            value = self.encode_simple_value(value.value)
            return value + ' ' + units
        return self.encode_simple_value(value)

    def encode_simple_value(self, value):
        if isinstance(value, str):
            return self.encode_string(value)

        if value is None:
            return self.encode_null(value)

        if isinstance(value, bool):
            return self.encode_bool(value)

        if isinstance(value, (int, float)):
            return self.encode_number(value)

        if isinstance(value, list):
            return self.encode_list(value)

        if isinstance(value, set):
            return self.encode_set(value)

        if isinstance(value, datetime.datetime):
            return self.encode_datetime(value)

        if isinstance(value, datetime.date):
            return self.encode_date(value)

        if isinstance(value, datetime.time):
            return self.encode_time(value)

        return self.default(value)

    def encode_units(self, value):
        return '<' + value + '>'

    def encode_null(self, value):
        return self.null

    def encode_number(self, value):
        return repr(value)

    def encode_string(self, value):
        value = value
        if needs_quotes(value):
            return quote_string(value)
        return value

    def encode_bool(self, value):
        if value:
            return self.true
        return self.false

    def encode_date(self, value: datetime.date) -> str:
        date = f'{value:%Y-%m-%d}'
        return date

    def encode_tz(self, offset: datetime.timedelta) -> str:
        hours = int(offset.seconds / 3600) + (offset.days * 24)
        return f'{hours:0>+2d}'

    def encode_time(self, value: datetime.time):
        if value.microsecond:
            second = u'%02d.%06d' % (value.second, value.microsecond)
            second = f'{value:%S.%f}'
        else:
            second = u'%02d' % value.second
            second = f'{value:%S}'

        time = f'{value:%H:%M}:{second}'

        if value.utcoffset() is not None:
            time += self.encode_tz(value.utcoffset())

        return time

    def encode_datetime(self, value: datetime.datetime) -> str:
        date = self.encode_date(value)
        time = self.encode_time(value)
        return date + 'T' + time

    def encode_sequence(self, values):
        return ', '.join([self.encode_value(v) for v in values])

    def encode_list(self, value):
        return '(' + self.encode_sequence(value) + ')'

    def encode_set(self, value):
        return '{' + self.encode_sequence(value) + '}'

    def default(self, value):
        raise TypeError(repr(value) + " is not serializable")


class IsisCubeLabelEncoder(PVLEncoder):
    begin_group = 'Group'
    end_group = 'End_Group'
    begin_object = 'Object'
    end_object = 'End_Object'
    end_statement = 'End'

    def encode_group_end(self, key, value, level, stream):
        self.indent(level, stream)
        stream.write(self.end_group)
        stream.write(self.newline)

    def encode_object_end(self, key, value, level, stream):
        self.indent(level, stream)
        stream.write(self.end_object)
        stream.write(self.newline)


class PDSLabelEncoder(PVLEncoder):
    begin_group = 'GROUP'
    begin_object = 'OBJECT'

    def _detect_assignment_col(self, block, indent=0):
        if not block:
            return 0
        block_items = block.items()
        return max(self._key_length(k, v, indent) for k, v in block_items)

    def _key_length(self, key, value, indent):
        length = indent + len(key)

        if isinstance(value, dict):
            indent += len(self.indentation)
            return max(length, self._detect_assignment_col(value, indent))

        return length

    def encode(self, module, stream):
        self.assignment_col = self._detect_assignment_col(module)
        super(PDSLabelEncoder, self).encode(module, stream)

    def encode_raw_assignment(self, key, value, level, stream):
        indented_key = (level * self.indentation) + key
        stream.write(indented_key.ljust(self.assignment_col))
        stream.write(self.assignment)
        stream.write(value)
        stream.write(self.newline)
