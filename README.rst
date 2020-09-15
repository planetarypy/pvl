===============================
pvl
===============================

.. image:: https://readthedocs.org/projects/pvl/badge/?version=latest
        :target: https://pvl.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://img.shields.io/travis/planetarypy/pvl.svg?style=flat-square
        :target: https://travis-ci.org/planetarypy/pvl
        :alt: Travis Build Status

.. image:: https://img.shields.io/pypi/v/pvl.svg?style=flat-square
        :target: https://pypi.python.org/pypi/pvl
        :alt: PyPI version

.. image:: https://img.shields.io/pypi/dm/pvl.svg?style=flat-square
        :target: https://pypi.python.org/pypi/pvl
        :alt: PyPI Downloads/month

.. image:: https://img.shields.io/conda/vn/conda-forge/pvl.svg
        :target: https://anaconda.org/conda-forge/pvl
        :alt: conda-forge version

.. image:: https://img.shields.io/conda/dn/conda-forge/pvl.svg
        :target: https://anaconda.org/conda-forge/pvl
        :alt: conda-forge downloads


Python implementation of a PVL (Parameter Value Language) library.

* Free software: BSD license
* Documentation: http://pvl.readthedocs.org.
* Support for Python 3.6 and higher (avaiable via pypi and conda).
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

Installing ``pvl`` from the conda-forge channel can be achieved by adding
conda-forge to your channels with::

    conda config --add channels conda-forge


Once the conda-forge channel has been enabled, ``pvl`` can be installed with::

    conda install pvl

It is possible to list all of the versions of ``pvl`` available on your platform
with::

    conda search pvl --channel conda-forge


Basic Usage
-----------

``pvl`` exposes an API familiar to users of the standard library
``json`` module.

Decoding is primarily done through ``pvl.load()`` for file-like objects and
``pvl.loads()`` for strings::

    >>> import pvl
    >>> module = pvl.loads("""
    ...     foo = bar
    ...     items = (1, 2, 3)
    ...     END
    ... """)
    >>> print(module)
    PVLModule([
      ('foo', 'bar')
      ('items', [1, 2, 3])
    ])
    >>> print(module['foo'])
    bar

There is also a ``pvl.loadu()`` to which you can provide the URL of a file that you would normally provide to
``pvl.load()``.

You may also use ``pvl.load()`` to read PVL text directly from an image_ that begins with PVL text::

    >>> import pvl
    >>> label = pvl.load('tests/data/pattern.cub')
    >>> print(label)
    PVLModule([
      ('IsisCube',
       {'Core': {'Dimensions': {'Bands': 1,
                                'Lines': 90,
                                'Samples': 90},
                 'Format': 'Tile',
                 'Pixels': {'Base': 0.0,
                            'ByteOrder': 'Lsb',
                            'Multiplier': 1.0,
                            'Type': 'Real'},
                 'StartByte': 65537,
                 'TileLines': 128,
                 'TileSamples': 128}})
      ('Label', PVLObject([
        ('Bytes', 65536)
      ]))
    ])
    >>> print(label['IsisCube']['Core']['StartByte'])
    65537


Similarly, encoding Python objects as PVL text is done through
``pvl.dump()`` and ``pvl.dumps()``::

    >>> import pvl
    >>> print(pvl.dumps({
    ...     'foo': 'bar',
    ...     'items': [1, 2, 3]
    ... }))
    FOO   = bar
    ITEMS = (1, 2, 3)
    END
    <BLANKLINE>

``pvl.PVLModule`` objects may also be pragmatically built up
to control the order of parameters as well as duplicate keys::

    >>> import pvl
    >>> module = pvl.PVLModule({'foo': 'bar'})
    >>> module.append('items', [1, 2, 3])
    >>> print(pvl.dumps(module))
    FOO   = bar
    ITEMS = (1, 2, 3)
    END
    <BLANKLINE>

A ``pvl.PVLModule`` is a ``dict``-like container that preserves
ordering as well as allows multiple values for the same key. It provides
similar semantics to a ``list`` of key/value ``tuples`` but 
with ``dict``-style access::

    >>> import pvl
    >>> module = pvl.PVLModule([
    ...     ('foo', 'bar'),
    ...     ('items', [1, 2, 3]),
    ...     ('foo', 'remember me?'),
    ... ])
    >>> print(module['foo'])
    bar
    >>> print(module.getlist('foo'))
    ['bar', 'remember me?']
    >>> print(module.items())
    ItemsView(PVLModule([
      ('foo', 'bar')
      ('items', [1, 2, 3])
      ('foo', 'remember me?')
    ]))
    >>> print(pvl.dumps(module))
    FOO   = bar
    ITEMS = (1, 2, 3)
    FOO   = 'remember me?'
    END
    <BLANKLINE>

However, there are some aspects to the default ``pvl.PVLModule`` that are not entirely
aligned with the modern Python 3 expectations of a Mapping object.  If you would like
to experiment with a more Python-3-ic object, you could instantiate a
``pvl.collections.PVLMultiDict`` object, or ``import pvl.new as pvl`` in your code
to have the loaders return objects of this type (and then easily switch back by just
changing the import statement).  To learn more about how PVLMultiDict is different
from the existing OrderedMultiDict that PVLModule is derived from, please read the
new PVLMultiDict documentation.

The intent is for the loaders (``pvl.load()``, ``pvl.loads()``, and ``pvl.loadu()``)
to be permissive, and attempt to parse as wide a variety of PVL text as
possible, including some kinds of 'broken' PVL text.

On the flip side, when dumping a Python object to PVL text (via
``pvl.dumps()`` and ``pvl.dump()``), the library will default
to writing PDS3-Standards-compliant PVL text, which in some ways
is the most restrictive, but the most likely version of PVL text
that you need if you're writing it out (this is different from
pre-1.0 versions of ``pvl``).

You can change this behavior by giving different parameters to the
loaders and dumpers that define the grammar of the PVL text that
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
