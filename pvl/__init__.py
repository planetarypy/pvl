# -*- coding: utf-8 -*-
"""Python implementation of PVL (Parameter Value Language)."""

# Copyright 2015, 2017, 2019-2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import inspect
import io
import urllib.request
from pathlib import Path

from .encoder import PDSLabelEncoder, PVLEncoder
from .parser import PVLParser, OmniParser
from .collections import (
    PVLModule,
    PVLGroup,
    PVLObject,
    Quantity,
    Units,
)

__author__ = "The pvl Developers"
__email__ = "rbeyer@rossbeyer.net"
__version__ = "1.1.0"
__all__ = [
    "load",
    "loads",
    "dump",
    "dumps",
    "PVLModule",
    "PVLGroup",
    "PVLObject",
    "Quantity",
    "Units",
]


def load(path, parser=None, grammar=None, decoder=None, **kwargs):
    """Returns a Python object from parsing the file at *path*.

    :param path: an :class:`os.PathLike` which presumably has a
        PVL Module in it to parse.
    :param parser: defaults to :class:`pvl.parser.OmniParser()`.
    :param grammar: defaults to :class:`pvl.grammar.OmniGrammar()`.
    :param decoder: defaults to :class:`pvl.decoder.OmniDecoder()`.
    :param ``**kwargs``: the keyword arguments that will be passed
        to :func:`loads()` and are described there.

    If *path* is not an :class:`os.PathLike`, it will be assumed to be an
    already-opened file object, and ``.read()`` will be applied
    to extract the text.

    If the :class:`os.PathLike` or file object contains some bytes
    decodable as text, followed by some that is not (e.g. an ISIS
    cube file), that's fine, this function will just extract the
    decodable text.
    """
    return loads(
        get_text_from(path),
        parser=parser,
        grammar=grammar,
        decoder=decoder,
        **kwargs
    )


def get_text_from(path) -> str:
    try:
        p = Path(path)
        return p.read_text()
    except UnicodeDecodeError:
        # This may be the result of an ISIS cube file (or anything else)
        # where the first set of bytes might be decodable, but once the
        # image data starts, they won't be, and the above tidy function
        # fails.  So open the file as a bytestream, and read until
        # we can't decode.  We don't want to just run the .read_bytes()
        # method of Path, because this could be a giant file.
        with open(path, mode="rb") as f:
            return decode_by_char(f)
    except TypeError:
        # Not an os.PathLike, maybe it is an already-opened file object
        if path.readable():
            position = path.tell()
            try:
                s = path.read()
                if isinstance(s, bytes):
                    # Oh, it was opened in 'b' mode, need to rewind and
                    # decode.  Since the 'catch' below already does that,
                    # we'll just emit a ... contrived ... UnicodeDecodeError
                    # so we don't have to double-write the code:
                    raise UnicodeDecodeError(
                        "utf_8",
                        "dummy".encode(),
                        0,
                        1,
                        "file object in byte mode",
                    )
            except UnicodeDecodeError:
                # All of the bytes weren't decodeable, maybe the initial
                # sequence is (as above)?
                path.seek(position)  # Reset after the previous .read():
                s = decode_by_char(path)

        else:
            # Not a path, not an already-opened file.
            raise TypeError(
                "Expected an os.PathLike or an already-opened "
                "file object, but did not get either."
            )
        return s


def decode_by_char(f: io.RawIOBase) -> str:
    """Returns a ``str`` decoded from the characters in *f*.

    :param f: is expected to be a file object which has been
        opened in binary mode ('rb') or just read mode ('r').

    The *f* stream will have one character or byte at a time read from it,
    and will attempt to decode each to a string and accumulate
    those individual strings together.  Once the end of the file is found
    or an element can no longer be decoded, the accumulated string will
    be returned.
    """
    s = ""
    try:
        for elem in iter(lambda: f.read(1), b""):
            if isinstance(elem, str):
                s += elem
            else:
                s += elem.decode()
    except UnicodeError:
        # Expecting this to mean that we got to the end of decodable
        # bytes, so we're all done, and pass through to return s.
        pass

    return s


