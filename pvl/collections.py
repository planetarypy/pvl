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
and Mutable Sequence ABCs. We also provide two implementations, the
OrderedMultiDict, and the newer PVLMultiDict.

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


class MutableMappingSequence(abc.MutableMapping, abc.MutableSequence):
    """ABC for a mutable object that has both mapping and
    sequence characteristics.

    Must implement `.getall(k)` and `.popall(k)` since a MutableMappingSequence
    can have many values for a single key, while `.get(k)` and
    `.pop(k)` return and operate on a single value, the *all*
    versions return and operate on all values in the MutableMappingSequence
    with the key `k`.

    Furthermore, `.pop()` without an argument should function as the
    MutableSequence pop() function and pop the last value when considering
    the MutableMappingSequence in a list-like manner.
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
        return "{!s}({!r})".format(type(self).__name__, self._mapping)


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
        return "{!s}({!r})".format(type(self).__name__, keys)

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
        return "{!s}({!r})".format(type(self).__name__, values)

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
            return "{!s}([])".format(type(self).__name__)

        lines = []
        for item in self.__items:
            for line in pprint.pformat(item).splitlines():
                lines.append("  " + line)

        return "{!s}([\n{!s}\n])".format(type(self).__name__, "\n".join(lines))

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

        warnings.warn(
            "The discard(k) function is deprecated in favor of .popall(k), "
            "please begin using it, as .discard(k) may be removed in the "
            "next major patch.",
            PendingDeprecationWarning,
        )

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
            raise TypeError(f"expected at most 1 arguments, got {len(args)}")

        iterable = args[0] if args else None
        if iterable:
            if isinstance(iterable, abc.Mapping) or hasattr(iterable, "items"):
                for key, value in iterable.items():
                    self.append(key, value)
            elif hasattr(iterable, "keys"):
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
            "The getlist() function is deprecated in favor of .getall(), "
            "please begin using it, as .getlist() may be removed in the "
            "next major patch.",
            PendingDeprecationWarning,
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
            "The pop(k) function removes "
            "all keys with value k to remain backwards compatible with the "
            "pvl 0.x architecture, this concept of "
            "operations for .pop(k) may change in future versions. "
            "Consider using .popall(k) instead.",
            FutureWarning,
        )

        if len(args) == 0 and len(kwargs) == 0:
            return self.popitem()

        return self.popall(*args, *kwargs)

    def popitem(self):

        warnings.warn(
            "The popitem() function removes "
            "and returns the last key, value pair to remain backwards "
            "compatible with the pvl 0.x architecture, this concept of "
            "operations for .popitem() may change in future versions. "
            "Consider using the list-like .pop(), without an argument instead.",
            FutureWarning,
        )
        # Yes, I know .pop() without an argument just redirects here, but it
        # won't always.

        if not self:
            raise KeyError(
                "popitem(): {!s} ".format(type(self).__name__) + "is empty"
            )

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

        The first positional argument will always be taken as the
        *index* for insertion.

        If three arguments are given, the second will be taken
        as the *key*, and the third as the *value* to insert.

        If only two arguments are given, the second must be a sequence.

        If it is a sequence of pairs (such that every item in the sequence is
        itself a sequence of length two), that sequence will be inserted
        as key, value pairs.

        If it happens to be a sequence of two items (the first of which is
        not a sequence), the first will be taken as the *key* and the
        second the *value* to insert.
        """

        if not isinstance(index, int):
            raise TypeError(
                "The first positional argument to pvl.MultiDict.insert()"
                "must be an int."
            )

        kvlist = _insert_arg_helper(args)

        for (key, value) in kvlist:
            self.__items.insert(index, (key, value))
            index += 1

            # Make sure indexing works with the new item
            if key in self:
                value_list = [val for k, val in self.__items if k == key]
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

    def key_index(self, key, instance: int = 0) -> int:
        """Get the index of the key to insert before or after."""
        if key not in self:
            raise KeyError(str(key))

        idxs = list()
        for idx, k in enumerate(self.keys()):
            if key == k:
                idxs.append(idx)

        try:
            return idxs[instance]
        except IndexError:
            raise IndexError(
                f"There are only {len(idxs)} elements with the key {key}, "
                f"the provided index ({instance}) is out of bounds."
            )

    def insert_after(self, key, new_item: abc.Iterable, instance=0):
        """Insert an item after a key"""
        index = self.key_index(key, instance)
        self.insert(index + 1, new_item)

    def insert_before(self, key, new_item: abc.Iterable, instance=0):
        """Insert an item before a key"""
        index = self.key_index(key, instance)
        self.insert(index, new_item)


