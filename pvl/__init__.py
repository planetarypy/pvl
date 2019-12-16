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
from pathlib import Path

from .encoder import PVLEncoder
from ._collections import (
    PVLModule,
    PVLGroup,
    PVLObject,
    Units,
)

from .parser import PVLParser as Parser

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


# def __create_decoder(cls, strict, **kwargs):
#     decoder = cls(**kwargs)
#     decoder.set_strict(strict)
#     return decoder


def load(path, **kwargs):
    """Takes an os.PathLike *path* which presumably has a PVL Module
       in it, and deserializes it to a Python object.

       If *path* is not an os.PathLike, it will be assumed to be an
       already-opened file object, and ``.read()`` will be applied
       to extract the text.

       If the os.PathLike or file object contains some bytes decodable as
       text, followed by some that is not (e.g. an ISIS cube file), that's
       fine, this function will just extract the decodable text.

       :param **kwargs: all other arguments will be passed to the
        loads() function and are described there.
    """
    try:
        try:
            p = Path(path)
            return loads(p.read_text(), **kwargs)
        except TypeError:
            # Not an os.PathLike, maybe it is an already-opened file object
            return loads(path.read(), **kwargs)
    except UnicodeDecodeError:
        # This may be the result of an ISIS cube file (or anything else)
        # where the first set of bytes might be decodable, but once the
        # image data starts, they won't be, and the above tidy functions
        # fail.  So open the file as a bytestream, and read until
        # we can't decode.  We don't want to just run the .read_bytes()
        # method of Path, because this could be a giant file.
        try:
            with open(p, mode='rb') as f:
                s = decode_bytes(f)
        except TypeError:
            s = decode_bytes(path)

        return loads(s, **kwargs)


def decode_bytes(f: io.RawIOBase) -> str:
    """Deserialize ``f`` which is expected to be a file object which
       has been opened in binary mode.

       The ``f`` stream will have one byte at a time read from it,
       and will attempt to decode each byte to a string and accumulate
       those individual strings together.  Once the end of the file is found
       or a byte can no longer be decoded, the accumulated string will
       be returned.
    """
    s = ''
    try:
        for byte in iter(lambda: f.read(1), b''):
            s += byte.decode()
    except UnicodeError:
        # Expecting this to mean that we got to the end of decodable
        # bytes, so we're all done, and pass through to return s.
        pass

    return s


def loads(s: str, parser=None, grammar=None, decoder=None, modcls=PVLModule,
          grpcls=PVLGroup, objcls=PVLObject, strict=False, **kwargs):
    """Deserialize the string, ``s``, as a pvl module.

    :param data: a pvl module as a string

    :param cls: the decoder class used to deserialize the pvl module. You may
        use the default ``PVLDecoder`` class or provide a custom sublcass.

    :param **kwargs: the keyword arguments to pass to the decoder class.
    """
    # decoder = __create_decoder(cls, strict, grammar=grammar, **kwargs)
    # return decoder.decode(s)

    if parser is None:
        parser = Parser(grammar=grammar, decoder=decoder,
                        module_class=modcls,
                        group_class=grpcls,
                        object_class=objcls,
                        strict=strict)
    elif not isinstance(parser, Parser):
        raise TypeError('The parser must be an instance of pvl.PVLParser.')

    return parser.parse(s)


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
    if isinstance(stream, str):
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
