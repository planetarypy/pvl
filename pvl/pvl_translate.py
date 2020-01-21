# -*- coding: utf-8 -*-
"""A program for converting PVL text to a specific PVL dialect."""

# Copyright 2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import argparse
import sys

import pvl
from .encoder import PVLEncoder, ODLEncoder, ISISEncoder, PDSLabelEncoder


def main():
    formats = dict(PDS3=PDSLabelEncoder(),
                   ODL=ODLEncoder(),
                   ISIS=ISISEncoder(),
                   PVL=PVLEncoder())

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-of', '--output_format', required=True,
                        choices=formats.keys(),
                        help='Select the format to create the new file as.')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin,
                        help='file containing PVL text to translate, '
                        'defaults to STDIN.')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout,
                        help='file to write translated PVL to, defaults '
                        'to STDOUT.')

    args = parser.parse_args()

    some_pvl = pvl.load(args.infile)

    pvl.dump(some_pvl, args.outfile, encoder=formats[args.output_format])
    return


if __name__ == "__main__":
    sys.exit(main())
