#!/usr/bin/env python
"""This module has unit tests for the pvl __init__ functions."""

# Copyright 2019, Ross A. Beyer (rbeyer@seti.org)
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

import io
import unittest
from unittest.mock import call, create_autospec, mock_open, patch

from pathlib import Path

import pvl

data_dir = Path("tests/data")


class TestLoadS(unittest.TestCase):
    def test_loads(self):
        some_pvl = """
a = b
GROUP = c
    c = d
END_GROUP
e =false
END"""
        decoded = pvl.PVLModule(a="b", c=pvl.PVLGroup(c="d"), e=False)
        self.assertEqual(decoded, pvl.loads(some_pvl))

        self.assertEqual(pvl.PVLModule(a="b"), pvl.loads("a=b"))


class TestLoad(unittest.TestCase):
    def setUp(self):
        self.simple = data_dir / "pds3" / "simple_image_1.lbl"
        rawurl = "https://raw.githubusercontent.com/planetarypy/pvl/main/"
        self.url = rawurl + str(self.simple)
        self.simplePVL = pvl.PVLModule(
            {
                "PDS_VERSION_ID": "PDS3",
                "RECORD_TYPE": "FIXED_LENGTH",
                "RECORD_BYTES": 824,
                "LABEL_RECORDS": 1,
                "FILE_RECORDS": 601,
                "^IMAGE": 2,
                "IMAGE": pvl.PVLObject(
                    {
                        "LINES": 600,
                        "LINE_SAMPLES": 824,
                        "SAMPLE_TYPE": "MSB_INTEGER",
                        "SAMPLE_BITS": 8,
                        "MEAN": 51.67785396440129,
                        "MEDIAN": 50.0,
                        "MINIMUM": 0,
                        "MAXIMUM": 255,
                        "STANDARD_DEVIATION": 16.97019,
                        "CHECKSUM": 25549531,
                    }
                ),
            }
        )

    def test_load_w_open(self):
        with open(self.simple) as f:
            self.assertEqual(self.simplePVL, pvl.load(f))

    def test_load_w_Path(self):
        self.assertEqual(self.simplePVL, pvl.load(self.simple))

    def test_load_w_string_path(self):
        string_path = str(self.simple)
        self.assertEqual(self.simplePVL, pvl.load(string_path))

    def test_loadu(self):
        self.assertEqual(self.simplePVL, pvl.loadu(self.url))
        self.assertEqual(
            self.simplePVL, pvl.loadu(self.simple.resolve().as_uri())
        )

    @patch("pvl.loads")
    @patch("pvl.decode_by_char")
    def test_loadu_args(self, m_decode, m_loads):
        pvl.loadu(self.url, data=None)
        pvl.loadu(self.url, noturlopen="should be passed to loads")
        m_decode.assert_called()
        self.assertNotIn("data", m_loads.call_args_list[0][1])
        self.assertIn("noturlopen", m_loads.call_args_list[1][1])

    def test_load_w_quantity(self):
        try:
            from astropy import units as u
            from pvl.decoder import OmniDecoder

            pvl_file = "tests/data/pds3/units1.lbl"
            km_upper = u.def_unit("KM", u.km)
            m_upper = u.def_unit("M", u.m)
            u.add_enabled_units([km_upper, m_upper])
            label = pvl.load(
                pvl_file, decoder=OmniDecoder(quantity_cls=u.Quantity)
            )
            self.assertEqual(label["FLOAT_UNIT"], u.Quantity(0.414, "KM"))
        except ImportError:
            pass


class TestISIScub(unittest.TestCase):
    def setUp(self):
        self.cub = data_dir / "pattern.cub"
        self.cubpvl = pvl.PVLModule(
            IsisCube=pvl.PVLObject(
                Core=pvl.PVLObject(
                    StartByte=65537,
                    Format="Tile",
                    TileSamples=128,
                    TileLines=128,
                    Dimensions=pvl.PVLGroup(Samples=90, Lines=90, Bands=1),
                    Pixels=pvl.PVLGroup(
                        Type="Real", ByteOrder="Lsb", Base=0.0, Multiplier=1.0
                    ),
                )
            ),
            Label=pvl.PVLObject(Bytes=65536),
        )

    def test_load_cub(self):
        self.assertEqual(self.cubpvl, pvl.load(self.cub))

    def test_load_cub_opened(self):
        with open(self.cub, "rb") as f:
            self.assertEqual(self.cubpvl, pvl.load(f))


class TestDumpS(unittest.TestCase):
    def setUp(self):
        self.module = pvl.PVLModule(
            a="b",
            staygroup=pvl.PVLGroup(c="d"),
            obj=pvl.PVLGroup(d="e", f=pvl.PVLGroup(g="h")),
        )

    def test_dumps_PDS(self):
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
        self.assertEqual(s, pvl.dumps(self.module))

    def test_dumps_PVL(self):
        s = """a = b;
BEGIN_GROUP = staygroup;
  c = d;
END_GROUP = staygroup;
BEGIN_GROUP = obj;
  d = e;
  BEGIN_GROUP = f;
    g = h;
  END_GROUP = f;
END_GROUP = obj;
END;"""

        self.assertEqual(
            s, pvl.dumps(self.module, encoder=pvl.encoder.PVLEncoder())
        )

    def test_dumps_ODL(self):

        s = """A = b\r
GROUP = staygroup\r
  C = d\r
END_GROUP = staygroup\r
GROUP = obj\r
  D = e\r
  GROUP = f\r
    G = h\r
  END_GROUP = f\r
END_GROUP = obj\r
END\r\n"""

        self.assertEqual(
            s, pvl.dumps(self.module, encoder=pvl.encoder.ODLEncoder())
        )


class TestDump(unittest.TestCase):
    def setUp(self):
        self.module = pvl.PVLModule(
            a="b",
            staygroup=pvl.PVLGroup(c="d"),
            obj=pvl.PVLGroup(d="e", f=pvl.PVLGroup(g="h")),
        )
        self.string = """A = b\r
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

    def test_dump_Path(self):
        mock_path = create_autospec(Path)
        with patch("pvl.Path", autospec=True, return_value=mock_path):
            pvl.dump(self.module, Path("dummy"))
            self.assertEqual(
                [call.write_text(self.string)], mock_path.method_calls
            )

    @patch("builtins.open", mock_open())
    def test_dump_file_object(self):
        with open("dummy", "w") as f:
            pvl.dump(self.module, f)
            self.assertEqual(
                [call.write(self.string.encode())], f.method_calls
            )

    def test_not_dumpable(self):
        f = 5
        self.assertRaises(TypeError, pvl.dump, self.module, f)


class TestDecode(unittest.TestCase):

    def test_str(self):
        s = "A test string\n"
        stream = io.StringIO(s)
        self.assertEqual(s, pvl.decode_by_char(stream))

    def test_utf(self):
        s = "A test with single-byte UTF characters."
        stream = io.BytesIO(s.encode())
        self.assertEqual(s, pvl.decode_by_char(stream))

    def test_latin1(self):
        s = "A test with single-byte latin-1 characters."
        stream = io.BytesIO(s.encode(encoding="latin-1"))
        self.assertEqual(s, pvl.decode_by_char(stream))

        ascii_text = "A few okay upper latin-1 chars: "
        some = ascii_text + "°."
        stream = io.BytesIO(some.encode(encoding="latin-1"))
        self.assertEqual(ascii_text, pvl.decode_by_char(stream))
