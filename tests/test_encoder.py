# -*- coding: utf-8 -*-
import os
import glob
import pvl


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data/')
PDS_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'pds3')


def test_dump():
    files = glob.glob(os.path.join(PDS_DATA_DIR, "*.lbl"))

    for infile in files:
        label = pvl.load(infile)
        assert label == pvl.loads(pvl.dumps(label))
