================
Parsing PVL text
================

.. contents:: `Table of Contents`
  :local:

-----------
From a File
-----------

The :func:`pvl.load()` function parses PVL-compliant text from a
file or stream and returns a dictionary containing information from
that text. This documentation will explain how to use the module
as well as some sample code to use the module efficiently.

Simple Use
+++++++++++

How to use :func:`pvl.load()`::

 >>> from pathlib import Path
 >>> import pvl
 >>> path = Path('path/to/img_file.ext')
 >>> pvl.load(path)
 >>> pvl.load(img)['key']
 Value

 >>> import pvl
 >>> img = 'path\to\img_file.ext'
 >>> pvl.load(img)
 >>> pvl.load(img)['key']
 Value

 >>> import pvl
 >>> img = 'path\to\img_file.ext'
 >>> with open(img, 'r+') as r:
         print(pvl.load(r)['key'])
 Value


Detailed Use
++++++++++++++

To view the image label as a dictionary::

 >>> import pvl
 >>> img = '1p205337908eff73u6p2438r2m1.img'
 >>> pvl.load(img)
 PVLModule([
  ('PDS_VERSION_ID', 'PDS3')
  ('RECORD_TYPE', 'FIXED_LENGTH')
  ('RECORD_BYTES', 2048)
  ('FILE_RECORDS', 1043)
  ('LABEL_RECORDS', 12)
  ('^IMAGE_HEADER', 13)
  ('^IMAGE', 20)
 ])

Not all image labels are formatted the same so different labels will have 
different information that you can obtain. To view what information you can
extract use the ``.keys()`` function::
 
 >>> import pvl
 >>> img = '1p205337908eff73u6p2438r2m1.img'
 >>> lbl = pvl.load(img)
 >>> lbl.keys()
 ['INSTRUMENT_ID',
 'SUBFRAME_REQUEST_PARMS',
 'SOLAR_LONGITUDE',
 'PRODUCER_INSTITUTION_NAME',
 'PRODUCT_ID',
 'PLANET_DAY_NUMBER',
 'PROCESSING_HISTORY_TEXT',]

Now you can just copy and paste from this list::
 
 >>> lbl['INSTRUMENT_ID']
 'PANCAM_RIGHT'

The list ``.keys()`` returns is out of order, to see the keys in the 
order of the dictionary use ``.items()`` function::

 >>> import pvl
 >>> img = '1p205337908eff73u6p2438r2m1.img'
 >>> for item in pvl.load(img).items():
         print(item[0])
 PDS_VERSION_ID
 RECORD_TYPE
 RECORD_BYTES
 FILE_RECORDS
 LABEL_RECORDS
 ^IMAGE_HEADER
 ^IMAGE
 DATA_SET_ID

We can take advantage of the fact ``.items()`` returns a list in order 
and use the index number of the key instead of copying and pasting. This will 
make extracting more than one piece of information at time more convenient. For
example, if you want to print out the first 5 pieces of information::
 
 >>> import pvl
 >>> img = '1p205337908eff73u6p2438r2m1.img'
 >>> keys = pvl.load(img).items()
 >>> for n in range(0,5):
        print(keys[n][0],keys[n][1])
 0PDS_VERSION_ID PDS3
 RECORD_TYPE FIXED_LENGTH
 RECORD_BYTES 2048
 FILE_RECORDS 1043
 LABEL_RECORDS 12

Some values have sub-dictionaries. You can access those by::
 
 >>> print(pvl.load(img)[keys[1]].keys())
 ['LINE_SAMPLES', 'FIRST_LINE_SAMPLE', 'LINES', 'GROUP_APPLICABILITY_FLAG', 'SUBFRAME_TYPE', 'SOURCE_ID', 'FIRST_LINE']
 >>> print pvl.load(img)[keys[1]]['SOURCE_ID']
 GROUND COMMANDED

``pvl.load`` also works for ISIS Cube files::

 >>> import pvl
 >>> img = 'pattern.cub'
 >>> keys = pvl.load(img).keys()
 >>> for n, item in enumerate(keys):
        print(n, item)
 0 Label
 1 IsisCube
 >>> print(pvl.load(img)[keys[0]])
 LabelObject([
  ('Bytes', 65536)
 ])
 >>> print(pvl.load(img)[keys[0]]['Bytes'])
 65536

Another way of using :func:`pvl.load` is to use python's ``with open()`` command. 
Otherwise using this method is very similar to using the methods described 
above::

 >>> import pvl
 >>> with open('pattern.cub','r') as r:
        print(pvl.load(r)['Label']['Bytes'])
 65536

-------------
From a String
-------------

The :func:`pvl.loads()` function returns a Python object (typically a 
:class:`pvl.PVLModule` object which is :class:`dict`-like) based on
parsing the text in the string parameter that it is given.


Simple Use
+++++++++++

How to use :func:`pvl.loads()`::
 
 >>> import pvl
 >>> s = """String = 'containing the label of the image'
 key = value
 END
 """
 >>> pvl.loads(s).keys()
 ['String', 'key']

 >>> pvl.loads(img)['key']
 value


Detailed Use
++++++++++++++

To view the image label dictionary::

 >>> import pvl
 >>> string = """Object = IsisCube
   Object = Core
     StartByte   = 65537
     Format      = Tile
     TileSamples = 128
     TileLines   = 128

   End_Object
 End_Object

 Object = Label
   Bytes = 65536
 End_Object
 End"""
 >>> print(pvl.loads(string))
 PVLModule([
  ('IsisCube',
   PVLObject([
    ('Core',
     PVLObject([
      ('StartByte', 65537)
      ('Format', 'Tile')
      ('TileSamples', 128)
      ('TileLines', 128)
    ]))
  ]))
  ('Label', PVLObject([
    ('Bytes', 65536)
  ]))
 ])

To view the keys available::

 >>> print(pvl.loads(string).keys())
 ['Label', 'IsisCube']

And to see the information contained in the keys::
 
 >>> print(pvl.loads(string)['Label'])
 PVLObject([
  ('Bytes', 65536)
 ])

And what is in the sub-dictionary::

 >>> print(pvl.loads(string)['Label']['Bytes'])
 65536

By default, :func:`pvl.loads()` and :func:`pvl.load()` are very permissive,
and do their best to attempt to parse a wide variety of PVL 'flavors.'

If a parsed label has a parameter with a missing value, the default
behavior of these functions will be to assign a 
:class:`pvl.parser.EmptyValueAtLine` object as the value::

  >>> string = """
  Object = Label
    A =
  End_Object
  End"""

  >>> print(pvl.loads(string))
  PVLModule([
   ('Label',
    PVLObject([
     ('A', EmptyValueAtLine(3 does not have a value. Treat as an empty string))
   ]))
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
  pvl.lexer.LexerError: (LexerError(...), 'Expecting an Aggregation Block, an Assignment Statement, or an End Statement, but found "#" : line 2 column 1 (char 51)')
