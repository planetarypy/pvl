# -*- coding: utf-8 -*-
import os
import io
import datetime
import glob
import pytest

import pvl
from pvl import (
    Label,
    LabelGroup,
    LabelObject,
    Units
)


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data/')
PDS_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'pds3')
PDS_LABELS = glob.glob(os.path.join(PDS_DATA_DIR, "*.lbl"))
BROKEN_DIR = os.path.join('tests', 'data', 'pds3', 'broken')
BAD_PDS_LABELS = glob.glob(os.path.join(BROKEN_DIR, "*.lbl"))


def test_assignment():
    label = pvl.loads('foo=bar')
    assert isinstance(label, Label)
    assert label['foo'] == 'bar'

    label = pvl.loads('Group_Foo=bar')
    assert isinstance(label, Label)
    assert label['Group_Foo'] == 'bar'

    label = pvl.loads('foo=bar-')
    assert isinstance(label, Label)
    assert label['foo'] == 'bar-'

    label = pvl.loads('foo=bar-\n')
    assert isinstance(label, Label)
    assert label['foo'] == 'bar-'


def test_spacing():
    label = pvl.loads("""
        foo = bar
        nospace=good
          lots_of_spacing    =    alsogood
        same = line no = problem; like=aboss
        End
    """)

    assert isinstance(label, Label)
    assert label['foo'] == 'bar'
    assert label['nospace'] == 'good'
    assert label['lots_of_spacing'] == 'alsogood'
    assert label['same'] == 'line'
    assert label['no'] == 'problem'
    assert label['like'] == 'aboss'


def test_linewrap():
    label = pvl.loads("""
        foo = bar-
              baz
        End
    """)

    assert label['foo'] == 'barbaz'


def test_special():
    label = pvl.loads("""
        none1 = NULL
        none2 = Null
        true1 = TRUE
        true2 = True
        true3 = true
        false1 = FALSE
        false2 = False
        false3 = false
        End
    """)

    assert label['none1'] is None
    assert label['none2'] is None

    assert label['true1'] is True
    assert label['true2'] is True
    assert label['true3'] is True

    assert label['false1'] is False
    assert label['false2'] is False
    assert label['false3'] is False


def test_integers():
    label = pvl.loads("""
        integer = 42
        positive_integer = +123
        negitive_integer = -1
        invalid_integer = 1a2
        End
    """)

    assert isinstance(label['integer'], int)
    assert label['integer'] == 42

    assert isinstance(label['integer'], int)
    assert label['positive_integer'] == 123

    assert isinstance(label['negitive_integer'], int)
    assert label['negitive_integer'] == -1

    assert isinstance(label['invalid_integer'], str)
    assert label['invalid_integer'] == '1a2'


def test_floats():
    label = pvl.loads("""
        float = 1.0
        float_no_decimal = 2.
        float_no_whole = .3
        float_leading_zero = 0.5
        positive_float = +2.0
        negative_float = -1.0
        invalid_float = 1.2.3
        End
    """)
    assert isinstance(label['float'], float)
    assert label['float'] == 1.0

    assert isinstance(label['float_no_decimal'], float)
    assert label['float_no_decimal'] == 2.0

    assert isinstance(label['float_no_whole'], float)
    assert label['float_no_whole'] == 0.3

    assert isinstance(label['float_leading_zero'], float)
    assert label['float_leading_zero'] == 0.5

    assert isinstance(label['positive_float'], float)
    assert label['positive_float'] == 2.0

    assert isinstance(label['negative_float'], float)
    assert label['negative_float'] == -1.0

    assert isinstance(label['invalid_float'], str)
    assert label['invalid_float'] == '1.2.3'


def test_exponents():
    label = pvl.loads("""
        capital = -1.E-3
        lower = -1.e-3
        small = -0.45e6
        int = 31459e1
        invalid = 1e
        End
    """)

    assert isinstance(label['capital'], float)
    assert label['capital'] == -1.0E-3

    assert isinstance(label['lower'], float)
    assert label['lower'] == -1.0E-3

    assert isinstance(label['small'], float)
    assert label['small'] == -0.45E6

    assert isinstance(label['int'], float)
    assert label['int'] == 31459e1

    assert isinstance(label['invalid'], str)
    assert label['invalid'] == '1e'