def _insert_arg_helper(args):
    # Helper function to un-mangle the many and various ways that
    # key, value pairs could be provided to the .insert() functions.
    # Takes all of them, and returns a list of key, value pairs, even
    # if there is only one.
    if len(args) == 1:
        if not isinstance(args, (abc.Sequence, abc.Mapping)):
            raise TypeError(
                "If a single argument is provided to the second positional "
                "argument of insert(), it must have a Sequence or Mapping "
                f"interface. Instead it was {type(args)}: {args}"
            )

        if isinstance(args[0], abc.Mapping):
            return list(args[0].items())

        else:
            if len(args[0]) == 2 and (
                isinstance(args[0][0], str)
                or not isinstance(args[0][0], abc.Sequence)
            ):
                kvlist = (args[0],)
            else:
                for pair in args[0]:
                    msg = (
                        "One of the elements in the sequence passed to the "
                        "second argument of insert() "
                    )
                    if not isinstance(pair, abc.Sequence):
                        raise TypeError(
                            msg + f"was not itself a sequence, it is: {pair}"
                        )
                    if not len(pair) == 2:
                        raise TypeError(
                            msg + f"was not a pair of values, it is: {pair}"
                        )

                kvlist = args[0]

    elif len(args) == 2:
        kvlist = (args,)
    else:
        raise TypeError(
            f"insert() takes 2 or 3 positional arguments ({len(args)} given)."
        )

    return kvlist


