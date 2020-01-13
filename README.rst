===============================
pvl
===============================

.. image:: https://img.shields.io/pypi/v/pvl.svg?style=flat-square
    :target: https://pypi.python.org/pypi/pvl

.. image:: https://img.shields.io/travis/planetarypy/pvl.svg?style=flat-square
        :target: https://travis-ci.org/planetarypy/pvl

.. image:: https://img.shields.io/pypi/dm/pvl.svg?style=flat-square
        :target: https://pypi.python.org/pypi/pvl

Python implementation of PVL (Parameter Value Language)

* Free software: BSD license
* Documentation: http://pvl.readthedocs.org.
* Support for Python 3.6 and higher (avaiable via pypi).
* `PlanetaryPy`_ Affiliate Package.

PVL is a markup language, similar to XML, commonly employed for
entries in the Planetary Database System used by NASA to store
mission data, among other uses.  This package supports both encoding
and decoding a variety of PVL 'flavors' including PVL itself, ODL,
`NASA PDS 3 Labels`_, and `USGS ISIS Cube Labels`_.


Installation
------------

Can either install with pip or with conda.

To install with pip, at the command line::

    $ pip install pvl

Directions for installing with conda-forge:

Installing pvl from the conda-forge channel can be achieved by adding
conda-forge to your channels with::

    conda config --add channels conda-forge


Once the conda-forge channel has been enabled, pvl can be installed with::

    conda install pvl

It is possible to list all of the versions of pvl available on your platform
with::

    conda search pvl --channel conda-forge


Basic Usage
-----------

pvl exposes an API familiar to users of the standard library :mod:`json` module.

Decoding is primarily done through :func:`pvl.load` for file like objects and
:func:`pvl.loads` for strings::

    >>> import pvl
    >>> module = pvl.loads("""
    ...     foo = bar
    ...     items = (1, 2, 3)
    ...     END
    ... """)
    >>> print module
    PVLModule([
      ('foo', 'bar')
      ('items', [1, 2, 3])
    ])
    >>> print module['foo']
    bar

You may also use :func:`pvl.load` to read a label directly from an image_::

    >>> import pvl
    >>> label = pvl.load('pattern.cub')
    >>> print label
    PVLModule([
      (u'IsisCube',
       PVLObject([
        (u'Core',
         PVLObject([
          ('StartByte', 65537)
          ('Format', 'Tile')
    # output truncated...
    >>> print label['IsisCube']['Core']['StartByte']
    65537


Similarly, encoding pvl modules is done through :func:`pvl.dump` and
:func:`pvl.dumps`::

    >>> import pvl
    >>> print pvl.dumps({
    ...     'foo': 'bar',
    ...     'items': [1, 2, 3]
    ... })
    items = (1, 2, 3)
    foo = bar
    END

:class:`pvl.PVLModule` objects may also be pragmatically built up
to control the order of parameters as well as duplicate keys::

    >>> import pvl
    >>> module = pvl.PVLModule({'foo': 'bar'})
    >>> module.append('items', [1, 2, 3])
    >>> print pvl.dumps(module)
    foo = bar
    items = (1, 2, 3)
    END

A :class:`pvl.PVLModule` is a :class:`dict`-like container that preserves
ordering as well as allows multiple values for the same key. It provides
similar semantics to a :class:`list` of key/value :class:`tuples` but 
with ``dict``-style access::

    >>> import pvl
    >>> module = pvl.PVLModule([
    ...     ('foo', 'bar'),
    ...     ('items', [1, 2, 3]),
    ...     ('foo', 'remember me?'),
    ... ])
    >>> print module['foo']
    bar
    >>> print module.getlist('foo')
    ['bar', 'remember me?']
    >>> print module.items()
    [('foo', 'bar'), ('items', [1, 2, 3]), ('foo', 'remember me?')]
    >>> print pvl.dumps(module)
    foo = bar
    items = (1, 2, 3)
    foo = "remember me?"
    END

The intent is for the loaders (:func:`pvl.load` and :func:`pvl.loads`)
to be permissive, and attempt to parse as wide a variety of PVL as
possible, including some kinds of 'broken' PVL.

On the flip side, when dumping a Python object to PVL text (via
:func:`pvl.dumps` and :func:`pvl.dump`), the library will default
to writing PDS 3-compliant PVL, which in some ways is the most
restrictive, but the most likely version of PVL that you need if
you're writing it out.

You can change this behavior by giving different parameters to the
loaders and dumpers that define the grammar of the PVL flavor that
you're interested in, as well as custom parsers, decoders, and
encoders.

For more information on custom serilization and deseralization see the
`full documentation`_.


Contributing
------------

Feedback, issues, and contributions are always gratefully welcomed. See the
`contributing guide`_ for details on how to help and setup a development
environment.


.. _PlanetaryPy: https://github.com/planetarypy
.. _USGS ISIS Cube Labels: http://isis.astrogeology.usgs.gov/
.. _NASA PDS 3 Labels: https://pds.nasa.gov
.. _image: https://github.com/planetarypy/pvl/raw/master/tests/data/pattern.cub
.. _full documentation: http://pvl.readthedocs.org
.. _contributing guide: https://github.com/planetarypy/pvl/blob/master/CONTRIBUTING.rst
