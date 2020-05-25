# -*- coding: utf-8 -*-
"""Parameter Value Language container datatypes providing enhancements
to Python general purpose built-in containers.

To enable efficient operations on parsed PVL text, we need an object
that acts as both a dict-like Mapping container and a list-like
Sequence container, essentially an ordered multi-dict.  There is
no existing object or even an Abstract Base Class in the Python
Standard Library for such an object.  So we define the
MutableMappingSequence ABC here, which is (as the name implies) an
abstract base class that implements both the Python MutableMapping
and Mutable Sequence ABCs. We also provide an implementation, the
OrderedMultiDict.

Additionally, for PVL Values which also have an associated PVL Units
Expression, they need to be returned as a quantity object which contains
both a notion of a value and the units for that value.  Again, there
is no fundamental Python type for a quantity, so we define the Quantity
class (formerly the Units class).
"""
# Copyright 2015, 2017, 2019-2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

import pprint
import warnings
from abc import abstractmethod
from collections import namedtuple, abc

from multidict import MultiDict


class MutableMappingSequence(
    abc.MutableMapping, abc.MutableSequence
):
    """ABC for a mutable object that has both mapping and
    sequence characteristics.

    Must implement `.getall()` and `.popall()` since MutableMappingSequence
    can have many values for a single key, while `.get(k)` and
    `.pop(k)` return and operate on a single value, the *all*
    versions return and operate on all values in the MutableMappingSequence
    with the key `k`.
    """

    @abstractmethod
    def append(self, key, value):
        pass

    @abstractmethod
    def getall(self, key):
        pass

    @abstractmethod
    def popall(self, key):
        pass


dict_setitem = dict.__setitem__
dict_getitem = dict.__getitem__
dict_delitem = dict.__delitem__
dict_contains = dict.__contains__
dict_clear = dict.clear


class MappingView(object):

    def __init__(self, mapping):
        self._mapping = mapping

    def __len__(self):
        return len(self._mapping)

    def __repr__(self):
        return '{!s}({!r})'.format(type(self).__name__, self._mapping)


class KeysView(MappingView):

    def __contains__(self, key):
        return key in self._mapping

    def __iter__(self):
        for key, _ in self._mapping:
            yield key

    def __getitem__(self, index):
        return self._mapping[index][0]

    def __repr__(self):
        keys = [key for key, _ in self._mapping]
        return '{!s}({!r})'.format(type(self).__name__, keys)

    def index(self, key):
        keys = [k for k, _ in self._mapping]
        return keys.index(key)


class ItemsView(MappingView):

    def __contains__(self, item):
        key, value = item
        return value in self._mapping.getlist(key)

    def __iter__(self):
        for item in self._mapping:
            yield item

    def __getitem__(self, index):
        return self._mapping[index]

    def index(self, item):
        items = [i for i in self._mapping]
        return items.index(item)


class ValuesView(MappingView):

    def __contains__(self, value):
        for _, v in self._mapping:
            if v == value:
                return True
        return False

    def __iter__(self):
        for _, value in self._mapping:
            yield value

    def __getitem__(self, index):
        return self._mapping[index][1]

    def __repr__(self):
        values = [value for _, value in self._mapping]
        return '{!s}({!r})'.format(type(self).__name__, values)

    def index(self, value):
        values = [val for _, val in self._mapping]
        return values.index(value)


