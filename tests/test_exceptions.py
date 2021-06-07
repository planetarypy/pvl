#!/usr/bin/env python
"""This module has tests for the pvl.exceptions functions."""

# Copyright 2021, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import unittest

import pvl.exceptions


class TestMock(unittest.TestCase):

    def test_LexerError(self):
        e = pvl.exceptions.LexerError("lex error", "This is the document.", 2, "Th")
        self.assertEqual(
            (
                pvl.exceptions.LexerError,
                ("lex error", "This is the document.", 1, "Th")
            ),
            e.__reduce__()
        )
