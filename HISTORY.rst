.. :changelog:

=========
 History
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

When updating this file, please add an entry for your change under
`Not Yet Released`_ and one of the following headings:

- Added - for new features.
- Changed - for changes in existing functionality.
- Deprecated - for soon-to-be removed features.
- Removed - for now removed features.
- Fixed - for any bug fixes.
- Security - in case of vulnerabilities.

If the heading does not yet exist under `Not Yet Released`_, then add it
as a 3rd level heading, underlined with pluses (see examples below).

When preparing for a public release add a new 2nd level heading,
underlined with dashes under `Not Yet Released`_ with the version number
and the release date, in year-month-day format (see examples below).


Not Yet Released
----------------

Fixed
+++++
* If there was a bare token in the PVL-text (i.e. a parameter with no value assignment),
  the returned error message was difficult to understand, should now be clear that
  it was looking for an equals sign, and didn't find one (Issue 108).
* Just importing the pvl library would emit the PendingDeprecationWarning about the Units
  class, even if a user did not import or instantiate the Units class.
  The warn() was not properly issued from the __init__() function, it now is (Issue 109).


1.3.2 (2022-02-05)
------------------

Fixed
+++++
* The parser was requesting the next token after an end-statement, even
  though nothing was done with this token (in the future it could
  be a comment that should be processed).  In the very rare case
  where all of the "data" bytes in a file with an attached PVL label
  (like a .IMG or .cub file) actually convert to UTF with no
  whitespace characters, that next token will take an unacceptable
  amount of time to return, if it does at all.  The parser now does
  not request additional tokens once an end-statement is identified
  (Issue 104).


1.3.1 (2022-02-05)
------------------

Fixed
+++++
* Deeply nested Aggregation Blocks (Object or Group) which had mis-matched
  Block Names should now properly result in LexerErrors instead of
  resulting in StopIteration Exceptions (Issue 100).

* The default "Omni" parsing strategy, now considers the ASCII NULL character
  ("\0") a "reserved character." The practical effect is that the
  ASCII NULL can not be in parameter names or unquoted strings (but
  would still be successfully parsed in quoted strings). This means
  that PVL-text that might have incorrectly used ASCII NULLs as
  delimiters will once again be consumed by our omnivorous parser
  (Issue 98).


1.3.0 (2021-09-10)
------------------

Added
+++++
* pvl.collections.Quantity objects now have __int__() and __float__()
  functions that will return the int and float versions of their
  .value parameter to facilitate numeric operations with Quantity
  objects (Issue 91).
* pvl.load() now has an `encoding=` parameter that is identical in usage
  to the parameter passed to `open()`, and will attempt to decode the whole
  file as if it had been encoded thusly.  If it encounters a decoding error,
  it will fall back to decoding the bytes one at a time as ASCII text (Issue 93).

Fixed
+++++
* If the PVL-text contained characters beyond the set allowed by the
  PVL specification, the OmniGrammar would refuse to parse them.
  This has been fixed to allow any valid character to be parsed,
  so that if there are weird UTF characters in the PVL-text, you'll get
  those weird UTF characters in the returned dict-like.  When the
  stricter PVL, ODL, or PDS3 dialects are used to "load" PVL-text,
  they will properly fail to parse this text (Issue 93).
* Empty parameters inside groups or objects (but not at the end), would
  cause the default "Omni" parsing strategy to go into an infinite
  loop.  Empty parameters in PVL, ODL, and PDS3 continue to not be
  allowed (Issue 95).


1.2.1 (2021-05-31)
------------------

Added
+++++
* So many tests, increased coverage by about 10%.

Fixed
+++++
* Attempting to import `pvl.new` without *multidict* being available,
  will now properly yield an ImportError.
* The `dump()` and `dumps()` functions now properly overwritten in `pvl.new`.
* All encoders that descended from PVLEncoder didn't properly have group_class and
  object_class arguments to their constructors, now they do.
* The `char_allowed()` function in grammar objects now raises a more useful ValueError
  than just a generic Exception.
* The new `collections.PVLMultiDict` wasn't correctly inserting Mapping objects with
  the `insert_before()` and `insert_after()` methods.
* The `token.Token` class's `__index__()` function didn't always properly return an
  index.
* The `token.Token` class's `__float__()` function would return int objects if the
  token could be converted to int.  Now always returns floats.


1.2.0 (2021-03-27)
------------------

Added
+++++
* Added a default_timezone parameter to grammar objects so that they could
  both communicate whether they had a default timezone (if not None),
  and what it was.
* Added a pvl.grammar.PDSGrammar class that specifies the default UTC
  time offset.
* Added a pvl.decoder.PDSLabelDecoder class that properly enforces only
  milisecond time precision (not microsecond as ODL allows), and does
  not allow times with a +HH:MM timezone specifier.  It does assume
  any time without a timezone specifier is a UTC time.
* Added a ``real_cls`` parameter to the decoder classes, so that users can specify
  an arbitrary type with which real numbers in the PVL-text could be returned in
  the dict-like from the loaders (defaults to ``float`` as you'd expect).
* The encoders now support a broader range of real types to complement the decoders.

Changed
+++++++
* Improved some build and test functionality.
* Moved the is_identifier() static function from the ODLEncoder to the ODLDecoder
  where it probably should have always been.


Fixed
+++++
* Very long Python ``str`` objects that otherwise qualified as ODL/PDS3 Symbol Strings,
  would get written out with single-quotes, but they would then be split across lines
  via the formatter, so they should be written as Text Strings with double-quotes.
  Better protections have been put in place.
* pvl.decoder.ODLDecoder now will return both "aware" and "naive"
  datetime objects (as appropriate) since "local" times without a
  timezone are allowed under ODL.
* pvl.decoder.ODLDecoder will now properly reject any unquoted string
  that does not parse as an ODL Identifier.
* pvl.decoder.ODLDecoder will raise an exception if there is a seconds value
  of 60 (which the PVLDecoder allows)
* pvl.encoder.ODLEncoder will raise an exception if given a "naive" time
  object.
* pvl.encoder.PDSLabelEncoder will now properly raise an exception if
  a time or datetime object cannot be represented with only milisecond
  precision.


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
