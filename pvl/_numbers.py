# -*- coding: utf-8 -*-
from six import b
import re


RE_FRAGMENTS = {
    'int': r'(?:[-+]?[0-9]+)',
    'float': r'(?:[-+]?(?:[0-9]+\.[0-9]*|[0-9]*\.[0-9]+))',
}

INTEGER = r'^%(int)s$' % RE_FRAGMENTS
FLOAT = r'^%(float)s$' % RE_FRAGMENTS
EXPONENT = r'(?:%(int)s|%(float)s)(?:e|E)(?:%(int)s)' % RE_FRAGMENTS

INTEGER_RE = re.compile(b(INTEGER))
FLOAT_RE = re.compile(b(FLOAT))
EXPONENT_RE = re.compile(b(EXPONENT))


def is_integer(value):
    return bool(INTEGER_RE.match(value))


def is_float(value):
    return bool(FLOAT_RE.match(value))


def is_exponent(value):
    return bool(EXPONENT_RE.match(value))


def is_number(value):
    return is_integer(value) or is_float(value) or is_exponent(value)


def parse_number(value):
    if is_integer(value):
        return int(value, 10)

    if is_float(value) or is_exponent(value):
        return float(value)

    raise ValueError('not a number')
