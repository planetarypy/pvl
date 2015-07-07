==============
Encoding Label
==============

This documentation explains how you can use ``pvl.dump`` and ``pvl.dumps`` so 
you can change, add, and/or write out the label to another file. This 
documentation assumes that you know what :doc:`pvl.load and pvl.loads <parsing>`
are and how to use them. Read the documentation on :doc:`pvl.load and pvl.loads 
<parsing>` if you do not. The examples use an IsisCube image label format,
however this module can write/alter any PVL compliant label.


.. contents:: `Table of Contents`
  :local:

---------
pvl.dump
---------

This module allows you to modify an existing image label and then write the
new label to the file or to a new file.

Simple Use
+++++++++++

How to use module::

 >>> import pvl
 >>> img = 'path/to/image.ext'
 >>> label = pvl.load(img)
 # Change information
 >>> label['Existing_Key'] = 'Different_Value'
 # Add Information
 >>> label['New_Key'] = 'New_Value'
 # Write out new label to file
 >>> with open(img,'w') as stream:
         pvl.dump(label,stream)

Parameters
++++++++++

Must include a label that is a dictionary and a file to write the label to.

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
 >>> print new_name
 pattern.lbl
 >>> with open(new_name, 'w') as stream:
         pvl.dump(label,new_name)
 >>> new_label = pvl.load(new_name)
 >>> print new_label['IsisCube']['Core']['Format']
 Changed_Value

---------
pvl.dumps
---------

This module takes a label dictionary and converts the dictionary to a string.

Simple Use
+++++++++++

How to use module::

 >>> import pvl
 >>> img = 'path/to/image.ext'
 >>> label = pvl.load(img)
 # Change information
 >>> label['Existing_Key'] = 'Different_Value'
 # Add Information
 >>> label['New_Key'] = 'New_Value'
 # Convert to a string
 >>> label_string = pvl.dumps(label)
 >>> print label_String
 Existing_Key = Different_Value
 New_Key = New_Value

Parameters
++++++++++

Must include a label as a dictionary.

Example
++++++++

 >>> import pvl
 >>> img = 'pattern.cub'
 >>> label = pvl.load(img)
 >>> label['New_Key'] = 'New_Value'
 >>> label_string = pvl.dumps(label)
 >>> print label_string
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