class OrderedMultiDict(dict, MutableMappingSequence):
    """A ``dict`` like container.

    This container preserves the original ordering as well as
    allows multiple values for the same key. It provides similar
    semantics to a ``list`` of ``tuples`` but with ``dict`` style
    access.

    Using ``__setitem__`` syntax overwrites all fields with the
    same key and ``__getitem__`` will return the first value with
    the key.
    """

    def __init__(self, *args, **kwargs):
        self.__items = []
        self.extend(*args, **kwargs)

    def __setitem__(self, key, value):
        if key not in self:
            return self.append(key, value)

        dict_setitem(self, key, [value])
        iteritems = iter(self.__items)

        for index, (old_key, old_value) in enumerate(iteritems):
            if old_key == key:
                # replace first occurrence
                self.__items[index] = (key, value)
                break

        tail = [item for item in iteritems if item[0] != key]
        self.__items[index + 1:] = tail

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self.__items[key]
        return dict_getitem(self, key)[0]

    def __delitem__(self, key):
        dict_delitem(self, key)
        self.__items = [item for item in self.__items if item[0] != key]

    def __iter__(self):
        return iter(self.__items)

    def __len__(self):
        return len(self.__items)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        if len(self) != len(other):
            return False

        items1 = self.items()
        items2 = other.items()

        for ((key1, value1), (key2, value2)) in zip(items1, items2):
            if key1 != key2:
                return False

            if value1 != value2:
                return False

        return True

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        if not self.__items:
            return '{!s}([])'.format(type(self).__name__)

        lines = []
        for item in self.__items:
            for line in pprint.pformat(item).splitlines():
                lines.append('  ' + line)

        return "{!s}([\n{!s}\n])".format(type(self).__name__, '\n'.join(lines))

    get = abc.MutableMapping.get
    update = abc.MutableMapping.update

    def keys(self):
        return KeysView(self)

    def values(self):
        return ValuesView(self)

    def items(self):
        return ItemsView(self)

    def clear(self):
        dict_clear(self)
        self.__items = []

    def discard(self, key):
        try:
            del self[key]
        except KeyError:
            pass

    def append(self, key, value):
        """Adds a (name, value) pair, doesn't overwrite the value if
        it already exists.
        """
        self.__items.append((key, value))

        try:
            dict_getitem(self, key).append(value)
        except KeyError:
            dict_setitem(self, key, [value])

    def extend(self, *args, **kwargs):
        """Add key value pairs for an iterable."""
        if len(args) > 1:
            raise TypeError(f'expected at most 1 arguments, got {len(args)}')

        iterable = args[0] if args else None
        if iterable:
            if isinstance(iterable, abc.Mapping) or hasattr(iterable, 'items'):
                for key, value in iterable.items():
                    self.append(key, value)
            elif hasattr(iterable, 'keys'):
                for key in iterable.keys():
                    self.append(key, iterable[key])
            else:
                for key, value in iterable:
                    self.append(key, value)

        for key, value in kwargs.items():
            self.append(key, value)

    def getall(self, key) -> abc.Sequence:
        """Returns a list of all the values for a named field.
        Returns KeyError if the key doesn't exist.
        """
        return list(dict_getitem(self, key))

    def getlist(self, key) -> abc.Sequence:
        """Returns a list of all the values for the named field.
        Returns an empty list if the key doesn't exist.
        """
        warnings.warn(
            "The pvl.collections.OrderedMultiDict.getlist(k) function is "
            "deprecated in favor of .getall(), please begin using it, as "
            ".getlist() may be removed in the next major patch.",
            PendingDeprecationWarning
        )

        try:
            return self.getall(key)
        except KeyError:
            return []

    # Turns out that this super-class function, even though it doesn't have
    # a concept of multiple keys, clears out multiple elements with the key,
    # probably because of how __delitem__ is defined:
    popall = abc.MutableMapping.pop

    def pop(self, *args, **kwargs):
        """Removes all items with the specified *key*."""

        warnings.warn(
            "The pvl.collections.OrderedMultiDict.pop(k) function removes "
            "all keys with value k to be backwards compatible with the "
            "pvl 0.x architecture, despite the new concept in "
            "pvl.collections.MutableMappingSequence, this concept of "
            "operations for .pop(k) may change in future versions."
            "Consider using .popall(k) instead.",
            FutureWarning
        )

        return self.popall(*args, *kwargs)

    def popitem(self):
        if not self:
            raise KeyError('popitem(): {!s} '.format(type(self).__name__) +
                           'is empty')

        key, _ = item = self.__items.pop()
        values = dict_getitem(self, key)
        values.pop()

        if not values:
            dict_delitem(self, key)

        return item

    def copy(self):
        return type(self)(self)

    def insert(self, index: int, *args) -> None:
        """Inserts at the index given by *index*.

        The first positional argument will be taken as the
        *index*. If three arguments are given, the second will be taken
        as the *key*, and the third as the *value*.  If only two arguments are
        given, the second must be a two-element sequence, where the first will
        be the *key* and the second the *value*.
        """
        if len(args) == 1:
            if len(args[0]) == 2:
                key, value = args[0]
            else:
                raise IndexError(
                    "If a sequence is provided to the second positional "
                    f"argument of pvl.OrderedMultiDict.insert() it must have "
                    f"exactly 2 elements, but it is {args[0]}"
                )
        elif len(args) == 2:
            self.__items.insert(index, args)
            key, value = args
        else:
            raise TypeError(
                f"{self.__name__}.insert() takes 2 or 3 positional arguments, "
                f"but {len(args)} were given."
            )

        self.__items.insert(index, (key, value))

        # Make sure indexing works with the new item
        if key in self:
            value_list = [val for k, val in self.__items if
                          k == key]
            dict_setitem(self, key, value_list)
        else:
            dict_setitem(self, key, [value])

        return

    def __insert_wrapper(func):
        """Make sure the arguments given to the insert methods are correct."""

        def check_func(self, key, new_item, instance=0):
            if key not in self.keys():
                raise KeyError(f"{key} not a key in label")
            if not isinstance(new_item, (list, OrderedMultiDict)):
                raise TypeError("The new item must be a list or PVLModule")
            if isinstance(new_item, OrderedMultiDict):
                new_item = list(new_item)
            return func(self, key, new_item, instance)
        return check_func

    def _get_index_for_insert(self, key, instance: int) -> int:
        """Get the index of the key to insert before or after."""
        if instance == 0:
            # Index method will return the first occurrence of the key
            index = self.keys().index(key)
        else:
            occurrence = -1
            for index, k in enumerate(self.keys()):
                if k == key:
                    occurrence += 1
                    if occurrence == instance:
                        # Found the key and the correct occurrence of the key
                        break

            if occurrence != instance:
                # Gone through the entire list of keys and the instance number
                # given is too high for the number of occurrences of the key
                raise ValueError(f"Cannot insert before/after the {instance} "
                                 f"instance of the key '{key}' since there are "
                                 f"only {occurrence} occurrences of the key")
        return index

    def _insert_item(
            self, key, new_item: abc.Iterable, instance: int, is_after: bool
    ):
        """Insert a new item before or after another item."""
        index = self._get_index_for_insert(key, instance)
        index = index + 1 if is_after else index

        # But new_item is always a list of two-tuples, even if only one, and
        # all should be inserted, so despite the singular "an item"
        # in the doc strings, this could be a whole bunch.
        for pair in new_item:
            self.insert(index, pair)
            index += 1

    @__insert_wrapper
    def insert_after(self, key, new_item: abc.Iterable, instance=0):
        """Insert an item after a key"""
        self._insert_item(key, new_item, instance, True)

    @__insert_wrapper
    def insert_before(self, key, new_item: abc.Iterable, instance=0):
        """Insert an item before a key"""
        self._insert_item(key, new_item, instance, False)


