# -*- coding: utf-8 -*-

import datetime
import unittest
from decimal import Decimal

from pvl.encoder import PVLEncoder, ODLEncoder, PDSLabelEncoder
from pvl.collections import Quantity, PVLModule, PVLGroup, PVLObject


class TestEncoder(unittest.TestCase):
    def setUp(self):
        self.e = PVLEncoder()

    def test_format(self):
        s = "ABC"
        self.assertEqual(s, self.e.format(s))
        self.assertEqual(f"  {s}", self.e.format(s, 1))

        s = "keyword = " + ("a" * 100)
        self.assertEqual(s, self.e.format(s))

        k = "keyword = "
        a60 = "a" * 60
        b60 = "b" * 60
        s = k + a60 + " " + b60
        self.assertEqual(
            (k + a60 + "\n" + (" " * len(k)) + b60), self.e.format(s)
        )

    def test_encode_string(self):
        s = "ABC"
        self.assertEqual(s, self.e.encode_string(s))

        s = 'AB"CD'
        self.assertEqual(f"'{s}'", self.e.encode_string(s))

        s = """AB'CD"""
        self.assertEqual(f'''"{s}"''', self.e.encode_string(s))

        s = "12:01"
        self.assertEqual(f'"{s}"', self.e.encode_string(s))

        s = "AB CD"
        self.assertEqual(f'"{s}"', self.e.encode_string(s))

        s = """Both"kinds'of quotes"""
        self.assertRaises(ValueError, self.e.encode_string, s)

    def test_encode_date(self):
        t = datetime.date(2019, 12, 31)
        self.assertEqual("2019-12-31", self.e.encode_date(t))

    def test_encode_time(self):
        t = datetime.time(1, 2)
        self.assertEqual("01:02", self.e.encode_time(t))

        t = datetime.time(13, 14, 15)
        self.assertEqual("13:14:15", self.e.encode_time(t))

        t = datetime.time(23, 24, 25, 123)
        self.assertEqual("23:24:25.000123", self.e.encode_time(t))

        t = datetime.time(23, 24, 0, 123)
        self.assertEqual("23:24:00.000123", self.e.encode_time(t))

    def test_encode_datetime(self):
        t = datetime.datetime(2001, 1, 1, 2, 3)
        self.assertEqual("2001-01-01T02:03", self.e.encode_datetime(t))

    def test_encode_set(self):
        f = frozenset(["a", "b", "c"])
        s_list = self.e.encode_set(f).strip("{}").split(", ")
        self.assertEqual(f, set(s_list))

    def test_encode_sequence(self):
        s = ["a", "b", "c"]
        self.assertEqual("(a, b, c)", self.e.encode_sequence(s))

    def test_encode_simple_value(self):
        pairs = (
            (None, "NULL"),
            (["a", "b", "c"], "(a, b, c)"),
            (datetime.datetime(2001, 1, 1, 2, 3), "2001-01-01T02:03"),
            (True, "TRUE"),
            (1.23, "1.23"),
            (42, "42"),
            (Decimal("12.30"), "12.30"),
            ("ABC", "ABC"),
        )
        for p in pairs:
            with self.subTest(pair=p):
                self.assertEqual(p[1], self.e.encode_simple_value(p[0]))

    def test_encode_value(self):
        pairs = ((42, "42"), (Quantity(34, "m/s"), "34 <m/s>"))
        for p in pairs:
            with self.subTest(pair=p):
                self.assertEqual(p[1], self.e.encode_value(p[0]))

    def test_encode_assignment(self):
        self.assertEqual("a = b;", self.e.encode_assignment("a", "b"))

    def test_encode_aggregation_block(self):
        g = PVLGroup(a="b", c="d")
        s = "BEGIN_GROUP = foo;\n  a = b;\n  c = d;\nEND_GROUP = foo;"
        self.assertEqual(s, self.e.encode_aggregation_block("foo", g))

    def test_encode_module(self):
        m = PVLModule(foo=PVLGroup(a="b", c="d"))
        s = "BEGIN_GROUP = foo;\n  a = b;\n  c = d;\nEND_GROUP = foo;"
        self.assertEqual(s, self.e.encode_module(m))

    def test_encode(self):
        g = PVLGroup(a="b", c="d")
        s = "a = b;\nc = d;\nEND;"
        self.assertEqual(s, self.e.encode(g))

        m = PVLModule(foo=PVLGroup(a="b", c="d"))
        s = "BEGIN_GROUP = foo;\n  a = b;\n  c = d;\nEND_GROUP = foo;\nEND;"
        self.assertEqual(s, self.e.encode(m))

        m = PVLModule(
            foo=PVLGroup(
                a="b", c="d", newline="Should be quoted\nand two lines."
            )
        )
        s = """BEGIN_GROUP = foo;
  a       = b;
  c       = d;
  newline = "Should be quoted
and two lines.";
END_GROUP = foo;
END;"""
        self.assertEqual(s, self.e.encode(m))

    def test_encode_quantity(self):
        q, s = Quantity(34, "m/s"), "34 <m/s>"
        self.assertEqual(s, self.e.encode_quantity(q))

        self.assertRaises(ValueError, self.e.encode_quantity, "not a quant")

        try:
            from astropy import units as u

            # astropy.units.Quantity makes values floating point
            # and appears to print the units with spaces.
            # It doesn't violate the PVL spec, but may cause users
            # a surprise.  However, if they are using Astropy
            # Quantities, they are theoretically aware of all that.
            q, s = u.Quantity(34, "m/s"), "34.0 <m / s>"
            self.assertEqual(s, self.e.encode_quantity(q))
        except ImportError:  # astropy isn't available.
            pass

        try:
            from pint import Quantity as pintquant

            # pint.Quantity also has its own peculiarities about
            # formating the output.  Again, doesn't break the spec,
            # but may cause surprises.
            q, s = pintquant(34, "m/s"), "34 <meter / second>"
            self.assertEqual(s, self.e.encode_quantity(q))
        except ImportError:  # pint isn't available.
            pass


