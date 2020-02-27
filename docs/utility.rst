================
Utility Programs
================

This library also provides some command-line utility programs to work with
PVL text.

.. autoprogram:: pvl.pvl_translate:arg_parser(pvl.pvl_translate.formats)
   :prog: pvl_translate

In the examples below will all operate on the file with these contents::
    
    PDS_VERSION_ID       = PDS3
    
    /* FILE DATA ELEMENTS */
    
    RECORD_TYPE          = FIXED_LENGTH
    RECORD_BYTES         = 824
    LABEL_RECORDS        = 1
    FILE_RECORDS         = 601
    
    /* POINTERS TO DATA OBJECTS */
    
    ^IMAGE               = 2
    
    /* IMAGE DATA ELEMENTS */
    
    OBJECT               = IMAGE
      LINES              = 600
      LINE_SAMPLES       = 824
      SAMPLE_TYPE        = MSB_INTEGER
      SAMPLE_BITS        = 8
      MEAN               = 51.67785396440129
      MEDIAN             = 50.00000
      MINIMUM            = 0
      MAXIMUM            = 255
      STANDARD_DEVIATION = 16.97019
      CHECKSUM           = 25549531
    END_OBJECT           = IMAGE
    
    END

Convert to PDS3 (whitespace and comments get removed)::

 > pvl_translate -of PDS3 tests/data/pds3/simple_image_1.lbl
 PDS_VERSION_ID = PDS3
 RECORD_TYPE    = FIXED_LENGTH
 RECORD_BYTES   = 824
 LABEL_RECORDS  = 1
 FILE_RECORDS   = 601
 ^IMAGE         = 2
 OBJECT = IMAGE
   LINES              = 600
   LINE_SAMPLES       = 824
   SAMPLE_TYPE        = MSB_INTEGER
   SAMPLE_BITS        = 8
   MEAN               = 51.67785396440129
   MEDIAN             = 50.0
   MINIMUM            = 0
   MAXIMUM            = 255
   STANDARD_DEVIATION = 16.97019
   CHECKSUM           = 25549531
 END_OBJECT = IMAGE
 END

Convert to PVL::

 > pvl_translate -of PVL tests/data/pds3/simple_image_1.lbl
 PDS_VERSION_ID = PDS3;
 RECORD_TYPE    = FIXED_LENGTH;
 RECORD_BYTES   = 824;
 LABEL_RECORDS  = 1;
 FILE_RECORDS   = 601;
 ^IMAGE         = 2;
 BEGIN_OBJECT = IMAGE;
   LINES              = 600;
   LINE_SAMPLES       = 824;
   SAMPLE_TYPE        = MSB_INTEGER;
   SAMPLE_BITS        = 8;
   MEAN               = 51.67785396440129;
   MEDIAN             = 50.0;
   MINIMUM            = 0;
   MAXIMUM            = 255;
   STANDARD_DEVIATION = 16.97019;
   CHECKSUM           = 25549531;
 END_OBJECT = IMAGE;
 END;

Convert to JSON::

 > pvl_translate -of JSON tests/data/pds3/simple_image_1.lbl
 {"PDS_VERSION_ID": "PDS3", "RECORD_TYPE": "FIXED_LENGTH", "RECORD_BYTES": 824, "LABEL_RECORDS": 1, "FILE_RECORDS": 601, "^IMAGE": 2, "IMAGE": {"LINES": 600, "LINE_SAMPLES": 824, "SAMPLE_TYPE": "MSB_INTEGER", "SAMPLE_BITS": 8, "MEAN": 51.67785396440129, "MEDIAN": 50.0, "MINIMUM": 0, "MAXIMUM": 255, "STANDARD_DEVIATION": 16.97019, "CHECKSUM": 25549531}}


.. autoprogram:: pvl.pvl_validate:arg_parser()
   :prog: pvl_validate

Validate one file::

 > pvl_validate tests/data/pds3/simple_image_1.lbl
 PDS3 |     Loads     |     Encodes
 ODL  |     Loads     |     Encodes
 PVL  |     Loads     |     Encodes
 ISIS |     Loads     |     Encodes
 Omni |     Loads     |     Encodes
 >

You can see here that the ``simple_image_1.lbl`` file can be
loaded and the resulting Python object encoded with each of the
PVL dialects that the ``pvl`` library knows.

A file with broken PVL text::

 > pvl_validate tests/data/pds3/broken/broken1.lbl
 PDS3 | does NOT load |
 ODL  | does NOT load |
 PVL  | does NOT load |
 ISIS |     Loads     |     Encodes
 Omni |     Loads     |     Encodes
 >

