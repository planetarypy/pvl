================
Parsing PVL text
================

.. contents:: `Table of Contents`
  :local:

-----------
From a File
-----------

The :func:`pvl.load()` function parses PVL text from a file or
stream and returns a :class:`dict`-like object (:class:`pvl.PVLModule`
by default) containing information from that text. This documentation
will explain how to use the module as well as some sample code to
use the module efficiently.

Simple Use
+++++++++++

How to use :func:`pvl.load()` to get a single value::

 >>> from pathlib import Path
 >>> import pvl
 >>> path = Path('tests/data/pds3/simple_image_1.lbl')
 >>> pvl.load(path)['RECORD_TYPE']
 'FIXED_LENGTH'

 >>> import pvl
 >>> img = 'tests/data/pds3/simple_image_1.lbl'
 >>> pvl.load(img)['RECORD_TYPE']
 'FIXED_LENGTH'

 >>> import pvl
 >>> img = 'tests/data/pds3/simple_image_1.lbl'
 >>> with open(img, 'r+') as r:
 ...    print(pvl.load(r)['RECORD_TYPE'])
 FIXED_LENGTH


Detailed Use
++++++++++++++

To view the image label of an ISIS cube as a dictionary::

 >>> import pvl
 >>> img = 'tests/data/pattern.cub'
 >>> module = pvl.load(img)
 >>> print(module)
 PVLModule([
   ('IsisCube',
    {'Core': {'Dimensions': {'Bands': 1,
                             'Lines': 90,
                             'Samples': 90},
              'Format': 'Tile',
              'Pixels': {'Base': 0.0,
                         'ByteOrder': 'Lsb',
                         'Multiplier': 1.0,
                         'Type': 'Real'},
              'StartByte': 65537,
              'TileLines': 128,
              'TileSamples': 128}})
   ('Label', PVLObject([
     ('Bytes', 65536)
   ]))
 ])

Not all image labels are formatted the same so different labels will have 
different information that you can obtain. To view what information you can
extract use the ``.keys()`` function::
 
 >>> import pvl
 >>> img = 'tests/data/pds3/simple_image_1.lbl'
 >>> lbl = pvl.load(img)
 >>> lbl.keys()
 KeysView(['PDS_VERSION_ID', 'RECORD_TYPE', 'RECORD_BYTES', 'LABEL_RECORDS', 'FILE_RECORDS', '^IMAGE', 'IMAGE'])

... now you can just copy and paste from this list::
 
 >>> lbl['RECORD_TYPE']
 'FIXED_LENGTH'

The list ``.keys()`` returns is out of order, to see the keys in the 
order of the dictionary use ``.items()`` function::

 >>> import pvl
 >>> img = 'tests/data/pds3/simple_image_1.lbl'
 >>> for item in pvl.load(img).items():
 ...    print(item[0])
 PDS_VERSION_ID
 RECORD_TYPE
 RECORD_BYTES
 LABEL_RECORDS
 FILE_RECORDS
 ^IMAGE
 IMAGE

We can take advantage of the fact ``.items()`` returns a list in order 
and use the index number of the key instead of copying and pasting. This will 
make extracting more than one piece of information at time more convenient. For
example, if you want to print out the first 5 pieces of information::
 
 >>> import pvl
 >>> img = 'tests/data/pds3/simple_image_1.lbl'
 >>> pvl_items = pvl.load(img).items()
 >>> for n in range(0, 5):
 ...    print(pvl_items[n][0], pvl_items[n][1])
 PDS_VERSION_ID PDS3
 RECORD_TYPE FIXED_LENGTH
 RECORD_BYTES 824
 LABEL_RECORDS 1
 FILE_RECORDS 601

... some values have sub-dictionaries. You can access those by::
 
 >>> print(pvl.load(img)['IMAGE'].keys())
 KeysView(['LINES', 'LINE_SAMPLES', 'SAMPLE_TYPE', 'SAMPLE_BITS', 'MEAN', 'MEDIAN', 'MINIMUM', 'MAXIMUM', 'STANDARD_DEVIATION', 'CHECKSUM'])
 >>> print(pvl.load(img)['IMAGE']['SAMPLE_BITS'])
 8