class TestODLEncoder(unittest.TestCase):
    def setUp(self):
        self.e = ODLEncoder()

    def test_is_scalar(self):
        self.assertTrue(self.e.is_scalar(5))
        self.assertTrue(self.e.is_scalar("scalar"))
        self.assertTrue(self.e.is_scalar(Quantity(5, "m")))
        self.assertFalse(self.e.is_scalar(Quantity("five", "m")))

    def test_encode_quantity(self):
        try:
            from astropy import units as u

            p = (u.Quantity(34, "m/s"), "34.0 <m / s>")
            self.assertEqual(p[1], self.e.encode_quantity(p[0]))
        except ImportError:  # astropy isn't available.
            pass

    def test_encode_time(self):
        t = datetime.time(1, 2)
        self.assertRaises(ValueError, self.e.encode_time, t)

        t = datetime.time(13, 14, 15,)
        self.assertRaises(ValueError, self.e.encode_time, t)

        t = datetime.time(
            13, 14, 15, tzinfo=datetime.timezone(datetime.timedelta(hours=2))
        )
        self.assertEqual("13:14:15+02", self.e.encode_time(t))

        t = datetime.time(
            13, 14, 15, tzinfo=datetime.timezone(datetime.timedelta(hours=0))
        )
        self.assertEqual("13:14:15Z", self.e.encode_time(t))

        t = datetime.time(15, 15, 59, tzinfo=datetime.timezone.utc)
        self.assertEqual("15:15:59Z", self.e.encode_time(t))


