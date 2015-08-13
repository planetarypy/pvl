# -*- coding: utf-8 -*-
import datetime
import six
from ._collections import PVLGroup, Units
from ._strings import needs_quotes, quote_string


class PVLEncoder(object):
    begin_group = b'BEGIN_GROUP'
    end_group = b'END_GROUP'
    begin_object = b'BEGIN_OBJECT'
    end_object = b'END_OBJECT'
    end_statement = b'END'
    null = b'NULL'
    true = b'TRUE'
    false = b'FALSE'
    assignment = b' = '
    indentation = b'  '
    newline = b'\r\n'

    def indent(self, level, stream):
        stream.write(level * self.indentation)

    def encode(self, module, stream):
        self.encode_block(module, 0, stream)
        stream.write(self.end_statement)

    def encode_block(self, block, level, stream):
        for key, value in six.iteritems(block):
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
            value=key.encode('utf-8'),
            level=level,
            stream=stream
        )

    def encode_group_end(self, key, value, level, stream):
        self.encode_raw_assignment(
            key=self.end_group,
            value=key.encode('utf-8'),
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
            value=key.encode('utf-8'),
            level=level,
            stream=stream
        )

    def encode_object_end(self, key, value, level, stream):
        self.encode_raw_assignment(
            key=self.end_object,
            value=key.encode('utf-8'),
            level=level,
            stream=stream
        )

    def encode_assignment(self, key, value, level, stream):
        self.encode_raw_assignment(
            key=key.encode('utf-8'),
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
            return value + b' ' + units
        return self.encode_simple_value(value)

    def encode_simple_value(self, value):
        if isinstance(value, six.string_types):
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
        return b'<' + value.encode('utf-8') + b'>'

    def encode_null(self, value):
        return self.null

    def encode_number(self, value):
        return repr(value).encode('utf-8')

    def encode_string(self, value):
        value = value.encode('utf-8')
        if needs_quotes(value):
            return quote_string(value)
        return value

    def encode_bool(self, value):
        if value:
            return self.true
        return self.false

    def encode_date(self, value):
        date = u'%04d-%02d-%02d' % (value.year, value.month, value.day)
        return date.encode('utf-8')

    def encode_tz(self, offset):
        hours = int(offset.seconds / 3600) + (offset.days * 24)
        return u'%+d' % hours

    def encode_time(self, value):
        if value.microsecond:
            second = u'%02d.%06d' % (value.second, value.microsecond)
        else:
            second = u'%02d' % value.second

        if value.utcoffset() is not None:
            second += self.encode_tz(value.utcoffset())

        time = u'%02d:%02d:%s' % (value.hour, value.minute, second)
        return time.encode('utf-8')

    def encode_datetime(self, value):
        date = self.encode_date(value)
        time = self.encode_time(value)
        return date + b'T' + time

    def encode_sequence(self, values):
        return b', '.join([self.encode_value(v) for v in values])

    def encode_list(self, value):
        return b'(' + self.encode_sequence(value) + b')'

    def encode_set(self, value):
        return b'{' + self.encode_sequence(value) + b'}'

    def default(self, value):
        raise TypeError(repr(value) + " is not serializable")


class IsisCubeLabelEncoder(PVLEncoder):
    begin_group = b'Group'
    end_group = b'End_Group'
    begin_object = b'Object'
    end_object = b'End_Object'
    end_statement = b'End'

    def encode_group_end(self, key, value, level, stream):
        self.indent(level, stream)
        stream.write(self.end_group)
        stream.write(self.newline)

    def encode_object_end(self, key, value, level, stream):
        self.indent(level, stream)
        stream.write(self.end_object)
        stream.write(self.newline)


class PDSLabelEncoder(PVLEncoder):
    begin_group = b'GROUP'
    begin_object = b'OBJECT'

    def _detect_assignment_col(self, block, indent=0):
        if not block:
            return 0
        block_items = six.iteritems(block)
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