def test_objects():
    label = pvl.loads("""
        Object = test_object
          foo = bar

          Object = embedded_object
            foo = bar
          End_Object

          Group = embedded_group
            foo = bar
          End_Group
        End_Object
        End
    """)
    test_object = label['test_object']
    assert isinstance(test_object, LabelObject)
    assert test_object['foo'] == 'bar'

    embedded_object = test_object['embedded_object']
    assert isinstance(embedded_object, LabelObject)
    assert embedded_object['foo'] == 'bar'

    embedded_group = test_object['embedded_group']
    assert isinstance(embedded_group, LabelGroup)
    assert embedded_group['foo'] == 'bar'

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads("""
            BEGIN_OBJECT = foo
            END_OBJECT = bar
        """)


def test_groups():
    label = pvl.loads("""
        Group = test_group
          foo = bar
          Object = embedded_object
            foo = bar
          End_Object

          Group = embedded_group
            foo = bar
          End_Group
        End_Group
        End
    """)
    test_group = label['test_group']
    assert isinstance(test_group, LabelGroup)
    assert test_group['foo'] == 'bar'

    embedded_object = test_group['embedded_object']
    assert isinstance(embedded_object, LabelObject)
    assert embedded_object['foo'] == 'bar'

    embedded_group = test_group['embedded_group']
    assert isinstance(embedded_group, LabelGroup)
    assert embedded_group['foo'] == 'bar'

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads("""
            BEGIN_GROUP = foo
            END_GROUP = bar
        """)


def test_alt_group_style():
    label = pvl.loads("""
        OBJECT               = TEST1
          FOO                = BAR
        END_OBJECT           = TEST1

        GROUP                = TEST2
          FOO                = BAR
        END_GROUP            = TEST2

        END
    """)
    test_group = label['TEST1']
    assert isinstance(test_group, LabelObject)
    assert test_group['FOO'] == 'BAR'

    embedded_object = label['TEST2']
    assert isinstance(embedded_object, LabelGroup)
    assert embedded_object['FOO'] == 'BAR'


def test_binary():
    label = pvl.loads("""
        binary_number = 2#0101#
        positive_binary_number = +2#0101#
        negative_binary_number = -2#0101#
        End
    """)

    assert isinstance(label['binary_number'], int)
    assert label['binary_number'] == 5

    assert isinstance(label['positive_binary_number'], int)
    assert label['positive_binary_number'] == 5

    assert isinstance(label['negative_binary_number'], int)
    assert label['negative_binary_number'] == -5

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads('empty = 2##')

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads('binary_number = 2#0101')

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads('binary_number = 2#01014201#')


def test_octal():
    label = pvl.loads("""
        octal_number = 8#0107#
        positive_octal_number = +8#0107#
        negative_octal_number = -8#0107#
        End
    """)

    assert isinstance(label['octal_number'], int)
    assert label['octal_number'] == 71

    assert isinstance(label['positive_octal_number'], int)
    assert label['positive_octal_number'] == 71

    assert isinstance(label['negative_octal_number'], int)
    assert label['negative_octal_number'] == -71

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads('empty = 8##')

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads('octal_number = 8#0107')

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads('octal_number = 8#01079#')


def test_hex():
    label = pvl.loads("""
        hex_number_upper = 16#100A#
        hex_number_lower = 16#100b#
        positive_hex_number = +16#100A#
        negative_hex_number = -16#100A#
        End
    """)

    assert isinstance(label['hex_number_upper'], int)
    assert label['hex_number_upper'] == 4106

    assert isinstance(label['hex_number_lower'], int)
    assert label['hex_number_lower'] == 4107

    assert isinstance(label['positive_hex_number'], int)
    assert label['positive_hex_number'] == 4106

    assert isinstance(label['negative_hex_number'], int)
    assert label['negative_hex_number'] == -4106

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads('empty = 16##')

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads('hex_number_upper = 16#100A')

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads('hex_number_upper = 16#100AZ#')


