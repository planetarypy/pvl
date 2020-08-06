============================
Quantities: Values and Units
============================

The PVL specifications supports the notion that PVL Value Expressions
can contain an optional PVL Units Expression that follows the PVL
Value.  This combination of information: a value followed by a unit
can be represented by a single object that we might call a quantity.

There is no fundamental Python object type that represents a value
and the units of that value. However, libraries like ``astropy``
and ``pint`` have implemented "quantity" objects (and managed to
name them both Quantity, but they have slightly different interfaces).
In order to avoid optional dependencies, the ``pvl`` library provides
the :class:`pvl.collections.Quantity` class, implemented as a
:class:`collections.namedtuple` with a ``value`` and a ``unit``
parameter.  However, the ``unit`` parameter is just a string and
so the ``pvl`` quantity objects doesn't have the super-powers that
the ``astropy`` and ``pint`` quntity objects do.

By default, this means that when PVL text is parsed by :func:`pvl.load`
or :func:`pvl.loads` and when a PVL Value followed by a PVL Units
Expression is encountered, a :class:`pvl.collections.Quantity` object
will be placed in the returned dict-like.

Likewise when :func:`pvl.dump` or :func:`pvl.dumps` encounters a
:class:`pvl.collections.Quantity` its value and units will be serialized
with the right PVL syntax.

However, the ``pvl`` library also supports the use of other quantity
objects.

--------------------------------------------
Getting other quantity objects from PVL text
--------------------------------------------

In order to get the parsing side of the ``pvl`` library to return
a particular kind of quantity object when a PVL Value followed by
a PVL Units Expression is found, you must pass the name of that
quantity class to the decoder's ``quantity_cls`` argument.  This
quantity class's constructor must take two arguments, where the
first will receive the PVL Value (as whatever Python type ``pvl``
determines it to be) and the second will receive the PVL Units
Expression (as a ``str``).

Examples of how to do this with :func:`pvl.load` or :func:`pvl.loads`
are below for ``astropy`` and ``pint``.

Depending on the PVL text that you are parsing, and the quantity
class that you are using, you may get errors if the quantity class
can't accept the PVL Units Expression, or if the *value* part of
the quantity class can't handle all of the possible types of PVL
Values (which can be Simple Values, Sets, or Sequences).


----------------------------------------------
Writing out other quantity objects to PVL text
----------------------------------------------

In order to get the encoding side of the ``pvl`` library to write out the
correct kind of PVL text based on some quantity object is more difficult 
due to the wide variety of ways that quantity objects are written in 3rd 
party libaries.  At this time, the ``pvl`` library can properly encode
:class:`pvl.collecitons.Quantity`, :class:`astropy.units.Quantity`, and
:class:`pint.Quantity` objects (or objects that pass an ``isinstance()``
test for those objects).  Any other kind of quantity object in the 
data structure passed to :func:`pvl.dump` or :func:`pvl.dumps` will
just be encoded as a string.

Other types are possible, but require additions to the encoder in
use.  The :class:`astropy.units.Quantity` object is already handled
by the ``pvl`` library, but if it wasn't, this is how you would
enable it.  You just need the class name, the name of the
property on the class that yields the value or magnitude (for
:class:`astropy.units.Quantity` that is ``value``), and the property
that yields the units (for :class:`astropy.units.Quantity` that is
``unit``).  With those pieces in hand, we just need to instantiate
an encoder and add the new quantity class and the names of those
properties to it, and then pass it to :func:`pvl.dump` or
:func:`pvl.dumps` as follows::

 >>> import pvl
 >>> from astropy import units as u
 >>> my_label = dict(length=u.Quantity(15, u.m), velocity=u.Quantity(0.5, u.m / u.s))
 >>> my_encoder = pvl.PDSLabelEncoder()
 >>> my_encoder.add_quantity_cls(u.Quantity, 'value', 'unit')
 >>> print(pvl.dumps(my_label, encoder=my_encoder))
 LENGTH   = 15.0 <m>
 VELOCITY = 0.5 <m / s>
 END
 <BLANKLINE>



----------------------
astropy.units.Quantity
----------------------

The Astropy Project has classes for handing `Units and Quantities
<https://docs.astropy.org/en/stable/units/>`_.

The :class:`astropy.units.Quantity` object can be returned in the data
structure returned from :func:`pvl.load` or :func:`pvl.loads`.  Here is
an example::

 >>> import pvl
 >>> pvl_text = "length = 42 <m/s>"
 >>> regular = pvl.loads(pvl_text)
 >>> print(regular['length'])
 Quantity(value=42, units='m/s')
 >>> print(type(regular['length']))
 <class 'pvl.collections.Quantity'>

 >>> from pvl.decoder import OmniDecoder
 >>> from astropy import units as u
 >>> w_astropy = pvl.loads(pvl_text, decoder=OmniDecoder(quantity_cls=u.Quantity))
 >>> print(w_astropy)
 PVLModule([
   ('length', <Quantity 42. m / s>)
 ])
 >>> print(type(w_astropy['length']))
 <class 'astropy.units.quantity.Quantity'>

