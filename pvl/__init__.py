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

from .encoder import PVLEncoder, PDSLabelEncoder
from ._collections import (
    PVLModule,
    PVLGroup,
    PVLObject,
    Units,
)

from .parser import PVLParser, OmniParser

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
        except UnicodeDecodeError:
            # This may be the result of an ISIS cube file (or anything else)
            # where the first set of bytes might be decodable, but once the
            # image data starts, they won't be, and the above tidy function
            # fails.  So open the file as a bytestream, and read until
            # we can't decode.  We don't want to just run the .read_bytes()
            # method of Path, because this could be a giant file.
            with open(p, mode='rb') as f:
                s = decode_bytes(f)
                return loads(s, **kwargs)

    except TypeError:
        # Not an os.PathLike, maybe it is an already-opened file object
        if path.readable():
            try:
                position = path.tell()
                return loads(path.read(), **kwargs)
            except UnicodeDecodeError:
                # All of the bytes weren't decodeable, maybe the initial
                # sequence is (as above)?
                path.seek(position)  # Reset after the previous .read():
                s = decode_bytes(path)
                return loads(s, **kwargs)
        else:
            # Not a path, not an already-opened file.
            raise TypeError('Expected an os.PathLike or an already-opened '
                            'file object, but did not get either.')


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
          grpcls=PVLGroup, objcls=PVLObject, **kwargs):
    """Deserialize the string, ``s``, as a pvl module.

    :param data: a pvl module as a string

    :param cls: the decoder class used to deserialize the pvl module. You may
        use the default ``PVLDecoder`` class or provide a custom sublcass.

    :param **kwargs: the keyword arguments to pass to the decoder class.
    """
    # decoder = __create_decoder(cls, strict, grammar=grammar, **kwargs)
    # return decoder.decode(s)

    if isinstance(s, bytes):
        # Someone passed us an old-style bytes sequence.  Although it isn't
        # a string, we can deal with it:
        s = s.decode()

    if parser is None:
        parser = OmniParser(grammar=grammar, decoder=decoder,
                            module_class=modcls,
                            group_class=grpcls,
                            object_class=objcls)
    elif not isinstance(parser, PVLParser):
        raise TypeError('The parser must be an instance of pvl.PVLParser.')

    return parser.parse(s)


def dump(module, path, **kwargs):
    """Serialize *module* as a pvl module to the provided *path*.

    If *path* is an os.PathLike, it will attempt to be opened and
    the serialized module will be written into that file via
    the pathlib.Path.write_text() function.

    If *path* is not an os.PathLike, it will be assumed to be an
    already-opened file object, and ``.write()`` will be applied
    on that object to write the serialized module.

    :param module: a ``PVLModule`` or ``dict``-like object to serialize

    :param **kwargs: the keyword arguments to pass to the dumps() function.
    """
    try:
        p = Path(path)
        return p.write_text(dumps(module, **kwargs))

    except TypeError:
        # Not an os.PathLike, maybe it is an already-opened file object
        try:
            if isinstance(path, io.TextIOBase):
                return path.write(dumps(module, **kwargs))
            else:
                return path.write(dumps(module, **kwargs).encode())
        except AttributeError:
            # Not a path, not an already-opened file.
            raise TypeError('Expected an os.PathLike or an already-opened '
                            'file object for writing, but got neither.')


def dumps(module, cls=PDSLabelEncoder, **kwargs):
    """Serialize ``module`` as a pvl module formated string.

    :param module: a ```PVLModule``` or ```dict``` like object to serialize

    :param cls: the encoder class used to serialize the pvl module. You may
        use the default ``PDSLabelEncoder`` class, provided encoder formats
        such as the ```PVLEncoder``` and ```ODLEncoder``` classes. You may
        also provide a custom sublcass of ```PVLEncoder```.

    :param **kwargs: the keyword arguments to pass to the encoder class.

    :returns: a byte string encoding of the pvl module
    """
    encoder = cls(**kwargs)
    return encoder.encode(module)


# Depreciated aliases
# TODO: add warnings for these?
Label = PVLModule
LabelGroup = PVLGroup
LabelObject = PVLObject
LabelEncoder = PVLEncoder
LabelDecoder = PVLEncoder