# I think the mixed test here is wrong.  The single quote before 'quotes'
# should terminate the quoted string.  I think the idea here was suppsed to
# be that the \\ escaped a slash, and then that left you with the following
# two character sequence: "\'", which was meant to be interpreted as an
# 'escaped' quote which shouldn't terminate the quoted string, but
# PVL doesn't 'escape' characters, even though Python does.  So
# to PVL, its a slash (which is in the PVL unrestricted character set),
# followed by a single quote, which properly terminates the quoted string,
# and then there's an unparseable "quotes'" after it that should cause an
# error.
#        mixed = 'mixed"\\'quotes'

def test_quotes():
    label = pvl.loads("""
        foo = 'bar'
        empty = ''
        space = '  test  '
        double = "double'quotes"
        single = 'single"quotes'
        number = '123'
        date = '1918-05-11'
        multiline = 'this is a
                     multi-line string'
        continuation = "The planet Jupi-
                        ter is very big"
        """)
#         formating = "\\n\\t\\f\\v\\\\\\n\\t\\f\\v\\\\"
#         End
#         """)

    assert isinstance(label['foo'], str)
    assert label['foo'] == 'bar'

    assert isinstance(label['empty'], str)
    assert label['empty'] == ''

    assert isinstance(label['space'], str)
    # This test is incorrect, since the whitespace is quoted, it should
    # not be collapsed.
    # assert label['space'] == 'test'
    assert label['space'] == '  test  '

    assert isinstance(label['double'], str)
    assert label['double'] == "double'quotes"

    assert isinstance(label['single'], str)
    assert label['single'] == 'single"quotes'

    # assert isinstance(label['single'], str)
    # assert label['mixed'] == 'mixed"\'quotes'

    assert isinstance(label['number'], str)
    assert label['number'] == '123'

    assert isinstance(label['date'], str)
    assert label['date'] == '1918-05-11'

    # This test is really for ODL-only, PVL will retain the newline and space.
    assert isinstance(label['multiline'], str)
    assert label['multiline'] == 'this is a multi-line string'

    # Also for ODL-only, but tests the OmniDecoder
    assert isinstance(label['continuation'], str)
    assert label['continuation'] == 'The planet Jupiter is very big'

    # Come back to this one
    # assert isinstance(label['formating'], str)
    # assert label['formating'] == '\n\t\f\v\\\n\t\f\v\\'

    # The quote after the equals here starts a quoted string, but
    # it doesn't complete, and therefore there's no assignment to foo.
    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads('foo = "bar')

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads("foo = 'bar")

    # The \b character is not an allowed PVL character.
    with pytest.raises(pvl.lexer.LexerError):
        # pvl.loads("foo = '\\bar'")
        pvl.loads("foo = '\bar'")


def test_comments():
    some_pvl = ("""
        /* comment on line */
        # here is a line comment
        /* here is a multi-
        line comment */
        foo = bar /* comment at end of line */
        weird/* in the */=/*middle*/comments
        baz = bang # end line comment
        End
    """)

    # Strict PVL doesn't allow #-comments
    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads(some_pvl, grammar=pvl.grammar.grammar())

    # Fortunately, we use the Omnigrammar as the default.
    label = pvl.loads(some_pvl)

    assert len(label) == 3

    assert isinstance(label['foo'], str)
    assert label['foo'] == 'bar'

    assert isinstance(label['foo'], str)
    assert label['weird'] == 'comments'

    assert isinstance(label['foo'], str)
    assert label['baz'] == 'bang'

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads(b'/*')