However, in our example file and in other files you may parse, the
units may be in upper case (e.g. KM, M), and by default, astropy will
not recognize the name of these units.  It will raise a handy
exception, which, in turn, will be raised as a
:class:`pvl.parser.QuantityError` that will look like this::

    pvl.parser.QuantityError: 'KM' did not parse as unit: At col
    0, KM is not a valid unit. Did you mean klm or km? If this is
    meant to be a custom unit, define it with 'u.def_unit'. To have
    it recognized inside a file reader or other code, enable it
    with 'u.add_enabled_units'. For details, see
    http://docs.astropy.org/en/latest/units/combining_and_defining.html

So, in order to parse our file, do this::

 >>> import pvl
 >>> from pvl.decoder import OmniDecoder
 >>> from astropy import units as u
 >>> pvl_file = 'tests/data/pds3/units1.lbl'
 >>> km_upper = u.def_unit('KM', u.km)
 >>> m_upper = u.def_unit('M', u.m)
 >>> u.add_enabled_units([km_upper, m_upper])  #doctest: +ELLIPSIS
 <astropy.units.core._UnitContext object at ...
 >>> label = pvl.load(pvl_file, decoder=OmniDecoder(quantity_cls=u.Quantity))
 >>> print(label)
 PVLModule([
   ('PDS_VERSION_ID', 'PDS3')
   ('MSL:COMMENT', 'THING TEST')
   ('FLOAT_UNIT', <Quantity 0.414 KM>)
   ('INT_UNIT', <Quantity 4. M>)
 ])
 >>> print(type(label['FLOAT_UNIT']))
 <class 'astropy.units.quantity.Quantity'>


Similarly, :class:`astropy.units.Quantity` objects can be encoded to PVL text
by :func:`pvl.dump` or :func:`pvl.dumps` without any particular special handling.
Here is an example::

 >>> import pvl
 >>> from astropy import units as u
 >>> my_label = dict(length=u.Quantity(15, u.m), velocity=u.Quantity(0.5, u.m / u.s))
 >>> print(pvl.dumps(my_label))
 LENGTH   = 15.0 <m>
 VELOCITY = 0.5 <m / s>
 END
 <BLANKLINE>


-------------
pint.Quantity
-------------
The `Pint library <http://pint.readthedocs.org>`_ also deals with quantities.

The :class:`pint.Quantity` object can also be returned in the data
structure returned from :func:`pvl.load` or :func:`pvl.loads` if you 
would prefer to use those objects.  Here is an example::

 >>> import pvl
 >>> pvl_text = "length = 42 <m/s>"
 >>> from pvl.decoder import OmniDecoder
 >>> import pint
 >>> w_pint = pvl.loads(pvl_text, decoder=OmniDecoder(quantity_cls=pint.Quantity))
 >>> print(w_pint)
 PVLModule([
   ('length', <Quantity(42, 'meter / second')>)
 ])
 >>> print(type(w_pint['length']))
 <class 'pint.quantity.Quantity'>

Just as with :class:`astropy.units.Quantity`, :class:`pint.Quantity` doesn't recognize
the upper case units, and will raise an error like this::

    pint.errors.UndefinedUnitError: 'KM' is not defined in the unit registry

So, in order to parse our file with uppercase units, you can create
a units definition file to add aliases and units to the pint
'registry'. When doing this programmatically note that if you define
a registry on-the-fly, you must use the registry's Quantity to the
``quantity_cls`` argument::

 >>> import pvl
 >>> from pvl.decoder import OmniDecoder
 >>> import pint
 >>> ureg = pint.UnitRegistry()
 >>> ureg.define('kilo- = 1000 = K- = k-')
 >>> ureg.define('@alias meter = M')
 >>> pvl_file = 'tests/data/pds3/units1.lbl'
 >>> label = pvl.load(pvl_file, decoder=OmniDecoder(quantity_cls=ureg.Quantity))
 >>> print(label)
 PVLModule([
   ('PDS_VERSION_ID', 'PDS3')
   ('MSL:COMMENT', 'THING TEST')
   ('FLOAT_UNIT', <Quantity(0.414, 'kilometer')>)
   ('INT_UNIT', <Quantity(4, 'meter')>)
 ])
 >>> print(type(label['FLOAT_UNIT']))
 <class 'pint.quantity.build_quantity_class.<locals>.Quantity'>

Similarly, :class:`pint.Quantity` objects can be encoded to PVL text
by :func:`pvl.dump` or :func:`pvl.dumps`::

 >>> import pvl
 >>> import pint
 >>> ureg = pint.UnitRegistry()
 >>> dist = 15 * ureg.m
 >>> vel = 0.5 * ureg.m / ureg.second
 >>> my_label = dict(length=dist, velocity=vel)
 >>> print(pvl.dumps(my_label))
 LENGTH   = 15 <meter>
 VELOCITY = 0.5 <meter / second>
 END
 <BLANKLINE>