try:  # noqa: C901
    # In order to access super class attributes for our derived class, we must
    # import the native Python version, instead of the default Cython version.
    from multidict._multidict_py import MultiDict

    class PVLMultiDict(MultiDict, MutableMappingSequence):
        """This is a new class that may be implemented as the default
        structure to be returned from the pvl loaders in the future (replacing
        OrderedMultiDict).

        Here is a summary of the differences:

        * OrderedMultiDict.getall('k') where k is not in the structure returns
          an empty list, PVLMultiDict.getall('k') properly returns a KeyError.
        * The .items(), .keys(), and .values() are proper iterators
          and don't return sequences like OrderedMultiDict did.
        * Calling list() on an OrderedMultiDict returns a list of tuples, which
          is like calling list() on the results of a dict.items() iterator.
          Calling list() on a PVLMultiDict returns just a list of keys,
          which is semantically identical to calling list() on a dict.
        * OrderedMultiDict.pop(k) removed all keys that matched k,
          PVLMultiDict.pop(k) just removes the first occurrence.
          PVLMultiDict.popall(k) would pop all.
        * OrderedMultiDict.popitem() removes the last item from the underlying
          list, PVLMultiDict.popitem() removes an arbitrary key, value pair,
          semantically identical to .popitem() on a dict.
        * OrderedMultiDict.__repr__() and .__str__() return identical strings,
          PVLMultiDict provides a .__str__() that is pretty-printed similar
          to OrderedMultiDict, but also a .__repr__() with a more compact
          representation.
        * Equality is different:  OrderedMultiDict has an isinstance()
          check in the __eq__() operator, which I don't think was right,
          since equality is about values, not about type.  PVLMultiDict
          has a value-based notion of equality.  So an empty PVLGroup and an
          empty PVLObject derived from PVLMultiDict could test equal,
          but would fail an isinstance() check.
        """

        # Also evaluated the boltons.OrderedMultiDict, but its semantics were
        # too different #52

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def __getitem__(self, key):
            # Allow list-like access of the underlying structure
            if isinstance(key, (int, slice)):
                return list(self.items())[key]
            return super().__getitem__(key)

        def __repr__(self):
            if len(self) == 0:
                return f"{self.__class__.__name__}()"

            return (
                f"{self.__class__.__name__}(" + str(list(self.items())) + ")"
            )

        def __str__(self):
            if len(self) == 0:
                return self.__repr__()

            lines = []
            for item in self.items():
                for line in pprint.pformat(item).splitlines():
                    lines.append("  " + line)

            return f"{self.__class__.__name__}([\n" + "\n".join(lines) + "\n])"

        def key_index(self, key, ith: int = 0) -> int:
            """Returns the index of the item in the underlying list
            implementation that is the *ith* value of that *key*.

            Effectively creates a list of all indexes that match *key*, and then
            returns the original index of the *ith* element of that list.  The
            *ith* integer can be any positive or negative integer and follows
            the rules for list indexes.
            """
            if key not in self:
                raise KeyError(str(key))
            idxs = list()
            for idx, (k, v) in enumerate(self.items()):
                if key == k:
                    idxs.append(idx)

            try:
                return idxs[ith]
            except IndexError:
                raise IndexError(
                    f"There are only {len(idxs)} elements with the key {key}, "
                    f"the provided index ({ith}) is out of bounds."
                )

        def _insert_item(
            self, key, new_item: abc.Iterable, instance: int, is_after: bool
        ):
            """Insert a new item before or after another item."""
            index = self.key_index(key, instance)
            index = index + 1 if is_after else index

            if isinstance(new_item, abc.Mapping):
                tuple_iter = new_item.items()
            else:
                tuple_iter = new_item
            self.insert(index, tuple_iter)

        def insert(self, index: int, *args) -> None:
            """Inserts at the index given by *index*.

            The first positional argument will always be taken as the
            *index* for insertion.

            If three arguments are given, the second will be taken
            as the *key*, and the third as the *value* to insert.

            If only two arguments are given, the second must be a sequence.

            If it is a sequence of pairs (such that every item in the sequence
            is itself a sequence of length two), that sequence will be inserted
            as key, value pairs.

            If it happens to be a sequence of two items (the first of which is
            not a sequence), the first will be taken as the *key* and the
            second the *value* to insert.
            """
            if not isinstance(index, int):
                raise TypeError(
                    "The first positional argument to pvl.MultiDict.insert()"
                    "must be an int."
                )

            kvlist = _insert_arg_helper(args)

            for (key, value) in kvlist:
                identity = self._title(key)
                self._impl._items.insert(
                    index, (identity, self._key(key), value)
                )
                self._impl.incr_version()
                index += 1
            return

        def insert_after(self, key, new_item, instance=0):
            """Insert an item after a key"""
            self._insert_item(key, new_item, instance, True)

        def insert_before(self, key, new_item, instance=0):
            """Insert an item before a key"""
            self._insert_item(key, new_item, instance, False)

        def pop(self, *args, **kwargs):
            """Returns a two-tuple or a single value, depending on how it is
            called.

            If no arguments are given, it removes and returns the last key,
            value pair (list-like behavior).

            If a *key* is given, the first instance of key is found and its
            value is removed and returned.  If *default* is not given and
            *key* is not in the dictionary, a KeyError is raised, otherwise
            *default* is returned (dict-like behavior).
            """
            if len(args) == 0 and len(kwargs) == 0:
                i, k, v = self._impl._items.pop()
                self._impl.incr_version()
                return i, v
            else:
                return super().pop(*args, **kwargs)

        def append(self, key, value):
            # Not sure why super() decided to go with the set-like add() instead
            # of the more appropriate list-like append().  Fixed it for them.
            self.add(key, value)

    # New versions based on PVLMultiDict
    class PVLModuleNew(PVLMultiDict):
        pass

    class PVLAggregationNew(PVLMultiDict):
        pass

    class PVLGroupNew(PVLAggregationNew):
        pass

    class PVLObjectNew(PVLAggregationNew):
        pass


except ImportError:
    warnings.warn(
        "The multidict library is not present, so the new PVLMultiDict "
        "cannot be used. At this time, it is completely optional, and doesn't "
        "impact the use of pvl.",
        ImportWarning,
    )


class PVLModule(OrderedMultiDict):
    pass


class PVLAggregation(OrderedMultiDict):
    pass


class PVLGroup(PVLAggregation):
    pass


class PVLObject(PVLAggregation):
    pass


class Quantity(namedtuple("Quantity", ["value", "units"])):
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
        PendingDeprecationWarning,
    )
