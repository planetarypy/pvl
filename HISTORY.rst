.. :changelog:

History
-------

1.0.0-alpha (fall 2019)
~~~~~~~~~~~~~~~~~~~~~~~
The above label will be changed and this paragraph will be removed
when the decision is made to release 1.0.0.  This work is categorized
as 1.0.0-alpha because backwards-incompatible changes are being
introduced to the codebase.

* Lightly refactored code so that it will no longer support Python 2, 
  and is only guaranteed to work with Python 3.6 and above.
* Removed the dependency on the `six` library that provided Python 2
  compatibility.
* Removed the dependency on the `pytz` library that provided 'timezone'
  support (functionality replaced by the `dateutil` library, detailed below).
* The private pvl/_numbers.py file was removed, as its capability is now
  accomplished with the Python Standard Library.
* The private pvl/_datetimes.py file was removed, as its capability is now
  accomplished with the `dateutil` library.
* Added an optional dependency on the `dateutil` library (if it is not
  present, the `pvl` library will gracefully fall back to treating dates and
  times as plain strings).  The `dateutil` library was added to provide more
  robust time string parsing, rather than continuing to support that
  functionality within `pvl`.

0.3.0 (2017-06-28)
~~~~~~~~~~~~~~~~~~

* Create methods to add items to the label
* Give user option to allow the parser to succeed in parsing broken labels

0.2.0 (2015-08-13)
~~~~~~~~~~~~~~~~~~

* Drastically increase test coverage.
* Lots of bug fixes.
* Add Cube and PDS encoders.
* Cleanup README.
* Use pvl specification terminology.
* Added element access by index and slice.

0.1.1 (2015-06-01)
~~~~~~~~~~~~~~~~~~

* Fixed issue with reading Pancam PDS Products.

0.1.0 (2015-05-30)
~~~~~~~~~~~~~~~~~~

* First release on PyPI.
