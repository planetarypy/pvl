# -*- coding: utf-8 -*-
import os
import glob
import io
import tempfile
import shutil
import pytest
import pvl


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data/')
PDS_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'pds3')
PDS_LABELS = glob.glob(os.path.join(PDS_DATA_DIR, "*.lbl"))


def test_dump_stream():
    for filename in PDS_LABELS:
        label = pvl.load(filename)
        stream = io.BytesIO()
        pvl.dump(label, stream)
        stream.seek(0)
        assert label == pvl.load(stream)


def test_dump_to_file():
    tmpdir = tempfile.mkdtemp()

    try:
        for filename in PDS_LABELS:
            label = pvl.load(filename)
            tmpfile = os.path.join(tmpdir, os.path.basename(filename))
            pvl.dump(label, tmpfile)
            assert label == pvl.load(tmpfile)
    finally:
        shutil.rmtree(tmpdir)


def test_default_encoder():
    for filename in PDS_LABELS:
        label = pvl.load(filename)
        assert label == pvl.loads(pvl.dumps(label))


def test_cube_encoder():
    for filename in PDS_LABELS:
        label = pvl.load(filename)
        encoder = pvl.encoder.IsisCubeLabelEncoder
        assert label == pvl.loads(pvl.dumps(label, cls=encoder))


def test_pds_encoder():
    for filename in PDS_LABELS:
        label = pvl.load(filename)
        encoder = pvl.encoder.PDSLabelEncoder
        assert label == pvl.loads(pvl.dumps(label, cls=encoder))


def test_special_values():
    module = pvl.PVLModule([
        ('bool_true', True),
        ('bool_false', False),
        ('null', None),
    ])
    assert module == pvl.loads(pvl.dumps(module))

    encoder = pvl.encoder.IsisCubeLabelEncoder
    assert module == pvl.loads(pvl.dumps(module, cls=encoder))

    encoder = pvl.encoder.PDSLabelEncoder
    assert module == pvl.loads(pvl.dumps(module, cls=encoder))


def test_special_strings():
    module = pvl.PVLModule([
        ('single_quote', "'"),
        ('double_quote', '"'),
        ('mixed_quotes', '"\''),
    ])
    assert module == pvl.loads(pvl.dumps(module))

    encoder = pvl.encoder.IsisCubeLabelEncoder
    assert module == pvl.loads(pvl.dumps(module, cls=encoder))

    encoder = pvl.encoder.PDSLabelEncoder
    assert module == pvl.loads(pvl.dumps(module, cls=encoder))


def test_unkown_value():
    class UnknownType(object):
        pass

    with pytest.raises(TypeError):
        pvl.dumps({'foo': UnknownType()})


def test_quoated_strings():
    module = pvl.PVLModule([
        ('int_like', "123"),
        ('float_like', '.2'),
        ('date', '1987-02-25'),
        ('time', '03:04:05'),
        ('datetime', '1987-02-25T03:04:05'),
        ('keyword', 'END'),
        ('restricted_chars', '&<>\'{},[]=!#()%";|'),
        ('restricted_seq', '/**/'),
    ])
    assert module == pvl.loads(pvl.dumps(module))

    encoder = pvl.encoder.IsisCubeLabelEncoder
    assert module == pvl.loads(pvl.dumps(module, cls=encoder))

    encoder = pvl.encoder.PDSLabelEncoder
    assert module == pvl.loads(pvl.dumps(module, cls=encoder))


def test_dump_to_file_insert_before():
    tmpdir = tempfile.mkdtemp()

    try:
        for filename in PDS_LABELS:
            label = pvl.load(filename)
            if os.path.basename(filename) != 'empty.lbl':
                label.insert_before('PDS_VERSION_ID', [('new', 'item')])
            tmpfile = os.path.join(tmpdir, os.path.basename(filename))
            pvl.dump(label, tmpfile)
            assert label == pvl.load(tmpfile)
    finally:
        shutil.rmtree(tmpdir)


def test_dump_to_file_insert_after():
    tmpdir = tempfile.mkdtemp()

    try:
        for filename in PDS_LABELS:
            label = pvl.load(filename)
            if os.path.basename(filename) != 'empty.lbl':
                label.insert_after('PDS_VERSION_ID', [('new', 'item')])
            tmpfile = os.path.join(tmpdir, os.path.basename(filename))
            pvl.dump(label, tmpfile)
            assert label == pvl.load(tmpfile)
    finally:
        shutil.rmtree(tmpdir)