def test_dates():
    some_pvl = ("""
        date1          = 1990-07-04
        date2          = 1990-158
        date3          = 2001-001
        date4          = 2001-01-01
        time1          = 12:00
        time_s         = 12:00:45
        time_s_float   = 12:00:45.4571
        time_tz1       = 15:24:12Z
        time_tz2       = 01:12:22+07
        time_tz3       = 01:12:22+7
        time_tz4       = 01:10:39.4575+07
        datetime1      = 1990-07-04T12:00
        datetime2      = 1990-158T15:24:12Z
        datetime3      = 2001-001T01:10:39+7
        datetime4      = 2001-001T01:10:39.457591+7
        End
    """)

    # PVL doesn't allow numeric TZ offsets, like "+07"
    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads(some_pvl, decoder=pvl.decoder.PVLDecoder())

    # But ODL, and the OmniDecoder do:
    label = pvl.loads(some_pvl)

    try:
        from dateutil import tz

        tz_plus_7 = tz.tzoffset('+7', datetime.timedelta(hours=7))

        assert isinstance(label['date1'], datetime.date)
        assert label['date1'] == datetime.date(1990, 7, 4)

        assert isinstance(label['date2'], datetime.date)
        assert label['date2'] == datetime.date(1990, 6, 7)

        assert isinstance(label['date3'], datetime.date)
        assert label['date3'] == datetime.date(2001, 1, 1)

        assert isinstance(label['date4'], datetime.date)
        assert label['date4'] == datetime.date(2001, 1, 1)

        assert isinstance(label['time1'], datetime.time)
        assert label['time1'] == datetime.time(12)

        assert isinstance(label['time_s'], datetime.time)
        assert label['time_s'] == datetime.time(12, 0, 45)

        assert isinstance(label['time_s_float'], datetime.time)
        assert label['time_s_float'] == datetime.time(12, 0, 45, 457100)

        assert isinstance(label['time_tz1'], datetime.time)
        assert label['time_tz1'] == datetime.time(15, 24, 12)

        assert isinstance(label['time_tz2'], datetime.time)
        assert label['time_tz2'] == datetime.time(1, 12, 22, tzinfo=tz_plus_7)

        assert isinstance(label['time_tz3'], datetime.time)
        assert label['time_tz3'] == datetime.time(1, 12, 22, tzinfo=tz_plus_7)

        assert isinstance(label['time_tz4'], datetime.time)
        assert label['time_tz4'] == datetime.time(1, 10, 39, 457500,
                                                  tzinfo=tz_plus_7)

        assert isinstance(label['datetime1'], datetime.datetime)
        assert label['datetime1'] == datetime.datetime(1990, 7, 4, 12)

        assert isinstance(label['datetime2'], datetime.datetime)
        assert label['datetime2'] == datetime.datetime(1990, 6, 7, 15, 24, 12)

        assert isinstance(label['datetime3'], datetime.datetime)
        assert label['datetime3'] == datetime.datetime(2001, 1, 1, 1, 10, 39,
                                                       tzinfo=tz_plus_7)

        assert isinstance(label['datetime4'], datetime.datetime)
        assert label['datetime4'] == datetime.datetime(2001, 1, 1, 1, 10, 39,
                                                       457591,
                                                       tzinfo=tz_plus_7)

    except ImportError:
        assert label['date1'] == '1990-07-04'
        assert label['date2'] == '1990-158'
        assert label['date3'] == '2001-001'
        assert label['date4'] == '2001-01-01'
        assert label['time1'] == '12:00'
        assert label['time_s'] == '12:00:45'
        assert label['time_s_float'] == '12:00:45.4571'
        assert label['time_tz1'] == '15:24:12Z'
        assert label['time_tz2'] == '01:12:22+07'
        assert label['time_tz3'] == '01:12:22+7'
        assert label['time_tz4'] == '01:10:39.4575+07'
        assert label['datetime1'] == '1990-07-04T12:00'
        assert label['datetime2'] == '1990-158T15:24:12Z'
        assert label['datetime3'] == '2001-001T01:10:39+7'
        assert label['datetime4'] == '2001-001T01:10:39.457591+7'


def test_set():
    label = pvl.loads("""
        strings = {a, b, c}
        nospace={a,b,c}
        numbers = {1, 2, 3}
        mixed = {a, 1, 2.5}
        multiline = {a,
                     b,
                     c}
        empty = {}
        End
    """)

    # sets are non-hashable, so pvl is now returning frozensets
    # assert isinstance(label['strings'], set)
    assert isinstance(label['strings'], frozenset)
    assert len(label['strings']) == 3
    assert 'a' in label['strings']
    assert 'b' in label['strings']
    assert 'c' in label['strings']

    # assert isinstance(label['nospace'], set)
    assert isinstance(label['nospace'], frozenset)
    assert len(label['nospace']) == 3
    assert 'a' in label['nospace']
    assert 'b' in label['nospace']
    assert 'c' in label['nospace']

    # assert isinstance(label['numbers'], set)
    assert isinstance(label['numbers'], frozenset)
    assert len(label['numbers']) == 3
    assert 1 in label['numbers']
    assert 2 in label['numbers']
    assert 3 in label['numbers']

    # assert isinstance(label['mixed'], set)
    assert isinstance(label['mixed'], frozenset)
    assert len(label['mixed']) == 3
    assert 'a' in label['mixed']
    assert 1 in label['mixed']
    assert 2.5 in label['mixed']

    # assert isinstance(label['multiline'], set)
    assert isinstance(label['multiline'], frozenset)
    assert len(label['multiline']) == 3
    assert 'a' in label['multiline']
    assert 'b' in label['multiline']
    assert 'c' in label['multiline']

    # assert isinstance(label['empty'], set)
    assert isinstance(label['empty'], frozenset)
    assert len(label['empty']) == 0


