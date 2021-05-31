#!/usr/bin/env python
"""This module has tests for the pvl_validate functions."""

# Copyright 2021, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import argparse
import unittest
from unittest.mock import patch

import pvl.pvl_validate as pvl_val


class TestMock(unittest.TestCase):
    def setUp(self):
        self.flavors = ["chocolate", "vanilla"]
        self.report1 = (
            "choc.txt", {"chocolate": (True, True), "vanilla": (True, False)}
        )
        self.report2 = (
            "van.txt", {"chocolate": (False, False), "vanilla": (True, True)}
        )

    def test_arg_parser(self):
        p = pvl_val.arg_parser()
        self.assertIsInstance(p, argparse.ArgumentParser)

    @patch("pvl.get_text_from", return_value="a=b")
    def test_main(self, m_get):
        self.assertIsNone(pvl_val.main("dummy.txt"))

        self.assertIsNone(pvl_val.main(["-v", "dummy.txt"]))

    def test_pvl_flavor(self):
        dialect = "PDS3"
        loads, encodes = pvl_val.pvl_flavor(
            "a = b", dialect, pvl_val.dialects[dialect], "dummy.txt"
        )
        self.assertEqual(True, loads)
        self.assertEqual(True, encodes)

        loads, encodes = pvl_val.pvl_flavor(
            "foo", dialect, pvl_val.dialects[dialect], "dummy.txt"
        )
        self.assertEqual(False, loads)
        self.assertEqual(None, encodes)

        loads, encodes = pvl_val.pvl_flavor(
            "set_with_float = {1.5}",
            dialect,
            pvl_val.dialects[dialect],
            "dummy.txt"
        )
        self.assertEqual(True, loads)
        self.assertEqual(False, encodes)

        with patch("pvl.pvl_validate.pvl.loads", side_effect=Exception("bogus")):
            loads, encodes = pvl_val.pvl_flavor(
                "a=b", dialect, pvl_val.dialects[dialect], "dummy.txt"
            )
            loads, encodes = pvl_val.pvl_flavor(
                "a=b",
                dialect,
                pvl_val.dialects[dialect],
                "dummy.txt",
                verbose=2
            )
            self.assertEqual(False, loads)
            self.assertEqual(None, encodes)

    def test_report(self):
        self.assertRaises(
            IndexError,
            pvl_val.report,
            [["report", ], ],
            self.flavors
        )

        with patch("pvl.pvl_validate.report_many", return_value="many"):
            self.assertEqual(
                "many",
                pvl_val.report([self.report1, self.report2], self.flavors)
            )

        self.assertEqual(
            """\
chocolate |     Loads     |     Encodes    
vanilla   |     Loads     | does NOT encode""",
            pvl_val.report([self.report1, ], self.flavors)
        )

    def test_report_many(self):
        self.assertEqual(
            """\
---------+-----------+----------
File     | chocolate |  vanilla 
---------+-----------+----------
choc.txt |  L    E   |  L   No E
van.txt  | No L No E |  L    E  """,
            pvl_val.report_many(
                [self.report1, self.report2], self.flavors
            )
        )

    def test_build_line(self):
        self.assertEqual(
            "a   |  b  ",
            pvl_val.build_line(['a', 'b'], [3, 4])
        )
