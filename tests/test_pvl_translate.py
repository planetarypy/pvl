#!/usr/bin/env python
"""This module has tests for the pvl_translate functions."""

# Copyright 2021, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import argparse
import unittest
from unittest.mock import patch, PropertyMock, MagicMock

import pvl.pvl_translate as pvl_trans
from pvl.encoder import PDSLabelEncoder


class TestMock(unittest.TestCase):
    def test_Writer(self):
        w = pvl_trans.Writer()
        self.assertRaises(Exception, w.dump, dict(a="b"), "dummy.txt")

    @patch("pvl.dump")
    def test_PVLWriter(self, m_dump):
        e = PDSLabelEncoder()
        w = pvl_trans.PVLWriter(e)
        d = dict(a="b")
        f = "dummy.pathlike"
        w.dump(d, f)
        m_dump.assert_called_once_with(d, f, encoder=e)

    @patch("json.dump")
    def test_JSONWriter(self, m_dump):
        w = pvl_trans.JSONWriter()
        d = dict(a="b")
        f = "dummy.pathlike"
        w.dump(d, f)
        m_dump.assert_called_once_with(d, f)

    def test_arg_parser(self):
        p = pvl_trans.arg_parser(pvl_trans.formats)
        self.assertIsInstance(p, argparse.ArgumentParser)

    @patch("pvl.pvl_translate.JSONWriter")
    @patch("pvl.pvl_translate.PVLWriter")
    @patch("pvl.pvl_translate.arg_parser")
    @patch("pvl.load")
    @patch("pvl.dump")
    def test_main(self, m_dump, m_load, m_parser, m_PVLWriter, m_JSONWriter):
        m_parser().parse_args().output_format = "PDS3"
        self.assertIsNone(pvl_trans.main())