def test_sequence():
    label = pvl.loads("""
        strings = (a, b, c)
        nospace=(a,b,c)
        numbers = (1, 2, 3)
        mixed = (a, 1, 2.5)
        empty = ()
        multiline = (a,
                     b,
                     c)
        End
    """)

    assert isinstance(label['strings'], list)
    assert len(label['strings']) == 3
    assert label['strings'][0] == 'a'
    assert label['strings'][1] == 'b'
    assert label['strings'][2] == 'c'

    assert isinstance(label['nospace'], list)
    assert len(label['nospace']) == 3
    assert label['nospace'][0] == 'a'
    assert label['nospace'][1] == 'b'
    assert label['nospace'][2] == 'c'

    assert isinstance(label['numbers'], list)
    assert len(label['numbers']) == 3
    assert label['numbers'][0] == 1
    assert label['numbers'][1] == 2
    assert label['numbers'][2] == 3

    assert isinstance(label['mixed'], list)
    assert len(label['mixed']) == 3
    assert label['mixed'][0] == 'a'
    assert label['mixed'][1] == 1
    assert label['mixed'][2] == 2.5

    assert isinstance(label['empty'], list)
    assert len(label['empty']) == 0

    assert isinstance(label['multiline'], list)
    assert len(label['multiline']) == 3
    assert label['multiline'][0] == 'a'
    assert label['multiline'][1] == 'b'
    assert label['multiline'][2] == 'c'


def test_units():
    label = pvl.loads("""
        foo = 42 <beards>
        g = 9.8 <m/s>
        list = (1, 2, 3) <numbers>
        cool = (1 <number>)
        End
    """)
    assert isinstance(label['foo'], Units)
    assert label['foo'].value == 42
    assert label['foo'].units == 'beards'

    assert isinstance(label['g'], Units)
    assert label['g'].value == 9.8
    assert label['g'].units == 'm/s'

    assert isinstance(label['list'], Units)
    assert isinstance(label['list'].value, list)
    assert label['list'].units == 'numbers'

    assert isinstance(label['cool'], list)
    assert isinstance(label['cool'][0], Units)
    assert label['cool'][0].value == 1
    assert label['cool'][0].units == 'number'

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads(b'foo = bar <')


def test_delimiters():
    label = pvl.loads("""
        foo = 1;
        Object = embedded_object;
          foo = bar;
        End_Object;
        bar = 2;
        Group = embedded_group;
          foo = bar;
        End_Group;
        End;
    """)

    assert isinstance(label, Label)
    assert label['foo'] == 1
    assert label['bar'] == 2

    assert isinstance(label['embedded_object'], LabelObject)
    assert label['embedded_object']['foo'] == 'bar'

    assert isinstance(label['embedded_group'], LabelGroup)
    assert label['embedded_group']['foo'] == 'bar'


def test_cube_label():
    with open(os.path.join(DATA_DIR, 'pattern.cub'), 'rb') as fp:
        label = pvl.load(fp)

    assert isinstance(label['Label'], dict)
    assert label['Label']['Bytes'] == 65536

    assert isinstance(label['IsisCube'], dict)
    assert isinstance(label['IsisCube']['Core'], dict)
    assert label['IsisCube']['Core']['StartByte'] == 65537
    assert label['IsisCube']['Core']['Format'] == 'Tile'
    assert label['IsisCube']['Core']['TileSamples'] == 128
    assert label['IsisCube']['Core']['TileLines'] == 128

    assert isinstance(label['IsisCube']['Core']['Dimensions'], dict)
    assert label['IsisCube']['Core']['Dimensions']['Samples'] == 90
    assert label['IsisCube']['Core']['Dimensions']['Lines'] == 90
    assert label['IsisCube']['Core']['Dimensions']['Bands'] == 1

    assert isinstance(label['IsisCube']['Core']['Pixels'], dict)
    assert label['IsisCube']['Core']['Pixels']['Type'] == 'Real'
    assert label['IsisCube']['Core']['Pixels']['ByteOrder'] == 'Lsb'
    assert label['IsisCube']['Core']['Pixels']['Base'] == 0.0
    assert label['IsisCube']['Core']['Pixels']['Multiplier'] == 1.0


