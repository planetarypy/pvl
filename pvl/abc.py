# -*- coding: utf-8 -*-
"""Parameter Value Language abstract base classes.

The main kind of object that this library returns from the loaders
is a combination of Python's collections.abc.MutableMapping and
collections.abc.MutableSequence.
"""

# Copyright 2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

from collections.abc import MutableMapping, MutableSequence

class MutableMappingSequence(
    MutableMapping, MutableSequence
):
    """ABC for a mutable object that has both mapping and
    sequence characteristics.
    """
    pass
