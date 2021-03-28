#!/usr/bin/env python
"""This module has tests for the pvl decoder functions."""

# Copyright 2019-2021, Ross A. Beyer (rbeyer@seti.org)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import itertools
import unittest
from decimal import Decimal

from pvl.decoder import PVLDecoder, ODLDecoder, PDSLabelDecoder, for_try_except
from pvl.collections import Quantity


class TestForTryExcept(unittest.TestCase):
    def test_for_try_except(self):
        self.assertEqual(
            5, for_try_except(ValueError, int, ("frank", "7.7", "5"))
        )
        self.assertRaises(
            ValueError, for_try_except, ValueError, int, ("frank", "7.7", "a")
        )

        self.assertEqual(
            datetime.date(2001, 1, 1),
            for_try_except(
                ValueError,
                datetime.datetime.strptime,
                itertools.repeat("2001-001"),
                ("%Y-%m-%d", "%Y-%j"),
            ).date(),
        )


class TestDecoder(unittest.TestCase):
    def setUp(self):
        self.d = PVLDecoder()

    def test_decode_quoted_string(self):
        self.assertEqual("Quoted", self.d.decode_quoted_string('"Quoted"'))
        self.assertEqual(
            'He said, "hello"',
            self.d.decode_quoted_string("""'He said, "hello"'"""),
        )
        self.assertEqual(
            'She said, \\"bye\\"',
            self.d.decode_quoted_string(r"'She said, \"bye\"'"),
        )
        self.assertEqual(
            "No\\tin Python", self.d.decode_quoted_string(r"'No\tin Python'")
        )
        self.assertEqual(
            "Line -\n Continued",
            self.d.decode_quoted_string("'Line -\n Continued'"),
        )

        # print(self.d.decode_quoted_string("""'mixed"\\'quotes'"""))

    def test_decode_unquoted_string(self):
        self.assertEqual("Unquoted", self.d.decode_unquoted_string("Unquoted"))

        for s in (
            'hhhhh"hello"',
            "Reserved=",
            "No\tin Python",
            "Line -\n Continued",
        ):
            with self.subTest(string=s):
                self.assertRaises(ValueError, self.d.decode_unquoted_string, s)

    def test_decode_decimal(self):
        for p in (
            ("125", 125),
            ("+211109", 211109),
            ("-79", -79),
            ("69.35", 69.35),
            ("+12456.345", 12456.345),  # Integers
            ("-0.23456", -0.23456),
            (".05", 0.05),
            ("-7.", -7),  # Floating
            ("-2.345678E12", -2345678000000.0),
            ("1.567E-10", 1.567e-10),
            ("+4.99E+3", 4990.0),
        ):  # Exponential
            with self.subTest(pair=p):
                self.assertEqual(p[1], self.d.decode_decimal(p[0]))

        for s in ("2#0101#", "frank"):
            with self.subTest(string=s):
                self.assertRaises(ValueError, self.d.decode_decimal, s)

    def test_decode_withDecimal(self):
        d = PVLDecoder(real_cls=Decimal)
        s = "123.450"
        self.assertEqual(d.decode_decimal(s), Decimal(s))

        self.assertRaises(ValueError, d.decode_decimal, "fruit")

    def test_decode_non_decimal(self):
        for p in (
            ("2#0101#", 5),
            ("+2#0101#", 5),
            ("-2#0101#", -5),  # Binary
            ("8#0107#", 71),
            ("+8#0156#", 110),
            ("-8#0134#", -92),  # Oct
            ("16#100A#", 4106),
            ("+16#23Bc#", 9148),
            ("-16#98ef#", -39151),
        ):  # Hex
            with self.subTest(pair=p):
                self.assertEqual(p[1], self.d.decode_non_decimal(p[0]))

    def test_decode_datetime(self):
        utc = datetime.timezone.utc
        for p in (
            ("2001-01-01", datetime.date(2001, 1, 1)),
            ("2001-027", datetime.date(2001, 1, 27)),
            ("2001-027Z", datetime.date(2001, 1, 27)),
            ("23:45", datetime.time(23, 45, tzinfo=utc)),
            ("01:42:57", datetime.time(1, 42, 57, tzinfo=utc)),
            ("12:34:56.789", datetime.time(12, 34, 56, 789000, tzinfo=utc)),
            (
                "2001-027T23:45",
                datetime.datetime(2001, 1, 27, 23, 45, tzinfo=utc),
            ),
            (
                "2001-01-01T01:34Z",
                datetime.datetime(2001, 1, 1, 1, 34, tzinfo=utc),
            ),
            ("01:42:57Z", datetime.time(1, 42, 57, tzinfo=utc)),
            ("2001-12-31T01:59:60.123Z", "2001-12-31T01:59:60.123Z"),
            ("2001-12-31T01:59:60.123456789", "2001-12-31T01:59:60.123456789"),
            ("01:00:60", "01:00:60"),
        ):
            with self.subTest(pair=p):
                self.assertEqual(p[1], self.d.decode_datetime(p[0]))

        self.assertRaises(ValueError, self.d.decode_datetime, "frank")

        fancy = "2001-001T01:10:39+7"
        self.assertRaises(ValueError, self.d.decode_datetime, fancy)

    def test_decode_simple_value(self):
        for p in (
            ("2001-01-01", datetime.date(2001, 1, 1)),
            ("2#0101#", 5),
            ("-79", -79),
            ("Unquoted", "Unquoted"),
            ('"Quoted"', "Quoted"),
            ("Null", None),
            ("TRUE", True),
            ("false", False),
        ):
            with self.subTest(pair=p):
                self.assertEqual(p[1], self.d.decode_simple_value(p[0]))

    def test_decode_quantity(self):
        q = self.d.decode_quantity("15", "m/s")
        self.assertEqual(q, Quantity("15", "m/s"))

        try:
            from astropy import units as u

            d = PVLDecoder(quantity_cls=u.Quantity)
            q = d.decode_quantity("15", "m/s")
            self.assertEqual(q, u.Quantity("15", "m/s"))
        except ImportError:  # astropy isn't available.
            pass

        try:
            from pint import Quantity as pintquant

            d = PVLDecoder(quantity_cls=pintquant)
            q = d.decode_quantity("15", "m/s")
            self.assertEqual(q, pintquant("15", "m/s"))
        except ImportError:  # pint isn't available.
            pass


