# -*- coding: utf-8 -*-
"""Python implementation of PVL (Parameter Value Language).

PVL is a markup language, similar to xml, commonly employed for entries in the
Planetary Database System used by NASA to store mission data, among other uses.
This package supports both encoding a decoding a superset of PVL, including the
USGS Isis Cube Label and NASA PDS 3 Label dialects.

Basic Usage
-----------

Decoding pvl modules::

    >>> import pvl
    >>> module = pvl.loads('''
    ...   foo = bar
    ...   items = (1, 2, 3)
    ...   END
    ... ''')
    >>> print module
    PVLModule([
      (u'foo', u'bar')
      (u'items', [1, 2, 3])
    ])
    >>> print module['foo']
    bar

Encoding pvl modules::

    >>> import pvl
    >>> print pvl.dumps({
    ...   'foo': 'bar',
    ...   'items': [1, 2, 3]
    ... })
    items = (1, 2, 3)
    foo = bar
    END

Building pvl modules::

    >>> import pvl
    >>> module = pvl.PVLModule({'foo': 'bar'})
    >>> module.append('items', [1, 2, 3])
    >>> print pvl.dumps(module)
    foo = bar
    items = (1, 2, 3)
    END
"""
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
__version__ = '0.2.0'
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


def __create_decoder(cls, strict, **kwargs):
    decoder = cls(**kwargs)
    decoder.set_strict(strict)
    return decoder


def load(stream, cls=PVLDecoder, strict=True, **kwargs):
    """Deserialize ``stream`` as a pvl module.

    :param stream: a ``.read()``-supporting file-like object containing a
        module. If ``stream`` is a string it will be treated as a filename

    :param cls: the decoder class used to deserialize the pvl module. You may
        use the default ``PVLDecoder`` class or provide a custom sublcass.

    :param **kwargs: the keyword arguments to pass to the decoder class.
    """
    decoder = __create_decoder(cls, strict, **kwargs)
    if isinstance(stream, six.string_types):
        with open(stream, 'rb') as fp:
            return decoder.decode(fp)
    return decoder.decode(stream)


def loads(data, cls=PVLDecoder, strict=True, **kwargs):
    """Deserialize ``data`` as a pvl module.

    :param data: a pvl module as a byte or unicode string

    :param cls: the decoder class used to deserialize the pvl module. You may
        use the default ``PVLDecoder`` class or provide a custom sublcass.

    :param **kwargs: the keyword arguments to pass to the decoder class.
    """
    decoder = __create_decoder(cls, strict, **kwargs)
    if not isinstance(data, bytes):
        data = data.encode('utf-8')
    return decoder.decode(data)


def dump(module, stream, cls=PVLEncoder, **kwargs):
    """Serialize ``module`` as a pvl module to the provided ``stream``.

    :param module: a ```PVLModule``` or ```dict``` like object to serialize

    :param stream: a ``.write()``-supporting file-like object to serialize the
        module to. If ``stream`` is a string it will be treated as a filename

    :param cls: the encoder class used to serialize the pvl module. You may use
        the default ``PVLEncoder`` class or provided encoder formats such as the
        ```IsisCubeLabelEncoder``` and ```PDSLabelEncoder``` classes. You may
        also provided a custom sublcass of ```PVLEncoder```

    :param **kwargs: the keyword arguments to pass to the encoder class.
    """
    if isinstance(stream, six.string_types):
        with open(stream, 'wb') as fp:
            return cls(**kwargs).encode(module, fp)
    cls(**kwargs).encode(module, stream)


def dumps(module, cls=PVLEncoder, **kwargs):
    """Serialize ``module`` as a pvl module formated byte string.

    :param module: a ```PVLModule``` or ```dict``` like object to serialize

    :param cls: the encoder class used to serialize the pvl module. You may use
        the default ``PVLEncoder`` class or provided encoder formats such as the
        ```IsisCubeLabelEncoder``` and ```PDSLabelEncoder``` classes. You may
        also provided a custom sublcass of ```PVLEncoder```

    :param **kwargs: the keyword arguments to pass to the encoder class.

    :returns: a byte string encoding of the pvl module
    """
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
