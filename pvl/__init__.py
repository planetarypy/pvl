# -*- coding: utf-8 -*-
import io
import six

from .decoder import PVLDecoder
from .encoder import PVLEncoder
from ._collections import (
    PVLModule,
    PVLGroup,
    PVLObject,
    Units,
)

__author__ = 'The PlanetaryPy Developers'
__email__ = 'trevor@heytrevor.com'
__version__ = '0.1.0'
__all__ = [
    'load',
    'loads',
    'dump',
    'dumps',
    'PVLModule',
    'PVLGroup',
    'PVLObject',
    'Units',
]


def load(stream, cls=PVLDecoder, **kwargs):
    """Parse an pvl module from a stream.

    :param stream: a ``.read()``-supporting file-like object containing a
        module. if ``stream`` is a string it will be treated as a filename
    """
    if isinstance(stream, six.string_types):
        with open(stream, 'rb') as fp:
            return cls(**kwargs).decode(fp)
    return cls(**kwargs).decode(stream)


def loads(data, encoding='utf-8', cls=PVLDecoder, **kwargs):
    """Parse an pvl module from a string.

    :param data: an pvl module as a string

    :returns: a dictionary representation of the given pvl module
    """
    if not isinstance(data, bytes):
        data = data.encode(encoding)
    return cls(**kwargs).decode(data)


def dump(module, stream, cls=PVLEncoder, **kwargs):
    if isinstance(stream, six.string_types):
        with open(stream, 'wb') as fp:
            return cls(**kwargs).encode(module, fp)
    cls(**kwargs).encode(module, stream)


def dumps(module, cls=PVLEncoder, **kwargs):
    stream = io.BytesIO()
    cls(**kwargs).encode(module, stream)
    return stream.getvalue()


# Depreciated aliases
# TODO: add warnings for these?
Label = PVLModule
LabelGroup = PVLGroup
LabelObject = PVLObject
LabelEncoder = PVLEncoder
LabelDecoder = PVLEncoder
