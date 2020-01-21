# -*- coding: utf-8 -*-
"""A program for testing and validating PVL text.

Returns a report for one file or many.  The program
will attempt to load the PVL text in each file
with the various kinds of PVL dialects, and if successful,
will also try and encode the read-in text.  Some kinds of
PVL text can be loaded, but not encoded.
"""

# Copyright 2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import argparse
import sys

import pvl
from .lexer import LexerError
from .grammar import PVLGrammar, ODLGrammar, ISISGrammar, OmniGrammar
from .parser import ParseError, PVLParser, ODLParser, OmniParser
from .decoder import PVLDecoder, ODLDecoder, OmniDecoder
from .encoder import PVLEncoder, ODLEncoder, ISISEncoder, PDSLabelEncoder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', nargs='+',
                        help='file containing PVL text to validate.')

    args = parser.parse_args()

    results_list = list()
    for f in args.file:
        pvl_text = pvl.get_text_from(f)

        results = dict()

        results['PDS3'] = pvl_flavor(pvl_text,
                                     ODLParser(), ODLGrammar(),
                                     ODLDecoder(), PDSLabelEncoder())
        results['ODL'] = pvl_flavor(pvl_text,
                                    ODLParser(), ODLGrammar(),
                                    ODLDecoder(), ODLEncoder())
        results['PVL'] = pvl_flavor(pvl_text,
                                    PVLParser(), PVLGrammar(),
                                    PVLDecoder(), PVLEncoder())
        results['ISIS'] = pvl_flavor(pvl_text,
                                     OmniParser(), ISISGrammar(),
                                     OmniDecoder(), ISISEncoder())
        results['Omni'] = pvl_flavor(pvl_text,
                                     OmniParser(), OmniGrammar(),
                                     OmniDecoder(), PVLEncoder())
        results_list.append((f, results))

    # Writing the flavors out again to preserve order.
    print(report(results_list, ['PDS3', 'ODL', 'PVL', 'ISIS', 'Omni']))
    return


def pvl_flavor(text, p, g, d, e) -> tuple((bool, bool)):
    """Returns a two-tuple of booleans which indicate
    whether the *text* could be loaded and then encoded.

    The first boolean in the two-tuple indicates whether the *text*
    could be loaded with the given parser, grammar, and decoder.
    The second indicates whether the loaded PVL object could be
    encoded with the given encoder, grammar, and decoder.  If the
    first element is False, the second will be None.
    """
    loads = None
    encodes = None
    try:
        some_pvl = pvl.loads(text,
                             parser=p,
                             grammar=g,
                             decoder=d)
        loads = True

        try:
            pvl.dumps(some_pvl,
                      encoder=e,
                      grammar=g,
                      decoder=d)
            encodes = True
        except (LexerError, ParseError, ValueError):
            encodes = False
    except (LexerError, ParseError):
        loads = False

    return (loads, encodes)


def report(reports: list, flavors: list) -> str:
    """Returns a multi-line string which is the
    pretty-printed report given the list of
    *reports*.
    """
    if len(reports[0][1]) != len(flavors):
        raise IndexError("The length of the report list keys "
                         f"({len(reports[0][1])}) "
                         "and the length of the flavors list "
                         f"({len(flavors)}) aren't the same.")

    if len(reports) > 1:
        return report_many(reports, flavors)

    r = reports[0][1]

    lines = list()
    loads = {True: 'Loads', False: 'does NOT load'}
    encodes = {True: 'Encodes', False: 'does NOT encode', None: ''}

    col1w = len(max(flavors, key=len))
    col2w = len(max(loads.values(), key=len))
    col3w = len(max(encodes.values(), key=len))

    for k in flavors:
        lines.append(build_line([k, loads[r[k][0]], encodes[r[k][1]]],
                                [col1w, col2w, col3w]))
    return '\n'.join(lines)


def report_many(r_list: list, flavors: list) -> str:
    """Returns a multi-line, table-like string which
    is the pretty-printed report of the items in *r_list*.
    """

    lines = list()
    loads = {True: 'L', False: 'No L'}
    encodes = {True: 'E', False: 'No E', None: ''}

    col1w = len(max([x[0] for x in r_list], key=len))
    col2w = len(max(loads.values(), key=len))
    col3w = len(max(encodes.values(), key=len))
    flavorw = col2w + col3w + 1

    header = ['File'] + flavors
    headerw = [col1w] + [flavorw] * len(flavors)
    rule = [' ' * col1w] + [' ' * flavorw] * len(flavors)

    rule_line = build_line(rule, headerw).replace('|', '+').replace(' ', '-')
    lines.append(rule_line)
    lines.append(build_line(header, headerw))
    lines.append(rule_line)

    for r in r_list:
        cells = [r[0]]
        widths = [col1w]
        for f in flavors:
            # cells.append(loads[r[1][f][0]] + ' ' + encodes[r[1][f][1]])
            cells.append('{0:^{w2}} {1:^{w3}}'.format(loads[r[1][f][0]],
                                                      encodes[r[1][f][1]],
                                                      w2=col2w,
                                                      w3=col3w))
            widths.append(flavorw)
        lines.append(build_line(cells, widths))

    return '\n'.join(lines)


def build_line(elements: list, widths: list, sep=' | ') -> str:
    """Returns a string formatted from the *elements* and *widths*
       provided.
    """
    cells = list()
    cells.append('{0:<{width}}'.format(elements[0], width=widths[0]))

    for e, w in zip(elements[1:], widths[1:]):
        cells.append('{0:^{width}}'.format(e, width=w))

    return sep.join(cells)


if __name__ == "__main__":
    sys.exit(main())
