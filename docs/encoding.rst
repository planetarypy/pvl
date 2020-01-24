====================
Writing out PVL text
====================

This documentation explains how you can use :func:`pvl.dump` and 
:func:`pvl.dumps` so you can change, add, and/or write out a Python
:class:`dict`-like object as PVL text either to a :class:`str` or
a file.  This documentation assumes that you've read about how to
`parse PVL text <parsing.rst>`_ and know how :func:`pvl.load` and
:func:`pvl.loads` work.

The examples primarily use an ISIS Cube image label format, which
typically doesn't conform to PDS 3 standards, so pay attention to
the differences between the PVL text that is loaded, versus the PDS
3-compliant PVL text that is dumped.

However, this library can write/alter any PVL compliant label.


.. contents:: `Table of Contents`
  :local:

--------------------------
Writing PVL Text to a File
--------------------------

The :func:`pvl.dump` function allows you to write out a :class:`dict`-like
Python object (typically a :class:`pvl.PVLModule` object) to a file as PVL
text.

Simple Use
+++++++++++

Read a label from a file::

 >>> import pvl
 >>> pvl_file = 'tests/data/pds3/tiny1.lbl'
 >>> label = pvl.load(pvl_file)
 >>> print(label)
 PVLModule([
   ('PDS_VERSION_ID', 'PDS3')
 ])

... then you can change a value::

 >>> label['PDS_VERSION_ID'] = 42
 >>> print(label)
 PVLModule([
   ('PDS_VERSION_ID', 42)
 ])

... then add keys to the ``label`` object::

 >>> label['New_Key'] = 'New_Value'
 >>> print(label)
 PVLModule([
   ('PDS_VERSION_ID', 42)
   ('New_Key', 'New_Value')
 ])

... and then write out the PVL text to a file::

 >>> pvl.dump(label, 'new.lbl')
 54

:func:`pvl.dump` returns the number of characters written to the file.

Changing A Key
+++++++++++++++

More complicated parameter value change.

Load some PVL text from a file::

 >>> import pvl
 >>> img = 'tests/data/pattern.cub'
 >>> label = pvl.load(img)
 >>> print(label['IsisCube']['Core']['Format'])
 Tile

... then change key 'Format' to 'Changed_Value'::

 >>> label['IsisCube']['Core']['Format'] = 'Changed_Value'

... then writing out file with new value::

 >>> new_file = 'new.lbl'
 >>> pvl.dump(label, new_file) 
 494

If you then try to show the changed value in the file, you'll 
get an error::

 >>> new_label = pvl.load(new_file)
 >>> print(new_label['IsisCube']['Core']['Format'])
 Traceback (most recent call last):
    ...
 KeyError: 'Format'

This is because the default for :func:`pvl.dump` and :func:`pvl.dumps` is to write out
PDS3-Standards-compliant PVL, in which the parameter values (but not the aggregation
block names) are uppercased::

 >>> print(new_label['IsisCube']['Core'].keys())
 KeysView(['STARTBYTE', 'FORMAT', 'TILESAMPLES', 'TILELINES', 'Dimensions', 'Pixels'])
 >>> print(new_label['IsisCube']['Core']['FORMAT'])
 Changed_Value

Clean up::

    >>> import os
    >>> os.remove(new_file)

Yes, this case difference is weird, yes, this means that you need
to be aware of the case of different keys in your :class:`pvl.PVLModule`
objects.


----------------------------
Writing PVL Text to a String
----------------------------

The :func:`pvl.dumps` function allows you to convert a :class:`dict`-like
Python object (typically a :class:`pvl.PVLModule` object) to a Python 
:class:`str` object which contains the PVL text.

Simple Use
+++++++++++

Get started, as above::

 >>> import pvl
 >>> pvl_file = 'tests/data/pds3/tiny1.lbl'
 >>> label = pvl.load(pvl_file)
 >>> print(label)
 PVLModule([
   ('PDS_VERSION_ID', 'PDS3')
 ])

