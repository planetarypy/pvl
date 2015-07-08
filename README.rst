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
* Support for Python 2, 3 and pypi.
* Proudly part of the `PlanetaryPy Toolkit`_

PVL is a markup language, similar to xml, commonly employed for entries in the
Planetary Database System used by NASA to store mission data, among other uses.
This package supports both encoding a decoding a superset of PVL, including the
`USGS Isis Cube Label`_ and `NASA PDS 3 Label`_ dialects.


Installation
------------

At the command line::

    $ pip install pvl


Basic Usage
-----------

pvl exposes an API familiar to users of the standard library json module.

Decoding is primarily done through ``pvl.load`` for file like objects and
``pvl.loads`` for strings::

    >>> import pvl
    >>> module = pvl.loads("""
    ...     foo = bar
    ...     items = (1, 2, 3)
    ...     END
    ... """)
    >>> print module
    PVLModule([
      (u'foo', u'bar')
      (u'items', [1, 2, 3])
    ])
    >>> print module['foo']
    bar

You may also use ``pvl.load`` to read a label directly from an image_::

    >>> import pvl
    >>> label = pvl.load('pattern.cub')
    >>> print label
    PVLModule([
      (u'IsisCube',
       PVLObject([
        (u'Core',
         PVLObject([
          (u'StartByte', 65537)
          (u'Format', u'Tile')
    # output truncated...
    >>> print label['IsisCube']['Core']['StartByte']
    65537


Similarly, encoding pvl modules is done through ``pvl.dump`` and ``pvl.dumps``::

    >>> import pvl
    >>> print pvl.dumps({
    ...     'foo': 'bar',
    ...     'items': [1, 2, 3]
    ... })
    items = (1, 2, 3)
    foo = bar
    END

``PVLModule`` objects may also be pragmatically built up to control the order
of parameters as well as duplicate keys::

    >>> import pvl
    >>> module = pvl.PVLModule({'foo': 'bar'})
    >>> module.append('items', [1, 2, 3])
    >>> print pvl.dumps(module)
    foo = bar
    items = (1, 2, 3)
    END

A ``PVLModule`` is a ``dict`` like container that preserves ordering as well as
allows multiple values for the same key. It provides a similar similar semantics
to a ``list`` of key/value ``tuples`` but with ``dict`` style access::

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
    [('foo', 'bar'), ('items', [1, 2, 3]), ('foo', u'remember me?')]
    >>> print pvl.dumps(module)
    foo = bar
    items = (1, 2, 3)
    foo = "remember me?"
    END

For more information on custom serilization and deseralization see the
`full documentation`_.


Contributing
------------

Feedback, issues, and contributions are always gratefully welcomed. See the
`contributing guide`_ for details on how to help and setup a development
environment.


.. _PlanetaryPy Toolkit: https://github.com/planetarypy
.. _USGS Isis Cube Label: http://isis.astrogeology.usgs.gov/
.. _NASA PDS 3 Label: https://pds.nasa.gov
.. _image: https://github.com/planetarypy/pvl/raw/master/tests/data/pattern.cub
.. _full documentation: http://pvl.readthedocs.org
.. _contributing guide: https://github.com/planetarypy/pvl/blob/master/CONTRIBUTING.rst
