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

import unittest
from unittest.mock import call, create_autospec, mock_open, patch

from pathlib import Path

import pvl
import pvl.new as pvln
from pvl.collections import PVLModuleNew as PVLModule
from pvl.collections import PVLGroupNew as PVLGroup
from pvl.collections import PVLObjectNew as PVLObject

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
        decoded = PVLModule(a="b", c=PVLGroup(c="d"), e=False)
        self.assertEqual(decoded, pvln.loads(some_pvl))

        self.assertEqual(PVLModule(a="b"), pvln.loads("a=b"))


class TestLoad(unittest.TestCase):
    def setUp(self):
        self.simple = data_dir / "pds3" / "simple_image_1.lbl"
        rawurl = "https://raw.githubusercontent.com/planetarypy/pvl/main/"
        self.url = rawurl + str(self.simple)
        self.simplePVL = PVLModule(
            {
                "PDS_VERSION_ID": "PDS3",
                "RECORD_TYPE": "FIXED_LENGTH",
                "RECORD_BYTES": 824,
                "LABEL_RECORDS": 1,
                "FILE_RECORDS": 601,
                "^IMAGE": 2,
                "IMAGE": PVLObject(
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
            self.assertEqual(self.simplePVL, pvln.load(f))

    def test_load_w_Path(self):
        self.assertEqual(self.simplePVL, pvln.load(self.simple))

    def test_load_w_string_path(self):
        string_path = str(self.simple)
        self.assertEqual(self.simplePVL, pvln.load(string_path))

    def test_loadu(self):
        self.assertEqual(self.simplePVL, pvln.loadu(self.url))
        self.assertEqual(
            self.simplePVL, pvln.loadu(self.simple.resolve().as_uri())
        )

    @patch("pvl.new.loads")
    @patch("pvl.new.decode_by_char")
    def test_loadu_args(self, m_decode, m_loads):
        pvln.loadu(self.url, data=None)
        pvln.loadu(self.url, noturlopen="should be passed to loads")
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
            label = pvln.load(
                pvl_file, decoder=OmniDecoder(quantity_cls=u.Quantity)
            )
            self.assertEqual(label["FLOAT_UNIT"], u.Quantity(0.414, "KM"))
        except ImportError:
            pass


class TestISIScub(unittest.TestCase):
    def setUp(self):
        self.cub = data_dir / "pattern.cub"
        self.cubpvl = PVLModule(
            IsisCube=PVLObject(
                Core=PVLObject(
                    StartByte=65537,
                    Format="Tile",
                    TileSamples=128,
                    TileLines=128,
                    Dimensions=PVLGroup(Samples=90, Lines=90, Bands=1),
                    Pixels=PVLGroup(
                        Type="Real", ByteOrder="Lsb", Base=0.0, Multiplier=1.0
                    ),
                )
            ),
            Label=PVLObject(Bytes=65536),
        )

    def test_load_cub(self):
        self.assertEqual(self.cubpvl, pvln.load(self.cub))

    def test_load_cub_opened(self):
        with open(self.cub, "rb") as f:
            self.assertEqual(self.cubpvl, pvln.load(f))


class TestDumpS(unittest.TestCase):
    def setUp(self):
        self.module = PVLModule(
            a="b",
            staygroup=PVLGroup(c="d"),
            obj=PVLGroup(d="e", f=PVLGroup(g="h")),
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
        self.assertEqual(s, pvln.dumps(self.module))

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
            s, pvln.dumps(
                self.module,
                encoder=pvl.encoder.PVLEncoder(
                    group_class=PVLGroup, object_class=PVLObject
                )
            )
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
            s, pvln.dumps(self.module, encoder=pvl.encoder.ODLEncoder(
                group_class=PVLGroup, object_class=PVLObject
            ))
        )


class TestDump(unittest.TestCase):
    def setUp(self):
        self.module = PVLModule(
            a="b",
            staygroup=PVLGroup(c="d"),
            obj=PVLGroup(d="e", f=PVLGroup(g="h")),
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
        with patch("pvl.new.Path", autospec=True, return_value=mock_path):
            pvln.dump(self.module, Path("dummy"))
            self.assertEqual(
                [call.write_text(self.string)], mock_path.method_calls
            )

    @patch("builtins.open", mock_open())
    def test_dump_file_object(self):
        with open("dummy", "w") as f:
            pvln.dump(self.module, f)
            self.assertEqual(
                [call.write(self.string.encode())], f.method_calls
            )

    def test_not_dumpable(self):
        f = 5
        self.assertRaises(TypeError, pvln.dump, self.module, f)
