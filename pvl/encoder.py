# -*- coding: utf-8 -*-
import six
from ._collections import LabelGroup, Units


class LabelEncoder(object):
    group = b'Group'
    end_group = b'End_Group'
    object = b'Object'
    end_object = b'End_Object'
    end_statement = b'End'
    null = b'NULL'
    true = b'TRUE'
    false = b'FALSE'
    assignment = b' = '
    indentation = b'  '
    newline = b'\n'

    def indent(self, level, stream):
        stream.write(level * self.indentation)

    def encode(self, label, stream):
        self.encode_block(label, 0, stream)
        stream.write(self.end_statement)

    def encode_block(self, block, level, stream):
        for key, value in six.iteritems(block):
            self.encode_statement(key, value, level, stream)

    def encode_statement(self, key, value, level, stream):
        if isinstance(value, LabelGroup):
            return self.encode_group(key, value, level, stream)

        if isinstance(value, dict):
            return self.encode_object(key, value, level, stream)

        self.encode_assignment(key, value, level, stream)

    def encode_group(self, key, value, level, stream):
        # Group begin
        self.indent(level, stream)
        stream.write(self.group)
        stream.write(self.assignment)
        stream.write(key.encode('utf-8'))
        stream.write(self.newline)

        # Body
        self.encode_block(value, level + 1, stream)

        # Group end
        self.indent(level, stream)
        stream.write(self.end_group)
        stream.write(self.newline)

    def encode_object(self, key, value, level, stream):
        # Object begin
        self.indent(level, stream)
        stream.write(self.object)
        stream.write(self.assignment)
        stream.write(key.encode('utf-8'))
        stream.write(self.newline)

        # Body
        self.encode_block(value, level + 1, stream)

        # Object end
        self.indent(level, stream)
        stream.write(self.end_object)
        stream.write(self.newline)

    def encode_assignment(self, key, value, level, stream):
        self.indent(level, stream)
        stream.write(key.encode('utf-8'))
        stream.write(self.assignment)
        stream.write(self.encode_value(value))
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

        if isinstance(value, (int, float)):
            return self.encode_number(value)

        if value is None:
            return self.encode_null(value)

        if isinstance(value, bool):
            return self.encode_bool(value)

        if isinstance(value, list):
            return self.encode_list(value)

        if isinstance(value, set):
            return self.encode_set(value)

        return self.default(value)

    def encode_units(self, value):
        return b'<' + value.encode('utf-8') + b'>'

    def encode_null(self, value):
        return self.null

    def encode_number(self, value):
        return str(value).encode('utf-8')

    def encode_string(self, value):
        if value.isalpha():
            return value.encode('utf-8')
        return repr(value.encode('utf-8'))

    def encode_bool(self, value):
        if value:
            return self.true
        return self.false

    def encode_sequence(self, values):
        return b', '.join([self.encode_value(v) for v in values])

    def encode_list(self, value):
        return b'(' + self.encode_sequence(value) + b')'

    def encode_set(self, value):
        return b'{' + self.encode_sequence(value) + b'}'

    def default(self, value):
        raise TypeError(repr(value) + " is not serializable")


class PDSLabelEncoder(LabelEncoder):
    group = b'GROUP'
    end_group = b'END'
    object = b'OBJECT'
    end_object = b'END'
    end_statement = b'END'