Another way of using :func:`pvl.load` is to use Python's ``with open()`` command. 
Otherwise using this method is very similar to using the methods described 
above::

 >>> import pvl
 >>> with open('tests/data/pattern.cub','r') as r:
 ...    print(pvl.load(r)['Label']['Bytes'])
 65536

-------------
From a String
-------------

The :func:`pvl.loads()` function returns a Python object (typically a 
:class:`pvl.PVLModule` object which is :class:`dict`-like) based on
parsing the PVL text in the string parameter that it is given.


Simple Use
+++++++++++

How to use :func:`pvl.loads()`::
 
 >>> import pvl
 >>> s = """String = 'containing the label of the image'
 ... key = value
 ... END
 ... """
 >>> pvl.loads(s).keys()
 KeysView(['String', 'key'])

 >>> pvl.loads(s)['key']
 'value'


Detailed Use
++++++++++++++

To view the image label dictionary::

 >>> import pvl
 >>> string = """Object = IsisCube
 ...   Object = Core
 ...     StartByte   = 65537
 ...     Format      = Tile
 ...     TileSamples = 128
 ...     TileLines   = 128
 ...
 ...   End_Object
 ... End_Object
 ...
 ... Object = Label
 ...   Bytes = 65536
 ... End_Object
 ... End"""
 >>> print(pvl.loads(string))
 PVLModule([
   ('IsisCube',
    {'Core': {'Format': 'Tile',
              'StartByte': 65537,
              'TileLines': 128,
              'TileSamples': 128}})
   ('Label', PVLObject([
     ('Bytes', 65536)
   ]))
 ])

... to view the keys available::

 >>> print(pvl.loads(string).keys())
 KeysView(['IsisCube', 'Label'])

... and to see the information contained in the keys::
 
 >>> print(pvl.loads(string)['Label'])
 PVLObject([
   ('Bytes', 65536)
 ])

... and what is in the sub-dictionary::

 >>> print(pvl.loads(string)['Label']['Bytes'])
 65536

By default, :func:`pvl.loads()` and :func:`pvl.load()` are very permissive,
and do their best to attempt to parse a wide variety of PVL 'flavors.'

If a parsed label has a parameter with a missing value, the default
behavior of these functions will be to assign a 
:class:`pvl.parser.EmptyValueAtLine` object as the value::

  >>> string = """
  ... Object = Label
  ...   A =
  ... End_Object
  ... End"""

  >>> print(pvl.loads(string))
  PVLModule([
    ('Label',
     {'A': EmptyValueAtLine(3 does not have a value. Treat as an empty string)})
  ])

Stricter parsing can be accomplished by passing a different grammar object
(e.g. :class:`pvl.grammar.PVLGrammar`, :class:`pvl.grammar.ODLGrammar`) to 
:func:`pvl.loads()` or :func:`pvl.load()`::

  >>> import pvl
  >>> some_pvl = """Comments = "PVL and ODL only allow /* */ comments"
  ... /* like this */
  ... # but people use hash-comments all the time
  ... END
  ... """
  >>> print(pvl.loads(some_pvl))
  PVLModule([
    ('Comments', 'PVL and ODL only allow /* */ comments')
  ])
  >>> pvl.loads(some_pvl, grammar=pvl.grammar.PVLGrammar())
  Traceback (most recent call last):
    ...
  pvl.exceptions.LexerError: (LexerError(...), 'Expecting an Aggregation Block, an Assignment Statement, or an End Statement, but found "#" : line 3 column 1 (char 67) near "like this */\n# but people"')


----------
From a URL
----------

The :func:`pvl.loadu()` function returns a Python object (typically a
:class:`pvl.PVLModule` object which is :class:`dict`-like) based on
parsing the PVL text in the data returned from a URL.

This is very similar to parsing PVL text from a file, but you use
:func:`pvl.loadu()` instead::

 >>> import pvl
 >>> url = 'https://hirise-pds.lpl.arizona.edu/PDS/RDR/ESP/ORB_017100_017199/ESP_017173_1715/ESP_017173_1715_RED.LBL'
 >>> pvl.loadu(url)['VIEWING_PARAMETERS']['PHASE_ANGLE']
 Quantity(value=50.784875, units='DEG')

Of course, other kinds of URLs, like file, ftp, rsync, sftp and more can be used.