def test_pds3_sample_image():
    infile = os.path.join(PDS_DATA_DIR, "simple_image_1.lbl")
    label = pvl.load(infile)
    assert label['RECORD_TYPE'] == 'FIXED_LENGTH'
    assert label['RECORD_BYTES'] == 824
    assert label['LABEL_RECORDS'] == 1
    assert label['FILE_RECORDS'] == 601
    assert label['IMAGE']['LINES'] == 600
    assert label['IMAGE']['LINE_SAMPLES'] == 824
    image_group = label['IMAGE']
    assert image_group['SAMPLE_TYPE'] == 'MSB_INTEGER'
    assert image_group['SAMPLE_BITS'] == 8
    assert abs(image_group['MEAN'] - 51.6778539644) <= 0.00001
    assert image_group['MEDIAN'] == 50.0
    assert image_group['MINIMUM'] == 0
    assert image_group['MAXIMUM'] == 255
    assert image_group['STANDARD_DEVIATION'] == 16.97019
    assert image_group['CHECKSUM'] == 25549531


def test_load_all_sample_labels():
    for filename in PDS_LABELS:
        label = pvl.load(filename)
        assert isinstance(label, Label)


def test_unicode():
    label = pvl.loads(u'foo=bar')
    assert isinstance(label, Label)
    assert label['foo'] == 'bar'


def test_bytes():
    label = pvl.loads(b'foo=bar')
    assert isinstance(label, Label)
    assert label['foo'] == 'bar'


def test_end_comment():
    label = pvl.loads(b'END/* commnet */')
    assert isinstance(label, Label)
    assert len(label) == 0


def test_parse_error():
    with pytest.raises(pvl.parser.ParseError):
        pvl.loads(b'foo=', parser=pvl.PVLParser())

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads(b'=')

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads(b'(}')

    # Identical with above?
    # with pytest.raises(pvl.decoder.ParseError):
    #     pvl.loads(b'foo=')

    with pytest.raises(pvl.lexer.LexerError):
        pvl.loads(b'foo=!')

    with pytest.raises(pvl.parser.ParseError):
        pvl.loads(b'foo')

    with pytest.raises(pvl.parser.ParseError):
        pvl.load(io.BytesIO(b'foo'))


EV = pvl.decoder.EmptyValueAtLine


@pytest.mark.parametrize(
    'label, expected, expected_errors',
    [
        (
            'broken1.lbl',
            [('foo', 'bar'), ('life', EV(2)), ('monty', 'python')],
            [2]
        ),
        (  # ParseError
            'broken2.lbl',
            [('foo', 'bar'), ('life', EV(2))],
            [2]
        ),
        (
            'broken3.lbl',
            [('foo', EV(1)), ('life', 42)],
            [1]
        ),
        (
            'broken4.lbl',
            [('foo', 'bar'), ('life', EV(2)), ('monty', EV(3))],
            [2, 3]
        ),
        (
            'broken5.lbl',
            [('foo', EV(1)), ('life', EV(2)), ('monty', 'python')],
            [1, 2]
        ),
        (
            'broken6.lbl',
            [('foo', EV(1)), ('life', EV(1)), ('monty', EV(1))],
            [1, 2, 3]
        ),
        (
            'broken7.lbl',
            [
                ('foo', 1),
                ('embedded_object', pvl.PVLObject(
                    [('foo', 'bar'), ('life', EV(1))]))
            ],
            [4]
        ),
        (
            'broken8.lbl',
            [
                ('foo', 1),
                ('embedded_group', pvl.PVLGroup(
                    [('foo', 'bar'), ('life', EV(1))]))
            ],
            [4]
        ),
        (
            'broken9.lbl',
            [('foo', 42), ('bar', EV(1))],
            [2]
        ),
        (
            'broken10.lbl',
            [('foo', Units(42, 'beards')), ('cool', EV(1))],
            [2]
        ),
        (
            'broken11.lbl',
            [('foo', EV(1)), ('cool', [Units(1, 'beards')])],
            [1]
        ),
        (
            'broken12.lbl',
            [
                ('strs', ['a', 'b']),
                ('empty', EV(2)), ('multiline', ['a', 'b'])
            ],
            [2]
        ),
        (
            'broken13.lbl',
            [
                ('same', 'line'),
                ('no', 'problem'),
                ('foo', EV(1)), ('bar', EV(2))
            ],
            [1, 2]
        ),
        (
            'broken14.lbl',
            [('foo', 'bar'), ('weird', EV(3)), ('baz', 'bang')],
            [3]
        ),
        (
            'broken15.lbl',
            [('foo', 'bar'), ('weird', 'comment'), ('baz', EV(4))],
            [4]
        ),
        (
            'broken16.lbl',
            [('foo', EV(2)), ('weird', 'comment'), ('baz', 'bang')],
            [2]
        ),
    ])
