===============================
pvl
===============================

.. image:: https://badge.fury.io/py/pvl.svg
    :target: http://badge.fury.io/py/pvl

.. image:: https://travis-ci.org/planetarypy/pvl.svg?branch=master
        :target: https://travis-ci.org/planetarypy/pvl

.. image:: https://pypip.in/d/pvl/badge.png
        :target: https://pypi.python.org/pypi/pvl


Python implementation of PVL (Parameter Value Language)

* Free software: BSD license
* Documentation: http://pvl.readthedocs.org.

Features
--------

* TODO

How to use Module
--------------------

.. contents:: `Table of Contents`
	:local:

pvl.load
+++++++++

General:: 

This module parses an isis label from a stream and returns a dictionary 
containing information from the label. The stream must be a string of the image 
file name with the path to the file included.

 >>> import pvl
 >>> img = 'img_file.ext'
 >>> pvl.load(img)
 Image Label
 >>> pvl.load(img)['key']
 value

 >>> import pvl
 >>> img = 'path\to\img_file.ext'
 >>> with open(img, 'r+') as r:
         print pvl.load(r)['key']
 Value

Example::

 >>> import pvl
 >>> img = '1p205337908eff73u6p2438r2m1.img'
 >>> pvl.load(img)
 >>> pvl.load(img).keys()
 [u'INSTRUMENT_ID',
 u'SUBFRAME_REQUEST_PARMS',
 u'SOLAR_LONGITUDE',
 u'PRODUCER_INSTITUTION_NAME',
 u'PRODUCT_ID',
 u'PLANET_DAY_NUMBER',
 u'PROCESSING_HISTORY_TEXT',]
 >>> load(img)['INSTRUMENT_ID']
 u'PANCAM_RIGHT'

See full documentation :doc:`parsing`

pvl.loads
+++++++++

General::

This module parses an isis label from a string and returns a dictionary 
containingv information from the label. 

How to use Moduel::
 
 >>> import pvl
 >>> img = """String containing the 

 label of the 

 isis image"""

 >>> pvl.loads(img).keys()
 >>> pvl.loads(img)['key']
 value


Example::

 >>> import pvl
 string = """Object = IsisCube
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
 >>> print pvl.loads(string).keys()
 [u'Label', u'IsisCube']
 >>> print pvl.loads(string)['Label']
 LabelObject([
  (u'Bytes', 65536)
 ])

See full documentation :doc:`parsing`