class TestODLDecoder(unittest.TestCase):
    def setUp(self):
        self.d = ODLDecoder()

    def test_decode_datetime(self):
        utc = datetime.timezone.utc

        for p in (
                ("1990-07-04", datetime.date(1990, 7, 4)),
                ("1990-158", datetime.date(1990, 6, 7)),
                ("2001-001", datetime.date(2001, 1, 1)),
                ("2001-01-01", datetime.date(2001, 1, 1)),
                ("12:00", datetime.time(12)),
                ("12:00:45", datetime.time(12, 0, 45)),
                (
                        "12:00:45.4571",
                        datetime.time(12, 0, 45, 457100),
                ),
                ("15:24:12Z", datetime.time(15, 24, 12, tzinfo=utc)),
                ("1990-07-04T12:00", datetime.datetime(1990, 7, 4, 12)),
                (
                    "1990-158T15:24:12Z",
                    datetime.datetime(1990, 6, 7, 15, 24, 12, tzinfo=utc),
                ),
        ):
            with self.subTest(pair=p):
                self.assertEqual(p[1], self.d.decode_datetime(p[0]))

        self.assertRaises(ValueError, self.d.decode_datetime, "01:00:60")

        try:
            from dateutil import tz
            tz_plus_7 = tz.tzoffset("+7", datetime.timedelta(hours=7))

            for p in (
                ("01:12:22+07", datetime.time(1, 12, 22, tzinfo=tz_plus_7)),
                ("01:12:22+7", datetime.time(1, 12, 22, tzinfo=tz_plus_7)),
                (
                    "01:10:39.4575+07",
                    datetime.time(1, 10, 39, 457500, tzinfo=tz_plus_7),
                ),
                (
                    "2001-001T01:10:39+7",
                    datetime.datetime(2001, 1, 1, 1, 10, 39, tzinfo=tz_plus_7),
                ),
                (
                    "2001-001T01:10:39.457591+7",
                    datetime.datetime(
                        2001, 1, 1, 1, 10, 39, 457591, tzinfo=tz_plus_7
                    ),
                ),
            ):
                with self.subTest(pair=p):
                    self.assertEqual(p[1], self.d.decode_datetime(p[0]))

        except ImportError:  # dateutil isn't available.
            pass


class TestPDS3Decoder(unittest.TestCase):
    def setUp(self):
        self.d = PDSLabelDecoder()

    def test_decode_datetime(self):
        utc = datetime.timezone.utc

        for p in (
            ("1990-07-04", datetime.date(1990, 7, 4)),
            ("1990-158", datetime.date(1990, 6, 7)),
            ("2001-001", datetime.date(2001, 1, 1)),
            ("2001-01-01", datetime.date(2001, 1, 1)),
            ("12:00", datetime.time(12, tzinfo=utc)),
            ("12:00:45", datetime.time(12, 0, 45, tzinfo=utc)),
            ("15:24:12Z", datetime.time(15, 24, 12, tzinfo=utc)),
            (
                "1990-158T15:24:12Z",
                datetime.datetime(1990, 6, 7, 15, 24, 12, tzinfo=utc)),
            (
                "12:00:45.457",
                datetime.time(12, 0, 45, 457000, tzinfo=utc),
            ),
            (
                "1990-07-04T12:00",
                datetime.datetime(1990, 7, 4, 12, tzinfo=utc),
            ),
        ):
            with self.subTest(pair=p):
                self.assertEqual(p[1], self.d.decode_datetime(p[0]))

        for t in (
                "01:12:22+07",
                "01:12:22+7",
                "01:10:39.4575+07",
                "2001-001T01:10:39+7",
                "2001-001T01:10:39.457591+7",
                "2001-001T01:10:39.457591",
        ):
            with self.subTest(time=t):
                self.assertRaises(ValueError, self.d.decode_datetime, t)