... then change a value, and add keys::

 >>> label['PDS_VERSION_ID'] = 42
 >>> label['New_Param'] = 'New_Value'
 >>> print(label)
 PVLModule([
   ('PDS_VERSION_ID', 42)
   ('New_Param', 'New_Value')
 ])

... then write to a string::

 >>> print(pvl.dumps(label))
 PDS_VERSION_ID = 42
 NEW_PARAM      = New_Value
 END
 <BLANKLINE>

Here we can see the effects of the PDS3LabelEncoder in the default
behavior of :func:`pvl.dumps`: it uppercases the parameters, and
puts a blank line after the END statement.  If we were to use the PVLEncoder,
you can see different behavior::

 >>> print(pvl.dumps(label, encoder=pvl.encoder.PVLEncoder()))
 PDS_VERSION_ID = 42;
 New_Param      = New_Value;
 END;


Adding A Key
+++++++++++++

More complicated::

 >>> import pvl
 >>> pvl_file = 'tests/data/pds3/group1.lbl'
 >>> label = pvl.load(pvl_file)
 >>> print(label)
 PVLModule([
   ('PDS_VERSION_ID', 'PDS3')
   ('IMAGE',
    {'CHECKSUM': 25549531,
     'MAXIMUM': 255,
     'STANDARD_DEVIATION': 16.97019})
   ('SHUTTER_TIMES', PVLGroup([
     ('START', 1234567)
     ('STOP', 2123232)
   ]))
 ])

... then add a new key and value to a sub group::

 >>> label['New_Key'] = 'New_Value'
 >>> label['IMAGE']['New_SubKey'] = 'New_SubValue'
 >>> print(label)
 PVLModule([
   ('PDS_VERSION_ID', 'PDS3')
   ('IMAGE',
    {'CHECKSUM': 25549531,
     'MAXIMUM': 255,
     'New_SubKey': 'New_SubValue',
     'STANDARD_DEVIATION': 16.97019})
   ('SHUTTER_TIMES', PVLGroup([
     ('START', 1234567)
     ('STOP', 2123232)
   ]))
   ('New_Key', 'New_Value')
 ])

... then when we dump, the default is to write PDS3 Labels, so the parameters are
uppercased::

  >>> print(pvl.dumps(label))
  PDS_VERSION_ID = PDS3
  OBJECT = IMAGE
    MAXIMUM            = 255
    STANDARD_DEVIATION = 16.97019
    CHECKSUM           = 25549531
    NEW_SUBKEY         = New_SubValue
  END_OBJECT = IMAGE
  GROUP = SHUTTER_TIMES
    START = 1234567
    STOP  = 2123232
  END_GROUP = SHUTTER_TIMES
  NEW_KEY        = New_Value
  END
  <BLANKLINE>


Example with an ISIS cube file
++++++++++++++++++++++++++++++

::

 >>> import pvl
 >>> img = 'tests/data/pattern.cub'
 >>> label = pvl.load(img)
 >>> label['New_Key'] = 'New_Value'
 >>> label_string = pvl.dumps(label)
 >>> print(label_string)
 OBJECT = IsisCube
   OBJECT = Core
     STARTBYTE   = 65537
     FORMAT      = Tile
     TILESAMPLES = 128
     TILELINES   = 128
     GROUP = Dimensions
       SAMPLES = 90
       LINES   = 90
       BANDS   = 1
     END_GROUP = Dimensions
     GROUP = Pixels
       TYPE       = Real
       BYTEORDER  = Lsb
       BASE       = 0.0
       MULTIPLIER = 1.0
     END_GROUP = Pixels
   END_OBJECT = Core
 END_OBJECT = IsisCube
 OBJECT = Label
   BYTES = 65536
 END_OBJECT = Label
 NEW_KEY      = New_Value
 END
 <BLANKLINE>

PVL text for ISIS program consumption
+++++++++++++++++++++++++++++++++++++

