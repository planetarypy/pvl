# -*- coding: utf-8 -*-
from six import b
import re

from ._datetimes import is_date_or_time
from ._numbers import is_number


QUOTE = b'"'
ALT_QUOTE = b"'"

LINE_CONTINUATION_RE = re.compile(b(r'-(?:\r\n|\n|\r)[ \t\v\f]*'))
FORMATTING_CHARS = [
    (b'\n', b'\\n'),
    (b'\t', b'\\t'),
    (b'\f', b'\\f'),
    (b'\v', b'\\v'),
    (b'\\', b'\\\\'),
]

RESTRICTED_SEQ = [
    b'/*', b'*/',  # Comments
]

RESTRICTED_CHARS = set([
    b' ', b'\r', b'\n', b'\t', b'\v', b'\f',  # Whitespace
    b'&', b'<', b'>', b'\'', b'{', b'}', b',', b'[', b']', b'=', b'!', b'#',
    b'(', b')', b'%', b'"', b';', b'|',  # Restricted chars
])

RESERVED_KEYWORDS = set([
    b'Null', b'NULL',
    b'End', b'END',
    b'TRUE', b'True', b'true',
    b'FALSE', b'False', b'false',
    b'Group', b'GROUP', b'BEGIN_GROUP',
    b'End_Group', b'END_GROUP',
    b'Object', b'OBJECT', b'BEGIN_OBJECT',
    b'End_Object', b'END_OBJECT',
    b'End', 'END',
])


def escape_quote(quote, value):
    return quote + value.replace(quote, b'\\' + quote) + quote


def unquote_string(value, encoding='utf-8'):
    value = LINE_CONTINUATION_RE.sub(b'', value)
    value = b' '.join(value.split()).strip()

    for char, escape in FORMATTING_CHARS:
        value = value.replace(escape, char)

    return value.decode(encoding)


def quote_string(value, encoding='utf-8'):
    value = value.encode(encoding)

    for char, escape in reversed(FORMATTING_CHARS):
        value = value.replace(char, escape)

    if QUOTE in value and ALT_QUOTE not in value:
        return escape_quote(ALT_QUOTE, value)

    return escape_quote(QUOTE, value)


def needs_quotes(value):
    if is_number(value):
        return True

    if is_date_or_time(value):
        return True

    if value in RESERVED_KEYWORDS:
        return True

    for char in value:
        if char in RESTRICTED_CHARS:
            return True

    for seq in RESTRICTED_SEQ:
        if seq in value:
            return True

    return False