def test_broken_labels(label, expected, expected_errors):
    with open(os.path.join(BROKEN_DIR, label), 'rb') as stream:
        module = pvl.load(stream)

    expected = pvl.PVLModule(expected)

    # This isn't a deep comparison, since all EmptyValueAtLine
    # are empty strings, regardless of their .lineno value, they
    # always compare equal.
    assert module == expected

    # But this should compare the 'line numbers' of the EmptyValueAtLines
    assert module.errors == expected_errors
    assert not module.valid


@pytest.mark.parametrize(
    'label', ['broken1.lbl',
              # 'broken2.lbl',  # moved to test_broken_labels_ParseError
              'broken3.lbl', 'broken4.lbl', 'broken5.lbl',
              'broken6.lbl', 'broken7.lbl', 'broken8.lbl',
              'broken9.lbl', 'broken10.lbl', 'broken11.lbl',
              'broken12.lbl', 'broken13.lbl', 'broken14.lbl',
              'broken15.lbl', 'broken16.lbl'])
def test_broken_labels_LexerError(label):
    with open(os.path.join(BROKEN_DIR, label), 'rb') as stream:
        # with pytest.raises(pvl.decoder.ParseError):
        with pytest.raises(pvl.lexer.LexerError):
            pvl.load(stream, parser=pvl.PVLParser())


def test_broken_labels_ParseError():
    with open(os.path.join(BROKEN_DIR, 'broken2.lbl'), 'rb') as stream:
        with pytest.raises(pvl.parser.ParseError):
            pvl.load(stream, parser=pvl.PVLParser())


def test_EmptyValueAtLine():
    test_ev = pvl.decoder.EmptyValueAtLine(1)
    assert test_ev == ''
    assert 'foo' + test_ev == 'foo'
    assert isinstance(test_ev, str)
    assert test_ev.lineno == 1
    assert int(test_ev) == 0
    assert float(test_ev) == 0.0
    trep = (
        'EmptyValueAtLine(1 does not have a value. Treat as an empty string)'
    )
    assert repr(test_ev) == trep


def test_load_all_bad_sample_labels():
    for filename in BAD_PDS_LABELS:
        label = pvl.load(filename)
        assert isinstance(label, Label)


def test_dump_stream():
    for filename in PDS_LABELS:
        # print(filename)
        label = pvl.load(filename)
        # print(label)
        stream = io.BytesIO()

        if('tests/data/pds3/set1.lbl' in filename or  # float in set
           'tests/data/pds3/set2.lbl' in filename or  # float in set
           'tests/data/pds3/dates.lbl' in filename):  # tz in dates
            # The default PDSLabelEncoder will refuse to
            # write out floating point values into sets,
            # or datetimes with non-UTC timezones,
            # but the ODLEncoder will:
            pvl.dump(label, stream, cls=pvl.encoder.ODLEncoder)
            stream.seek(0)
            assert label == pvl.load(stream)

            with pytest.raises(ValueError):
                pvl.dump(label, stream)

        else:
            pvl.dump(label, stream)
            stream.seek(0)
            # assert label == pvl.load(stream)
            s = pvl.load(stream)
            if 'tests/data/pds3/float1.lbl' in filename:
                # FlOAT not FLOAT, see test below
                assert label != s
            else:
                assert label == s