There are a number of ISIS programs that take PVL text files as a
way of allowing users to provide more detailed inputs.  To write
PVL text that is readable by ISIS, you can use the
:class:`pvl.encoder.ISISEncoder`.  Here's an example of creating a map file
used by the ISIS program ``cam2map``.  Since ``cam2map`` needs the
'Mapping' aggregation to be a PVL Group, you must use the
:class:`pvl.PVLGroup` object to assign to 'Mapping' rather than
just a dict-like (which gets encoded as a PVL Object by default).
You'd normally use :func:`pvl.dump` to write to a file, but we use
:func:`pvl.dumps` here to show what you'd get::

 >>> import pvl
 >>> subsc_lat = 10
 >>> subsc_lon = 10
 >>> map_pvl = {'Mapping': pvl.PVLGroup({'ProjectionName': 'Orthographic',
 ...                                     'CenterLatitude': subsc_lat,
 ...                                     'CenterLongitude': subsc_lon})}
 >>> print(pvl.dumps(map_pvl, encoder=pvl.encoder.ISISEncoder()))
 Group = Mapping
   ProjectionName  = Orthographic
   CenterLatitude  = 10
   CenterLongitude = 10
 End_Group = Mapping
 END


Pre-1.0 pvl dump behavior
+++++++++++++++++++++++++

If you don't like the new default behavior of writing out PDS3 Label
Compliant PVL text, then just using an encoder with some different 
settings will get you the old style::

 >>> import pvl
 >>> img = 'tests/data/pattern.cub'
 >>> label = pvl.load(img)
 >>> print(pvl.dumps(label))
 OBJECT = IsisCube
   OBJECT = Core
     STARTBYTE   = 65537
     FORMAT      = Tile
     TILESAMPLES = 128
     TILELINES   = 128
     GROUP = Dimensions
       SAMPLES = 90
       LINES   = 90
       BANDS   = 1
     END_GROUP = Dimensions
     GROUP = Pixels
       TYPE       = Real
       BYTEORDER  = Lsb
       BASE       = 0.0
       MULTIPLIER = 1.0
     END_GROUP = Pixels
   END_OBJECT = Core
 END_OBJECT = IsisCube
 OBJECT = Label
   BYTES = 65536
 END_OBJECT = Label
 END
 <BLANKLINE>
 >>> print(pvl.dumps(label, encoder=pvl.PVLEncoder(end_delimiter=False)))
 ...                                               
 BEGIN_OBJECT = IsisCube
   BEGIN_OBJECT = Core
     StartByte   = 65537
     Format      = Tile
     TileSamples = 128
     TileLines   = 128
     BEGIN_GROUP = Dimensions
       Samples = 90
       Lines   = 90
       Bands   = 1
     END_GROUP = Dimensions
     BEGIN_GROUP = Pixels
       Type       = Real
       ByteOrder  = Lsb
       Base       = 0.0
       Multiplier = 1.0
     END_GROUP = Pixels
   END_OBJECT = Core
 END_OBJECT = IsisCube
 BEGIN_OBJECT = Label
   Bytes = 65536
 END_OBJECT = Label
 END


... of course, to really get the true old behavior, you should also use
the carriage return/newline combination line endings, and encode the string as a
bytearray, since that is the Python type that the pre-1.0 library
produced::

 >>> print(pvl.dumps(label, encoder=pvl.PVLEncoder(end_delimiter=False,
 ...                                               newline='\r\n')).encode())
 b'BEGIN_OBJECT = IsisCube\r\n  BEGIN_OBJECT = Core\r\n    StartByte   = 65537\r\n    Format      = Tile\r\n    TileSamples = 128\r\n    TileLines   = 128\r\n    BEGIN_GROUP = Dimensions\r\n      Samples = 90\r\n      Lines   = 90\r\n      Bands   = 1\r\n    END_GROUP = Dimensions\r\n    BEGIN_GROUP = Pixels\r\n      Type       = Real\r\n      ByteOrder  = Lsb\r\n      Base       = 0.0\r\n      Multiplier = 1.0\r\n    END_GROUP = Pixels\r\n  END_OBJECT = Core\r\nEND_OBJECT = IsisCube\r\nBEGIN_OBJECT = Label\r\n  Bytes = 65536\r\nEND_OBJECT = Label\r\nEND'
