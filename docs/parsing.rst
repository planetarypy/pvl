==============
Parsing Label
==============

.. contents:: `Table of Contents`
  :local:

--------
pvl.load
--------

This module parses a PVL compliant label from a stream and returns a dictionary 
containing information from the label. This documentation will explain how to 
use the module as well as some sample code to use the module efficiently.

Simple Use
+++++++++++

How to use Module::
 
 >>> import pvl
 >>> img = 'path\to\img_file.ext'
 >>> pvl.load(img)
 Image Label Dictionary
 >>> pvl.load(img)['key']
 Value

 >>> import pvl
 >>> img = 'path\to\img_file.ext'
 >>> with open(img, 'r+') as r:
         print pvl.load(r)['key']
 Value


Parameters
+++++++++++

Must be a string of the image file name with the file path included.

Detailed Use
++++++++++++++

To view the image label as a dictionary::

 >>> import pvl
 >>> img = '1p205337908eff73u6p2438r2m1.img'
 >>> pvl.load(img)
 Label([
  (u'PDS_VERSION_ID', u'PDS3')
  (u'RECORD_TYPE', u'FIXED_LENGTH')
  (u'RECORD_BYTES', 2048)
  (u'FILE_RECORDS', 1043)
  (u'LABEL_RECORDS', 12)
  (u'^IMAGE_HEADER', 13)
  (u'^IMAGE', 20)

Not all image labels are formatted the same so different labels will have 
different information that you can obtain. To view what information you can
extract use the ``.keys()`` function::
 
 >>> import pvl
 >>> img = '1p205337908eff73u6p2438r2m1.img'
 >>> lbl = pvl.load(img)
 >>> lbl.keys()
 [u'INSTRUMENT_ID',
 u'SUBFRAME_REQUEST_PARMS',
 u'SOLAR_LONGITUDE',
 u'PRODUCER_INSTITUTION_NAME',
 u'PRODUCT_ID',
 u'PLANET_DAY_NUMBER',
 u'PROCESSING_HISTORY_TEXT',]

Now you can just copy and paste from this list::
 
 >>> lbl['INSTRUMENT_ID']
 u'PANCAM_RIGHT'

The list ``.keys()`` returns is out of order, to see the keys in the 
order of the dictionary use ``.items()`` function::

 >>> import pvl
 >>> img = '1p205337908eff73u6p2438r2m1.img'
 >>> for item in pvl.load(img).items():
         print item[0]
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
        print keys[n][0],keys[n][1]
 0PDS_VERSION_ID PDS3
 RECORD_TYPE FIXED_LENGTH
 RECORD_BYTES 2048
 FILE_RECORDS 1043
 LABEL_RECORDS 12

Some values have sub dictionaries. You can access those by::
 
 >>> print pvl.load(img)[keys[1]].keys()
 [u'LINE_SAMPLES', u'FIRST_LINE_SAMPLE', u'LINES', u'GROUP_APPLICABILITY_FLAG', u'SUBFRAME_TYPE', u'SOURCE_ID', u'FIRST_LINE']
 >>> print pvl.load(img)[keys[1]]['SOURCE_ID']
 GROUND COMMANDED

``pvl.load`` also works for Isis Cube files::

 >>> import pvl
 >>> img = 'pattern.cub'
 >>> keys = pvl.load(img).keys()
 >>> for n, item in enumerate(keys):
        print n, item
 0 Label
 1 IsisCube
 >>> print pvl.load(img)[keys[0]]
 LabelObject([
  (u'Bytes', 65536)
 ])
 >>> print pvl.load(img)[keys[0]]['Bytes']
 65536

Another way of using ``pvl.load`` is to use python's ``with open()`` command. 
Otherwise the using this method is very similar to using the methods described 
above::

 >>> import pvl
 >>> with open('pattern.cub','r') as r:
        print pvl.load(r)['Label']['Bytes']
 65536

---------
pvl.loads
---------

This module parses a PVL compliant label from a string and returns a dictionary 
containing information from the label. This documentation will explain how to 
use the module as well as some sample code to use the module efficiently.

Simple Use
+++++++++++

How to use Module::
 
 >>> import pvl
 >>> img = """String
 containing the label

 of the image"""
 >>> pvl.loads(img).keys()
 >>> pvl.loads(img)['key']
 value

Parameters
+++++++++++

Must be a string of the of the label.

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
 >>> print pvl.loads(string)
 Label([
  (u'IsisCube',
   LabelObject([
    (u'Core',
     LabelObject([
      (u'StartByte', 65537)
      (u'Format', u'Tile')
      (u'TileSamples', 128)
      (u'TileLines', 128)
    ]))
  ]))
  (u'Label', LabelObject([
    (u'Bytes', 65536)
  ]))
 ])

To view the keys available::

 >>> print pvl.loads(string).keys()
 [u'Label', u'IsisCube']

And to see the information contained in the keys::
 
 >>> print pvl.loads(string)['Label']
 LabelObject([
  (u'Bytes', 65536)
 ])

And what is in the subdirectory::

 >>> print pvl.loads(string)['Label']['Bytes']
 65536
