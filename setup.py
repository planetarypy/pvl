#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='pvl',
    version='1.3.0',
    description=(
        'Python implementation for PVL (Parameter Value Language) '
        'parsing and encoding.'
    ),
    long_description=readme + '\n\n' + history,
    author='The PlanetaryPy Developers',
    maintainer="Ross Beyer",
    maintainer_email="rbeyer@rossbeyer.net",
    url='https://github.com/planetarypy/pvl',
    packages=[
        'pvl',
    ],
    package_dir={'pvl':
                 'pvl'},
    include_package_data=True,
    license="BSD",
    zip_safe=False,
    keywords='pvl',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Text Processing'
    ],
    extras_require={
        "allopts": ["astropy", "multidict", "pint", "python-dateutil"],
        "dateutil":  ["python-dateutil"],
        "multidict": ["multidict"],
        "quantities": ["astropy", "pint"],
    },
    entry_points={"console_scripts": [
        "pvl_translate = pvl.pvl_translate:main",
        "pvl_validate= pvl.pvl_validate:main",
    ], }
)
