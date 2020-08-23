# -*- coding: utf-8 -*-
"""A program for converting PVL text to a specific PVL dialect.

The ``pvl_translate`` program will read a file with PVL text (any
of the kinds of files that :func:`pvl.load` reads) or STDIN and
will convert that PVL text to a particular PVL dialect.  It is not
particularly robust, and if it cannot make simple conversions, it
will raise errors.
"""

# Copyright 2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import argparse
import json
import os
import sys

import pvl
from .encoder import PVLEncoder, ODLEncoder, ISISEncoder, PDSLabelEncoder


class Writer(object):
    """Base class for writers.  Descendents must implement dump().
    """

    def dump(self, dictlike: dict, outfile: os.PathLike):
        raise Exception


class PVLWriter(Writer):
    def __init__(self, encoder):
        self.encoder = encoder

    def dump(self, dictlike: dict, outfile: os.PathLike):
        return pvl.dump(dictlike, outfile, encoder=self.encoder)


class JSONWriter(Writer):
    def dump(self, dictlike: dict, outfile: os.PathLike):
        return json.dump(dictlike, outfile)


formats = dict(
    PDS3=PVLWriter(PDSLabelEncoder()),
    ODL=PVLWriter(ODLEncoder()),
    ISIS=PVLWriter(ISISEncoder()),
    PVL=PVLWriter(PVLEncoder()),
    JSON=JSONWriter(),
)


def arg_parser(formats):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-of",
        "--output_format",
        required=True,
        choices=formats.keys(),
        help="Select the format to create the new file as.",
    )
    parser.add_argument(
        "infile",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="file containing PVL text to translate, " "defaults to STDIN.",
    )
    parser.add_argument(
        "outfile",
        nargs="?",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="file to write translated PVL to, defaults " "to STDOUT.",
    )
    parser.add_argument("--version", action="version", version=pvl.__version__)
    return parser


def main():
    args = arg_parser(formats).parse_args()

    some_pvl = pvl.load(args.infile)

    formats[args.output_format].dump(some_pvl, args.outfile)
    return


if __name__ == "__main__":
    sys.exit(main())
