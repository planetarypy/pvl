# -*- coding: utf-8 -*-
import io
import six

from .decoder import LabelDecoder
from .encoder import LabelEncoder
from ._collections import (
    Label,
    LabelGroup,
    LabelObject,
    Units,
)

__author__ = 'Trevor Olson'
__email__ = 'trevor@heytrevor.com'
__version__ = '0.1.0'
__all__ = [
    'load',
    'loads',
    'dump',
    'dumps',
    'Label',
    'LabelGroup',
    'LabelObject',
    'Units',
]


def load(stream):
    """Parse an isis label from a stream.

    :param stream: a ``.read()``-supporting file-like object containing a label.
        if ``stream`` is a string it will be treated as a filename
    """
    if isinstance(stream, six.string_types):
        with open(stream, 'rb') as fp:
            return LabelDecoder().decode(fp)
    return LabelDecoder().decode(stream)


def loads(data, encoding='utf-8'):
    """Parse an isis label from a string.

    :param data: an isis label as a string

    :returns: a dictionary representation of the given isis label
    """
    if not isinstance(data, bytes):
        data = data.encode(encoding)
    return LabelDecoder().decode(data)


def dump(label, stream):
    LabelEncoder().encode(label, stream)


def dumps(label):
    stream = io.BytesIO()
    LabelEncoder().encode(label, stream)
    return stream.getvalue()
