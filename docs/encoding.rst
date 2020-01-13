====================
Writing out PVL text
====================

This documentation explains how you can use :func:`pvl.dump` and 
:func:`pvl.dumps` so you can change, add, and/or write out the label to 
another file. This documentation assumes that you've read about how to
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

Read a label from a file, and then write it out to another::

 >>> import pvl
 >>> img = 'path/to/image.ext'
 >>> label = pvl.load(img)
 # Change information
 >>> label['Existing_Key'] = 'Different_Value'
 # Add Information
 >>> label['New_Key'] = 'New_Value'
 # Write out new label to file
 >>> pvl.dump(label, 'path/to/new.pvl')


Changing A Key
+++++++++++++++

In order to change the value assigned to a key::

 >>> import pvl
 >>> img = 'pattern.cub'
 >>> label = pvl.load(img)
 >>> print label['IsisCube']['Core']['Format']
 Tile
 # Changing key 'Format' to 'Changed_Value'
 >>> label['IsisCube']['Core']['Format'] = 'Changed_Value'
 # Writing out file with new value
 >>> with open(img,'w') as stream:
         pvl.dump(label,stream)
 # Showing the value changed in the file
 >>> new_label = pvl.load(img)
 >>> print new_label['IsisCube']['Core']['Format']
 Changed_Value

Adding A Key
+++++++++++++

In order to add a new key and value to a label::

 >>> import pvl
 >>> img = 'pattern.cub'
 >>> label = pvl.load(img)
 # Adding a new key and value
 >>> label['New_Key'] = 'New_Value'
 # Adding a new key and value to a sub group
 >>> label['IsisCube']['Core']['New_SubKey'] = 'New_SubValue'
 # Writing new keys and values to file
 >>> with open(img,'w') as stream:
         pvl.dump(label,stream)
 # Showing the value changed in the file
 >>> new_label = pvl.load(img)
 >>>print new_label['New_Key']
 New_Value
 >>> print new_label['IsisCube']['Core']['New_SubKey']
 New_SubValue

Writing to a Different File
++++++++++++++++++++++++++++

If you do not want to overwrite the existing file and make a detached label::

 >>> import pvl
 >>> img = 'pattern.cub'
 >>> label = pvl.load(img)
 >>> label['IsisCube']['Core']['Format'] = 'Changed_Value'
 # Creating new file with same name but with .lbl extension
 >>> new_name = img.replace('.img','.lbl')
 >>> print(new_name)
 pattern.lbl
 >>> pvl.dump(label, new_name)
 >>> new_label = pvl.load(new_name)
 >>> print new_label['IsisCube']['Core']['Format']
 Changed_Value

----------------------------
Writing PVL Text to a String
----------------------------

The :func:`pvl.dumps` function allows you to convert a :class:`dict`-like
Python object (typically a :class:`pvl.PVLModule` object) to a Python 
:class:`str` object which contains the PVL text.

Simple Use
+++++++++++

How to use::

 >>> import pvl
 >>> img = 'path/to/image.ext'
 >>> label = pvl.load(img)
 # Change information
 >>> label['Existing_Key'] = 'Different_Value'
 # Add Information
 >>> label['New_Key'] = 'New_Value'
 # Convert to a string
 >>> label_string = pvl.dumps(label)
 >>> print(label_string)
 EXISTING_KEY = Different_Value
 NEW_KEY = New_Value

Example
++++++++

::

 >>> import pvl
 >>> img = 'pattern.cub'
 >>> label = pvl.load(img)
 >>> label['New_Key'] = 'New_Value'
 >>> label_string = pvl.dumps(label)
 >>> print(label_string)
 Object = IsisCube
  Object = Core
    StartByte = 65537
    Format = Tile
    TileSamples = 128
    TileLines = 128
    Group = Dimensions
      Samples = 90
      Lines = 90
      Bands = 1
    End_Group
 End_Object
 New_Key = New_Value
 End

