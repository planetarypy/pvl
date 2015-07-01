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

 >>> from pvl import load
 >>> img = 'img_file.ext'
 >>> load(img)
 Image Label
 >>> load(img)['key']
 value

 >>> from pvl import load
 >>> img = 'path\to\img_file.ext'
 >>> with open(img, 'r+') as r:
         print load(r)['key']
 Value

Example::

 >>> from pvl import load
 >>> img = '1p205337908eff73u6p2438r2m1.img'
 >>> load(img)
 >>> load(img).keys()
 [u'INSTRUMENT_ID',
 u'SUBFRAME_REQUEST_PARMS',
 u'SOLAR_LONGITUDE',
 u'PRODUCER_INSTITUTION_NAME',
 u'PRODUCT_ID',
 u'PLANET_DAY_NUMBER',
 u'PROCESSING_HISTORY_TEXT',]
 >>> load(img)['INSTRUMENT_ID']
 u'PANCAM_RIGHT'

See full documentation :doc:`load`

pvl.loads
+++++++++

General::

This module parses an isis label from a string and returns a dictionary 
containingv information from the label. 

How to use Moduel::
 
 >>> from pvl import load
 >>> img = """String containing the 

 label of the 

 isis image"""

 >>> loads(img).keys()
 >>> load(img)['key']
 value


Example::

 >>> from pvl import loads
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
 >>> print loads(string).keys()
 [u'Label', u'IsisCube']
 >>> print loads(string)['Label']
 LabelObject([
  (u'Bytes', 65536)
 ])

See full documentation :doc:`loads`