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

from pathlib import Path

import pvl

data_dir = Path('tests/data')


class TestLoadS(unittest.TestCase):

    def test_loads(self):
        some_pvl = '''
a = b
GROUP = c
    c = d
END_GROUP
e =false
END'''
        decoded = pvl.PVLModule(a='b', c=pvl.PVLGroup(c='d'), e=False)
        self.assertEqual(decoded, pvl.loads(some_pvl))


class TestLoad(unittest.TestCase):

    def setUp(self):
        self.simple = data_dir / 'pds3' / 'simple_image_1.lbl'
        self.simplePVL = pvl.PVLModule(
            {'PDS_VERSION_ID': 'PDS3',
             'RECORD_TYPE': 'FIXED_LENGTH',
             'RECORD_BYTES': 824,
             'LABEL_RECORDS': 1,
             'FILE_RECORDS': 601,
             '^IMAGE': 2,
             'IMAGE': pvl.PVLObject({'LINES': 600,
                                     'LINE_SAMPLES': 824,
                                     'SAMPLE_TYPE': 'MSB_INTEGER',
                                     'SAMPLE_BITS': 8,
                                     'MEAN': 51.67785396440129,
                                     'MEDIAN': 50.0,
                                     'MINIMUM': 0,
                                     'MAXIMUM': 255,
                                     'STANDARD_DEVIATION': 16.97019,
                                     'CHECKSUM': 25549531})})

    def test_load_w_open(self):
        with open(self.simple) as f:
            self.assertEqual(self.simplePVL, pvl.load(f))

    def test_load_w_Path(self):
        self.assertEqual(self.simplePVL, pvl.load(self.simple))

    def test_load_w_string_path(self):
        string_path = str(self.simple)
        self.assertEqual(self.simplePVL, pvl.load(string_path))


class TestISIScub(unittest.TestCase):

    def setUp(self):
        self.cub = data_dir / 'pattern.cub'
        self.cubpvl = pvl.PVLModule(
            IsisCube=pvl.PVLObject(
                Core=pvl.PVLObject(StartByte=65537,
                                   Format='Tile',
                                   TileSamples=128,
                                   TileLines=128,
                                   Dimensions=pvl.PVLGroup(Samples=90,
                                                           Lines=90,
                                                           Bands=1),
                                   Pixels=pvl.PVLGroup(Type='Real',
                                                       ByteOrder='Lsb',
                                                       Base=0.0,
                                                       Multiplier=1.0))),
            Label=pvl.PVLObject(Bytes=65536))

    def test_load_cub(self):
        self.assertEqual(self.cubpvl, pvl.load(self.cub))