def _insert_check(func):
    """This Decorator makes sure the arguments given to the insert methods
    are correct.
    """

    def check_func(self, key, new_item, instance=0):
        if key not in self.keys():
            raise KeyError(f"'{key}' not not found.")
        if not isinstance(new_item, Sized):
            raise TypeError("The new item must be Sized.")
        return func(self, key, new_item, instance)
    return check_func


class PVLMultiDict(MultiDict):
    """Core data structure returned from the pvl loaders.

    For now, this is just going to document the changes in going
    from the old custom pvl.OrderedMultiDict to the multidict.MultiDict
    object. Also evaluated the boltons.OrderedMultiDict, but its
    semantics were too different #52

    Will alias pvl.OrderedMultiDict as PVLModule and
        alias multiduct.MultiDict as MultiDict

    Differences:
    - PVLModule.getlist() is now MultiDict.getall() - could put in an alias
    - PVLModule.getlist('k') where k is not in the structure returns
        an empty list, MultiDict.getall() properly returns a KeyError.
    - PVLModule.append() is now MultiDict.add(), made an alias.
    - The .items(), .keys(), and .values() are now proper iterators
        and don't return sequences like PVLModule did.
    - The PVLModule.insert_before() and PVLModule.insert_after() functionality
        had an edge case where if you had a k, v pair, you had to
        pass it to those functions as a sequence that contained a
        single element that had two elements in it, now you can
        also just pass a two-tuple or whatever, and as long as the
        first thing is a string, it'll get inserted.

    Potential changes:
    - Calling list() on a PVLModule returns a list of tuples, which
        is like calling list() on the results of a dict.items() iterator.
        Calling list() on a MultiDict would return just a list of keys,
        which is semantically identical to calling list() on a dict.
        test_set(), test_conversion()
    - PVLModule.pop(k) removed all keys that matched k, MultiDict.pop(k) now
        just removes the first occurrence.  MultiDict.popall(k) would pop
        and return all.
        test_pop()
    - PVLModule.popitem() used to remove the last item from the underlying list,
        MultiDict.popitem() removes an arbitrary key, value pair.
        test_popitem
    - MultiDict.__repr__() returns something different, need to evaluate.
        test_repr
    - equality is different.  PVLModule has an isinstance()
        check in the __eq__() operator, which I don't think was right,
        since equality is about values, not about type.  MultiDict
        has a value-based notion of equality.  So an empty PVLGroup and an
        empty PVLObject could test equal, but would fail an isinstance() check.
        test_equality
    """

    def __getitem__(self, key):
        # Allow list-like access of the underlying structure
        if isinstance(key, int):
            i, k, v = self._impl._items[key]
            return k, v
        elif isinstance(key, slice):
            return list(map((lambda t: (t[1], t[2])), self._impl._items[key]))
        return super().__getitem__(key)

    def _get_index(self, key, ith: int) -> int:
        """Returns the index of the item in the underlying list implementation
        that is the *ith* value of that *key*.

        Effectively creates a list of all indexes that match *key*, and then
        returns the index of the *ith* element of that list.  The *ith*
        integer can be any positive or negative integer and follows the
        rules for list indexes.
        """
        identity = self._title(key)
        idxs = list()
        for idx, (i, k, v) in enumerate(self._impl._items):
            if i == identity:
                idxs.append(idx)

        try:
            return idxs[ith]
        except IndexError:
            raise IndexError(
                f"There are only {len(idxs)} elements with the key {key}, "
                f"the provided index ({ith}) is out of bounds."
            )

    def _insert_item(self, key, new_item, instance: int, is_after: bool):
        """Insert a new item before or after another item."""
        index = self._get_index(key, instance)
        index = index + 1 if is_after else index
        if len(new_item) == 2 and isinstance(new_item[0], str):
            identity = self._title(new_item[0])
            self._impl._items.insert(index,
                                     (identity, self._key(new_item[0]), new_item[1]))
            self._impl.incr_version()
        else:
            triplets = list()
            if isinstance(new_item, Mapping):
                for k, v in new_item.items():
                    identity = self._title(k)
                    triplets.append((identity, self._key(k), v))
            else:
                # Maybe a sequence containing pairs?
                for pair in new_item:
                    if len(pair) != 2:
                        raise ValueError(
                            "Items to insert must be key, value pairs, and "
                            f"{pair} is not."
                        )
                    identity = self._title(pair[0])
                    triplets.append((identity, self._key(pair[0]), pair[1]))
            # Now insert the list
            self._impl._items = self._impl._items[:index] + triplets + self._impl._items[index:]
            self._impl.incr_version()
        return

    @_insert_check
    def insert_after(self, key, new_item, instance=0):
        """Insert an item after a key"""
        self._insert_item(key, new_item, instance, True)

    @_insert_check
    def insert_before(self, key, new_item, instance=0):
        """Insert an item before a key"""
        self._insert_item(key, new_item, instance, False)

    def append(self, key, value):
        self.add(key, value)

    def discard(self, key):
        # This should probably be deprecated, it is just
        # version of del that swallows the exception
        try:
            del self[key]
        except KeyError:
            pass


# class PVLModule(PVLMultiDict):
class PVLModule(OrderedMultiDict):

        pass
    # def __init__(self, *args, **kwargs):
    #     super(PVLModule, self).__init__(*args, **kwargs)
    #     self.errors = []

    # @property
    # def valid(self):
    #     return not self.errors


class PVLAggregation(OrderedMultiDict):
    pass


class PVLGroup(PVLAggregation):
    pass


class PVLObject(PVLAggregation):
    pass


class Quantity(namedtuple('Quantity', ['value', 'units'])):
    """A simple collections.namedtuple object to contain
    a value and units parameter.

    If you need more comprehensive units handling, you
    may want to use the astropy.units.Quantity object,
    the pint.Quantity object, or some other 3rd party
    object.  Please see the documentation on :doc:`quantities`
    for how to use 3rd party Quantity objects with pvl.
    """
    pass


class Units(Quantity):
    warnings.warn(
        "The pvl.collections.Units object is deprecated, and may be removed at "
        "the next major patch. Please use pvl.collections.Quantity instead.",
        PendingDeprecationWarning
    )