Here, the PVL text in broken1.lbl cannot be loaded by the PDS3, ODL, or PVL dialects, to learn why
use ``-v``::

 > pvl_validate -v tests/data/pds3/broken/broken1.lbl
 ERROR: PDS3 load error tests/data/pds3/broken/broken1.lbl (LexerError(...), 'Expecting an Aggregation Block, an Assignment Statement, or an End Statement, but found "=" : line 3 column 7 (char 23)')
 ERROR: ODL load error tests/data/pds3/broken/broken1.lbl (LexerError(...), 'Expecting an Aggregation Block, an Assignment Statement, or an End Statement, but found "=" : line 3 column 7 (char 23)')
 ERROR: PVL load error tests/data/pds3/broken/broken1.lbl (LexerError(...), 'Expecting an Aggregation Block, an Assignment Statement, or an End Statement, but found "=" : line 3 column 7 (char 23)')
 PDS3 | does NOT load |
 ODL  | does NOT load |
 PVL  | does NOT load |
 ISIS |     Loads     |     Encodes
 Omni |     Loads     |     Encodes

This tells us that in these cases, there is a parameter with a
missing value.  However, the OmniParser (the default, and also what
the ISIS dialect uses) has more tolerance for broken PVL text, and
is able to load it, and then write valid PVL back out.

Here's a file which has some PVL text which is valid for some dialects, but not others::

 > pvl_validate tests/data/pds3/dates.lbl
 PDS3 |     Loads     | does NOT encode
 ODL  |     Loads     |     Encodes
 PVL  |     Loads     |     Encodes
 ISIS |     Loads     |     Encodes
 Omni |     Loads     |     Encodes
 >

Here, ``pvl_validate`` indicates that it can load the file with all of the PVL dialects, and
can encode it back for most.  What was the problem::

 > pvl_validate -v tests/data/pds3/dates.lbl
 ERROR: PDS3 encode error tests/data/pds3/dates.lbl PDS labels should only have UTC times, but this time has a timezone: 01:12:22+07:00
 PDS3 |     Loads     | does NOT encode
 ODL  |     Loads     |     Encodes
 PVL  |     Loads     |     Encodes
 ISIS |     Loads     |     Encodes
 Omni |     Loads     |     Encodes


It indicates that it cannot encode the Python object out to the
PDS3 format because it contains a date with a different time zone
(which aren't allowed in a PDS3 Label).  So this is an example of
how the loaders are a little more permissive, but to really test
whether some PVL text is conformant, it also should be able to be
encoded.

In this case, if the user wants to write out a valid PDS3 label, they will have to do 
some work to fix the value.


Validating a bunch of files::

 > pvl_validate tests/data/pds3/*lbl
 ---------------------------------------+-----------+-----------+-----------+-----------+----------
 File                                   |   PDS3    |    ODL    |    PVL    |   ISIS    |   Omni
 ---------------------------------------+-----------+-----------+-----------+-----------+----------
 tests/data/pds3/backslashes.lbl        |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/based_integer1.lbl     |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/dates.lbl              |  L   No E |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/empty.lbl              |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/float1.lbl             |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/float_unit1.lbl        |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/group1.lbl             |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/group2.lbl             |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/group3.lbl             |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/group4.lbl             |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/namespaced_string1.lbl |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/negative_float1.lbl    |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/negative_int1.lbl      |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/nested_object1.lbl     |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/nested_object2.lbl     |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/scaled_real1.lbl       |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/sequence1.lbl          |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/sequence2.lbl          |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/sequence3.lbl          |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/sequence_units1.lbl    |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/set1.lbl               |  L   No E |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/set2.lbl               |  L   No E |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/simple_image_1.lbl     |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/simple_image_2.lbl     |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/string2.lbl            |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/string3.lbl            |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/string4.lbl            |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/tiny1.lbl              |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/tiny2.lbl              |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/tiny3.lbl              |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/tiny4.lbl              |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/units1.lbl             |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/units2.lbl             |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 >

and with ``-v``:: 

 > pvl_validate -v tests/data/pds3/*lbl
 ERROR: PDS3 encode error tests/data/pds3/dates.lbl PDS labels should only have UTC times, but this time has a timezone: 01:12:22+07:00
 ERROR: PDS3 encode error tests/data/pds3/set1.lbl The PDS only allows integers and symbols in sets: {1.5}
 ERROR: PDS3 encode error tests/data/pds3/set2.lbl The PDS only allows integers and symbols in sets: {2.33, 3.4}
 ---------------------------------------+-----------+-----------+-----------+-----------+----------
 File                                   |   PDS3    |    ODL    |    PVL    |   ISIS    |   Omni
 ---------------------------------------+-----------+-----------+-----------+-----------+----------
 tests/data/pds3/backslashes.lbl        |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/based_integer1.lbl     |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/dates.lbl              |  L   No E |  L    E   |  L    E   |  L    E   |  L    E
 tests/data/pds3/empty.lbl              |  L    E   |  L    E   |  L    E   |  L    E   |  L    E
 [... output truncated ...]