class TestPDSLabelEncoder(unittest.TestCase):
    def setUp(self):
        self.e = PDSLabelEncoder()

    def test_count_aggs(self):
        m = PVLModule(a=PVLGroup(), b=PVLObject(), c=PVLObject())
        self.assertEqual((2, 1), self.e.count_aggs(m))

    def test_is_PDSgroup(self):
        g = PVLGroup(a="b", c=PVLGroup())
        self.assertFalse(self.e.is_PDSgroup(g))

        g = PVLGroup({"a": "b", "^c": 5})
        self.assertFalse(self.e.is_PDSgroup(g))

        g = PVLGroup({"a": "b", "^c": "d"})
        self.assertTrue(self.e.is_PDSgroup(g))

        g = PVLGroup((("a", "b"), ("c", "d"), ("a", "b2")))
        self.assertFalse(self.e.is_PDSgroup(g))

    def test_convert_grp_to_obj(self):
        g = PVLGroup(a="b", c="d")
        o = PVLObject(a="b", c="d")
        converted = PVLObject(g)
        self.assertEqual(o, converted)
        self.assertIsInstance(converted, PVLObject)

    def test_encode_aggregation_block(self):
        g = PVLGroup(a="b", c=PVLGroup(d="e"))
        no_convert = PDSLabelEncoder(convert_group_to_object=False)
        self.assertRaises(
            ValueError, no_convert.encode_aggregation_block, "key", g
        )

        s = """OBJECT = key\r
  A = b\r
  GROUP = c\r
    D = e\r
  END_GROUP = c\r
END_OBJECT = key"""
        self.assertEqual(s, self.e.encode_aggregation_block("key", g))

    def test_encode_set(self):
        s = {"a", "has'apostrophe"}
        self.assertRaises(ValueError, self.e.encode_set, s)

        s = {"a", "has\newline"}
        self.assertRaises(ValueError, self.e.encode_set, s)

    def test_encode_time(self):
        t = datetime.time(1, 2)
        self.assertEqual("01:02Z", self.e.encode_time(t))

        t = datetime.time(13, 14, 15,)
        self.assertEqual("13:14:15Z", self.e.encode_time(t))

        # time objects with offsets other than zero should raise an Exception.
        t = datetime.time(
            13, 14, 15, tzinfo=datetime.timezone(datetime.timedelta(hours=2))
        )
        self.assertRaises(ValueError, self.e.encode_time, t)

        t = datetime.time(
            13, 14, 15, tzinfo=datetime.timezone(datetime.timedelta(hours=0))
        )
        self.assertEqual("13:14:15Z", self.e.encode_time(t))

        t = datetime.time(15, 15, 59, tzinfo=datetime.timezone.utc)
        self.assertEqual("15:15:59Z", self.e.encode_time(t))

        t = datetime.time(10, 54, 12, 129000, tzinfo=datetime.timezone.utc)
        self.assertEqual("10:54:12.129Z", self.e.encode_time(t))

        # time objects with precision greater than milisecond should raise
        t = datetime.time(10, 54, 12, 123456, tzinfo=datetime.timezone.utc)
        self.assertRaises(ValueError, self.e.encode_time, t)

        e = PDSLabelEncoder(time_trailing_z=False)
        self.assertEqual("01:02", e.encode_time(datetime.time(1, 2)))

    def test_encode_string(self):
        e = PDSLabelEncoder(symbol_single_quote=False)
        self.assertEqual('"AB CD"', e.encode_string('AB CD'))

    def test_encode(self):
        m = PVLModule(a=PVLGroup(g1=2, g2=3.4), b="c")

        no_convert = PDSLabelEncoder(convert_group_to_object=False)
        self.assertRaises(ValueError, no_convert.encode, m)

        s = """OBJECT = a\r
  G1 = 2\r
  G2 = 3.4\r
END_OBJECT = a\r
B = c\r
END\r\n"""
        self.assertEqual(s, self.e.encode(m))

        m = PVLModule(
            a="b",
            staygroup=PVLGroup(c="d"),
            obj=PVLGroup(d="e", f=PVLGroup(g="h")),
        )

        s = """A = b\r
GROUP = staygroup\r
  C = d\r
END_GROUP = staygroup\r
OBJECT = obj\r
  D = e\r
  GROUP = f\r
    G = h\r
  END_GROUP = f\r
END_OBJECT = obj\r
END\r\n"""

        self.assertEqual(s, self.e.encode(m))
