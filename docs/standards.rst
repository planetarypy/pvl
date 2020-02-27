==========================
Standards & Specifications
==========================

Although many people use the term 'PVL' to describe parameter-value
text, they are often unaware that there are at least four different
'dialects' or 'flavors' of 'PVL'.  They are described below.

Unfortunately one of them is actually named PVL, so it is difficult
to distinguish when someone is using "PVL" to refer to the formal
specification versus when they are using "PVL" to refer to some
text that could be parsable as PVL.

In the documentation for this library, we will attempt to provide
enough context for you to distinguish, but we will typically use
"PVL text" to refer to some generic text that may or may not conform
to one of the PVL 'dialects' or that could be converted into one
of them.  We will also use ``pvl`` to refer to this Python library.

In practice, since people are not typcially aware of the formal PVL
specification, when most people say "PVL" they are referring to
generic "PVL text."


------------------------------
Parameter Value Language (PVL)
------------------------------

The definition of the Parameter Value Language (PVL) is based on
the Consultive Committee for Space Data Systems, and their
:download:`Parameter Value Language Specification (CCSD0006 and
CCSD0008), CCSDS 6441.0-B-2 <CCSDS-641.0-B-2-PVL.pdf>` referred to
as the Blue Book with a date of June 2000.

This formal definition of PVL is quite permissive, and usually forms
the base class of objects in this library.


---------------------------------
Object Description Language (ODL)
---------------------------------

The Object Description Language (ODL) is based on PVL, but adds
additional restrictions.  It is defined in the :download:`PDS3 Standards
Reference (version 3.8, 27 Feb 2009) Chapter 12: Object Description
Language Specification and Usage <PDS3-3.8-20090227-Ch12-ODL.pdf>`.

However, even though ODL is specified by the PDS, by itself, it is
not the definition that PDS3 labels should conform to.  By and
large, as a user, you are rarely interested in the ODL specification,
and mostly want to deal with the PDS3 Standard.


-------------
PDS3 Standard
-------------

The PDS3 Standard is also defined in the PDS3 Standards Reference
(version 3.8, 27 Feb 2009) Chapter 12: Object Description Language
Specification.  The PDS3 Standard are mostly additional restrictions
on the base definition of ODL, and appear as additional notes or
sections in the document.


----------------------
ISIS Cube Label format
----------------------

The ISIS software has used a custom implementation (through at least
ISIS 3.9) to write PVL text into the labels of its cube files.  This
PVL text does not strictly follow any of the published standards.
It was based on PDS3 ODL from the 1990s, but has some extensions
adopted from existing and prior data sets from ISIS2, PDS, JAXA,
ISRO, etc., and extensions used only within ISIS3 files (.cub,
.net).  This is one of the reasons using ISIS cube files as an
archive format or PVL text written by ISIS as a submission to the 
PDS has been strongly discouraged.

Since there is no specification, only a detailed analysis of the ISIS
software that writes its PVL text would yield a strategy for parsing it.

At this time, the loaders (:func:`pvl.loads` and :func:`pvl.load`)
default to using the :class:`pvl.parser.OmniParser` which should
be able to parse most forms of PVL text that ISIS writes out or
into its cube labels. However, this is very likely where a user
could run into errors (if there is something that isn't supported),
and we welcome bug reports to help extend our coverage of this
flavor of PVL text.
