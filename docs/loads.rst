=========
pvl.loads
=========

.. contents:: `Table of Contents`
	:local:

This module parses an isis label from a string and returns a dictionary 
containingv information from the label. This documentation will explain how to 
use the module as well as some sample code to use the module efficiently.

Simple Use
-----------

How to use Moduel::
 
 >>> from pvl import load
 >>> img = """String
 containing the label

 of the isis image"""
 >>> loads(img).keys()
 >>> load(img)['key']
 value

Parameters
-----------

Must be a string of the of the label.

Detailed Use
--------------

To view the isis label dictonary::

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
 >>> print loads(string)
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

 >>> print loads(string).keys()
 [u'Label', u'IsisCube']

And to see the information contained in the keys::
 
 >>> print loads(string)['Label']
 LabelObject([
  (u'Bytes', 65536)
 ])

And what is in the subdirectory::

 >>> print loads(string)['Label']['Bytes']
 65536

For more examples, see :doc:`load` and use the methods in that documentation

