.. :changelog:

=========
 History
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

When updating this file, please add an entry for your change under
Unreleased_ and one of the following headings:

- Added - for new features.
- Changed - for changes in existing functionality.
- Deprecated - for soon-to-be removed features.
- Removed - for now removed features.
- Fixed - for any bug fixes.
- Security - in case of vulnerabilities.

If the heading does not yet exist under Unreleased_, then add it
as a 3rd level heading, underlined with pluses (see examples below).

When preparing for a public release add a new 2nd level heading,
underlined with dashes under Unreleased_ with the version number
and the release date, in year-month-day format (see examples below).


Unreleased
----------

1.1.0 (2020-12-04)
------------------

Added
+++++
* Modified `pvl_validate` to more robustly deal with errors, and also provide
  more error-reporting via `-v` and `-vv`.
* Modified ISISGrammar so that it can parse comments that begin with an octothorpe (#).

Fixed
+++++
* Altered documentation in grammar.py that was incorrectly indicating that
  there were parameters that could be passed on object initiation that would
  alter how those objects behaved.


1.0.1 (2020-09-21)
------------------

Fixed
+++++
* The PDSLabelEncoder was improperly raising an exception if the Python datetime
  object to encode had a tzinfo component that had zero offset from UTC.


1.0.0 (2020-08-23)
------------------
This production version of the pvl library consists of significant
API and functionality changes from the 0.x version that has been
in use for 5 years (a credit to Trevor Olson's skills).  The
documentation has been significantly upgraded, and various granular
changes over the 10 alpha versions of 1.0.0 over the last 8 months
are detailed in their entries below.  However, here is a high-level
overview of what changed from the 0.x version:

Added
+++++
* ``pvl.load()`` and ``pvl.dump()`` take all of the arguments that they could take
  before (string containing a filename, byte streams, etc.), but now also accept any
  ``os.PathLike`` object, or even an already-opened file object.
* ``pvl.loadu()`` function will load PVL text from URLs.
* Utility programs `pvl_validate` and `pvl_translate` were added, please see
  the "Utility Programs" section of the documentation for more information.
* The library can now parse and encode PVL Values with Units expressions
  with third-party quantity objects like `astropy.units.Quantity` and `pint.Quantity`.
  Please see the "Quantities: Values and Units" section of the documentation.
* Implemented a new PVLMultiDict (optional, needs 3rd party multidict library) which
  which has more pythonic behaviors than the existing OrderedMultiDict.  Experiment
  with getting it returned by the loaders by altering your import statement to
  ``import pvl.new as pvl`` and then using the loaders as usual to get the new object
  returned to you.

Changed
+++++++
* Only guaranteed to work with Python 3.6 and above.
* Rigorously implemented the three dialects of PVL text: PVL itself,
  ODL, and the PDS3 Label Standard.  There is a fourth de-facto
  dialect, that of ISIS cube labels that is also handled.  Please see
  the "Standards & Specifications" section of the documentation.
* There is now a default dialect for the dump functions: the PDS3 Label Standard.
  This is different and more strict than before, but other output dialects are
  possible.  Please see the "Writing out PVL text" section in the documentation
  for more information, and how to enable an output similar to the 0.x output.
* There are now ``pvl.collections`` and ``pvl.exceptions`` modules.  There was previously
  an internal ``pvl._collections`` module, and the exception classes were scattered through
  the other modules.

Fixed
+++++
* All ``datetime.time`` and ``datetime.datetime`` objects returned from the loaders
  are now timezone "aware." Previously some were and some were not.
* Functionality to correctly parse dash (-) continuation lines in ISIS output is
  now supported.
* The library now properly parses quoted strings that include backslashes.


Deprecated
++++++++++
* The `pvl.collections.Units` object is deprecated in favor of
  the new ``pvl.collections.Quantity`` object (really a name-only change, no functionality
  difference).


1.0.0-alpha.9 (2020-08-18)
--------------------------
* Minor addition to pvl.collections.MutableMappingSequence.
* Implemented PVLMultiDict which is based on the 3rd Party
  `multidict.MultiDict` object as an option to use instead
  of the default OrderedMultiDict.  The new PVLMultiDict
  is better aligned with the Python 3 way that Mapping
  objects behave.
* Enhanced the existing OrderedMultiDict with some functionality
  that extends its behavior closer to the Python 3 ideal, and
  inserted warnings about how the retained non-Python-3
  behaviors might be removed at the next major patch.
* Implemented pvl.new that can be included for those that wish
  to try out what getting the new PVLMultiDict returned from
  the loaders might be like by just changing an import statement.

1.0.0-alpha.8 (2020-08-01)
--------------------------
* Renamed the _collections module to just collections.
* Renamed the Units class to Quantity (Units remains, but has a deprecation warning).
* Defined a new ABC: pvl.collections.MutableMappingSequence
* More detail for these changes can be found in Issue #62.

1.0.0-alpha.7 (2020-07-29)
--------------------------
* Created a new exceptions.py module and grouped all pvl Exceptions
  there.  Addresses #58
* Altered the message that LexerError emits to provide context
  around the character that caused the error.
* Added bump2version configuration file.

1.0.0-alpha.6 (2020-07-27)
--------------------------
* Enforced that all datetime.time and datetime.datetime objects
  returned should be timezone "aware."  This breaks 0.x functionality
  where some were and some weren't.  Addresses #57.


1.0.0-alpha.5 (2020-05-30)
--------------------------
* ISIS creates PVL text with unquoted plus signs ("+"), needed to adjust
  the ISISGrammar and OmniGrammar objects to parse this properly (#59).
* In the process of doing so, realized that we have some classes that
  optionally take a grammar and a decoder, and if they aren't given, to default.
  However, a decoder *has* a grammar object, so if a grammar isn't provided, but
  a decoder is, the grammar should be taken from the decoder, otherwise you
  could get confusing behavior.
* Updated pvl_validate to be explicit about these arguments.
* Added a --version argument to both pvl_translate and pvl_validate.

1.0.0.-alpha.4 (2020-05-29)
---------------------------
* Added the pvl.loadu() function as a convenience function to load PVL text from
  URLs.

1.0.0-alpha.3 (2020-05-28)
--------------------------
* Implemented tests in tox and Travis for Python 3.8, and discovered a bug
  that we fixed (#54).

1.0.0-alpha.2 (2020-04-18)
--------------------------
* The ability to deal with 3rd-party 'quantity' objects like astropy.units.Quantity
  and pint.Quantity was added and documented, addresses #22.

1.0.0-alpha.1 (2020-04-17)
--------------------------
This is a bugfix on 1.0.0-alpha to properly parse scientific notation
and deal with properly catching an error.


1.0.0-alpha (winter 2019-2020)
------------------------------
This is the alpha version of release 1.0.0 for pvl, and the items
here and in other 'alpha' entries may be consolidated when 1.0.0
is released.  This work is categorized as 1.0.0-alpha because
backwards-incompatible changes are being introduced to the codebase.

* Refactored code so that it will no longer support Python 2, 
  and is only guaranteed to work with Python 3.6 and above.
* Rigorously implemented the three dialects of PVL text: PVL itself,
  ODL, and the PDS3 Label Standard.  There is a fourth de-facto
  dialect, that of ISIS cube labels that is also handled.  These
  dialects each have their own grammars, parsers, decoders, and
  encoders, and there are also some 'Omni' versions of same that
  handle the widest possible range of PVL text.
* When parsing via the loaders, ``pvl`` continues to consume as
  wide a variety of PVL text as is reasonably possible, just like
  always.  However, now when encoding via the dumpers, ``pvl`` will
  default to writing out PDS3 Label Standard format PVL text, one
  of the strictest dialects, but other options are available.  This
  behavior is different from the pre-1.0 version, which wrote out 
  more generic PVL text.
* Removed the dependency on the ``six`` library that provided Python 2
  compatibility.
* Removed the dependency on the ``pytz`` library that provided 'timezone'
  support, as that functionality is replaced with the Standard Library's
  ``datetime`` module.
* The private ``pvl/_numbers.py`` file was removed, as its capability is now
  accomplished with the Python Standard Library.
* The private ``pvl/_datetimes.py`` file was removed, as its capability is now
  accomplished with the Standard Library's ``datetime`` module.
* the private ``pvl/_strings.py`` file was removed, as its capabilities are now
  mostly replaced with the new grammar module and some functions in other new
  modules.
* Internally, the library is now working with string objects, not byte literals, 
  so the ``pvl/stream.py`` module is no longer needed.
* Added an optional dependency on the 3rd party ``dateutil`` library, to parse
  more exotic date and time formats.  If this library is not present, the
  ``pvl`` library will gracefully fall back to not parsing more exotic
  formats. 
* Implmented a more formal approach to parsing PVL text:  The properties
  of the PVL language are represented by a grammar object.  A string is
  broken into tokens by the lexer function.  Those tokens are parsed by a
  parser object, and when a token needs to be converted to a Python object,
  a decoder object does that job.  When a Python object must be converted to
  PVL text, an encoder object does that job.
* Since the tests in ``tests/test_decoder.py`` and ``tests/test_encoder.py``
  were really just exercising the loader and dumper functions, those tests were
  moved to ``tests/test_pvl.py``, but all still work (with light modifications for
  the new defaults).  Unit tests were added for most of the new classes and
  functions.  All docstring tests now also pass doctest testing and are now
  included in the ``make test`` target.
* Functionality to correctly parse dash (-) continuation lines written by ISIS
  as detailed in #34 is implemented and tested.
* Functionality to use ``pathlib.Path`` objects for ``pvl.load()`` and
  ``pvl.dump()`` as requested in #20 and #31 is implemented and tested.
* Functionality to accept already-opened file objects that were opened in 
  'r' mode or 'rb' mode as alluded to in #6 is implemented and tested.
* The library now properly parses quoted strings that include backslashes
  as detailed in #33.
* Utility programs pvl_validate and pvl_translate were added.
* Documentation was updated and expanded.

0.3.0 (2017-06-28)
------------------

* Create methods to add items to the label
* Give user option to allow the parser to succeed in parsing broken labels

0.2.0 (2015-08-13)
------------------

* Drastically increase test coverage.
* Lots of bug fixes.
* Add Cube and PDS encoders.
* Cleanup README.
* Use pvl specification terminology.
* Added element access by index and slice.

0.1.1 (2015-06-01)
------------------

* Fixed issue with reading Pancam PDS Products.

0.1.0 (2015-05-30)
------------------

* First release on PyPI.