# def test_dump_to_file():
#     tmpdir = tempfile.mkdtemp()
#
#     try:
#         for filename in PDS_LABELS:
#             label = pvl.load(filename)
#             tmpfile = os.path.join(tmpdir, os.path.basename(filename))
#             pvl.dump(label, tmpfile)
#             assert label == pvl.load(tmpfile)
#     finally:
#         shutil.rmtree(tmpdir)


# def test_default_encoder():
#     for filename in PDS_LABELS:
#         label = pvl.load(filename)
#         assert label == pvl.loads(pvl.dumps(label))


# def test_cube_encoder():
#     for filename in PDS_LABELS:
#         label = pvl.load(filename)
#         encoder = pvl.encoder.IsisCubeLabelEncoder
#         assert label == pvl.loads(pvl.dumps(label, cls=encoder))


# def test_pds_encoder():
#     for filename in PDS_LABELS:
#         label = pvl.load(filename)
#         encoder = pvl.encoder.PDSLabelEncoder
#         assert label == pvl.loads(pvl.dumps(label, cls=encoder))


# def test_special_values():
#     module = pvl.PVLModule([
#         ('bool_true', True),
#         ('bool_false', False),
#         ('null', None),
#     ])
#     assert module == pvl.loads(pvl.dumps(module))
#
#     encoder = pvl.encoder.IsisCubeLabelEncoder
#     assert module == pvl.loads(pvl.dumps(module, cls=encoder))
#
#     encoder = pvl.encoder.PDSLabelEncoder
#     assert module == pvl.loads(pvl.dumps(module, cls=encoder))


# def test_special_strings():
#     module = pvl.PVLModule([
#         ('single_quote', "'"),
#         ('double_quote', '"'),
#         ('mixed_quotes', '"\''),
#     ])
#     assert module == pvl.loads(pvl.dumps(module))
#
#     encoder = pvl.encoder.IsisCubeLabelEncoder
#     assert module == pvl.loads(pvl.dumps(module, cls=encoder))
#
#     encoder = pvl.encoder.PDSLabelEncoder
#     assert module == pvl.loads(pvl.dumps(module, cls=encoder))


# def test_unkown_value():
#     class UnknownType(object):
#         pass
#
#     with pytest.raises(TypeError):
#         pvl.dumps({'foo': UnknownType()})


# def test_quoated_strings():
#     module = pvl.PVLModule([
#         ('int_like', "123"),
#         ('float_like', '.2'),
#         ('date', '1987-02-25'),
#         ('time', '03:04:05'),
#         ('datetime', '1987-02-25T03:04:05'),
#         ('keyword', 'END'),
#         ('restricted_chars', '&<>\'{},[]=!#()%";|'),
#         ('restricted_seq', '/**/'),
#     ])
#     assert module == pvl.loads(pvl.dumps(module))
#
#     encoder = pvl.encoder.IsisCubeLabelEncoder
#     assert module == pvl.loads(pvl.dumps(module, cls=encoder))
#
#     encoder = pvl.encoder.PDSLabelEncoder
#     assert module == pvl.loads(pvl.dumps(module, cls=encoder))


# def test_dump_to_file_insert_before():
#     tmpdir = tempfile.mkdtemp()
#
#     try:
#         for filename in PDS_LABELS:
#             label = pvl.load(filename)
#             if os.path.basename(filename) != 'empty.lbl':
#                 label.insert_before('PDS_VERSION_ID', [('new', 'item')])
#             tmpfile = os.path.join(tmpdir, os.path.basename(filename))
#             pvl.dump(label, tmpfile)
#             assert label == pvl.load(tmpfile)
#     finally:
#         shutil.rmtree(tmpdir)
#
#
# def test_dump_to_file_insert_after():
#     tmpdir = tempfile.mkdtemp()
#
#     try:
#         for filename in PDS_LABELS:
#             label = pvl.load(filename)
#             if os.path.basename(filename) != 'empty.lbl':
#                 label.insert_after('PDS_VERSION_ID', [('new', 'item')])
#             tmpfile = os.path.join(tmpdir, os.path.basename(filename))
#             pvl.dump(label, tmpfile)
#             assert label == pvl.load(tmpfile)
#     finally:
#         shutil.rmtree(tmpdir)