def loadu(url, parser=None, grammar=None, decoder=None, **kwargs):
    """Returns a Python object from parsing *url*.

        :param url: this will be passed to :func:`urllib.request.urlopen`
            and can be a string or a :class:`urllib.request.Request` object.
        :param parser: defaults to :class:`pvl.parser.OmniParser()`.
        :param grammar: defaults to :class:`pvl.grammar.OmniGrammar()`.
        :param decoder: defaults to :class:`pvl.decoder.OmniDecoder()`.
        :param ``**kwargs``: the keyword arguments that will be passed
            to :func:`urllib.request.urlopen` and to :func:`loads()`.

        The ``**kwargs`` will first be scanned for arguments that
        can be given to :func:`urllib.request.urlopen`.  If any are
        found, they are extracted and used.  All remaining elements
        will be passed on as keyword arguments to :func:`loads()`.

        Note that *url* can be any URL that :func:`urllib.request.urlopen`
        takes.  Certainly http and https URLs, but also file, ftp, rsync,
        sftp and more!
        """

    # Peel off the args for urlopen:
    url_args = dict()
    for a in inspect.signature(urllib.request.urlopen).parameters.keys():
        if a in kwargs:
            url_args[a] = kwargs.pop(a)

    # The object returned from urlopen will always have a .read()
    # function that returns bytes, so:
    with urllib.request.urlopen(url, **url_args) as resp:
        s = decode_by_char(resp)

    return loads(s, parser=parser, grammar=grammar, decoder=decoder, **kwargs)


def loads(s: str, parser=None, grammar=None, decoder=None, **kwargs):
    """Deserialize the string, *s*, as a Python object.

    :param s: contains some PVL to parse.
    :param parser: defaults to :class:`pvl.parser.OmniParser()`.
    :param grammar: defaults to :class:`pvl.grammar.OmniGrammar()`.
    :param decoder: defaults to :class:`pvl.decoder.OmniDecoder()`.
    :param ``**kwargs``: the keyword arguments to pass to the *parser* class
        if *parser* is none.
    """
    # decoder = __create_decoder(cls, strict, grammar=grammar, **kwargs)
    # return decoder.decode(s)

    if isinstance(s, bytes):
        # Someone passed us an old-style bytes sequence.  Although it isn't
        # a string, we can deal with it:
        s = s.decode()

    if parser is None:
        parser = OmniParser(grammar=grammar, decoder=decoder, **kwargs)
    elif not isinstance(parser, PVLParser):
        raise TypeError("The parser must be an instance of pvl.PVLParser.")

    return parser.parse(s)


def dump(module, path, **kwargs):
    """Serialize *module* as PVL text to the provided *path*.

    :param module: a ``PVLModule`` or ``dict``-like object to serialize.
    :param path: an :class:`os.PathLike`
    :param ``**kwargs``: the keyword arguments to pass to :func:`dumps()`.

    If *path* is an :class:`os.PathLike`, it will attempt to be opened
    and the serialized module will be written into that file via
    the :func:`pathlib.Path.write_text()` function, and will return
    what that function returns.

    If *path* is not an :class:`os.PathLike`, it will be assumed to be an
    already-opened file object, and ``.write()`` will be applied
    on that object to write the serialized module, and will return
    what that function returns.
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
            raise TypeError(
                "Expected an os.PathLike or an already-opened "
                "file object for writing, but got neither."
            )


def dumps(module, encoder=None, grammar=None, decoder=None, **kwargs) -> str:
    """Returns a string where the *module* object has been serialized
    to PVL syntax.

    :param module: a ``PVLModule`` or ``dict`` like object to serialize.
    :param encoder: defaults to :class:`pvl.parser.PDSLabelEncoder()`.
    :param grammar: defaults to :class:`pvl.grammar.ODLGrammar()`.
    :param decoder: defaults to :class:`pvl.decoder.ODLDecoder()`.
    :param ``**kwargs``: the keyword arguments to pass to the encoder
        class if *encoder* is none.
    """
    if encoder is None:
        encoder = PDSLabelEncoder(grammar=grammar, decoder=decoder, **kwargs)
    elif not isinstance(encoder, PVLEncoder):
        raise TypeError("The encoder must be an instance of pvl.PVLEncoder.")

    return encoder.encode(module)
