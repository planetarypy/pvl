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
    version='0.3.0',
    description='Python implementation of PVL (Parameter Value Language)',
    long_description=readme + '\n\n' + history,
    author='The PlanetaryPy Developers',
    author_email='trevor@heytrevor.com',
    url='https://github.com/planetarypy/pvl',
    packages=[
        'pvl',
    ],
    package_dir={'pvl':
                 'pvl'},
    include_package_data=True,
    install_requires=[
        'pytz',
        'six',
    ],
    license="BSD",
    zip_safe=False,
    keywords='pvl',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
