===============================
pvl
===============================

.. image:: https://badge.fury.io/py/pvl.svg
    :target: http://badge.fury.io/py/pvl

.. image:: https://travis-ci.org/planetarypy/pvl.svg?branch=master
        :target: https://travis-ci.org/planetarypy/pvl

.. image:: https://pypip.in/d/pvl/badge.png
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

    $ pip install gnsq


Basic Usage
-----------

Decoding pvl modules::

    >>> import pvl
    >>> module = pvl.loads("""
    ...   foo = bar
    ...   items = (1, 2, 3)
    ...   END
    ... """)
    >>> print module
    PVLModule([
      (u'foo', u'bar')
      (u'items', [1, 2, 3])
    ])
    >>> print module['foo']
    bar

Encoding pvl modules::

    >>> import pvl
    >>> print pvl.dumps({
    ...   'foo': 'bar',
    ...   'items': [1, 2, 3]
    ... })
    items = (1, 2, 3)
    foo = bar
    END

Building pvl modules::

    >>> import pvl
    >>> module = pvl.PVLModule({'foo': 'bar'})
    >>> module.append('items', [1, 2, 3])
    >>> print pvl.dumps(module)
    foo = bar
    items = (1, 2, 3)
    END

.. _PlanetaryPy Toolkit: https://github.com/planetarypy
.. _USGS Isis Cube Label: http://isis.astrogeology.usgs.gov/
.. _NASA PDS 3 Label: https://pds.nasa.gov
