# -*- coding: utf-8 -*-
import sys
import pprint
import six
from collections import Mapping, MutableMapping, namedtuple


PY3 = sys.version_info[0] == 3
INDEX_TYPES = six.integer_types + (slice,)

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
        return '%s(%r)' % (type(self).__name__, self._mapping)


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
        return '%s(%r)' % (type(self).__name__, keys)

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
        return '%s(%r)' % (type(self).__name__, values)

    def index(self, value):
        values = [val for _, val in self._mapping]
        return values.index(value)


class OrderedMultiDict(dict, MutableMapping):
    """A ``dict`` like container.

    This container preserves the original ordering as well as allows multiple
    values for the same key. It provides a similar similar semantics to a
    ``list`` of ``tuples`` but with ``dict`` style access.

    Using ``__setitem__`` syntax overwrites all fields with the same key and
    ``__getitem__`` will return the first value with the key.
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
        if isinstance(key, INDEX_TYPES):
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

        items1 = six.iteritems(self)
        items2 = six.iteritems(other)

        for ((key1, value1), (key2, value2)) in six.moves.zip(items1, items2):
            if key1 != key2:
                return False

            if value1 != value2:
                return False

        return True

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        if not self.__items:
            return '%s([])' % type(self).__name__

        lines = []
        for item in self.__items:
            for line in pprint.pformat(item).splitlines():
                lines.append('  ' + line)

        return "%s([\n%s\n])" % (type(self).__name__, '\n'.join(lines))

    get = MutableMapping.get
    update = MutableMapping.update
    pop = MutableMapping.pop

    if PY3:  # noqa
        def keys(self):
            return KeysView(self)

        def values(self):
            return ValuesView(self)

        def items(self):
            return ItemsView(self)

    else:
        def keys(self):
            return [key for key, _ in self.__items]

        def iterkeys(self):
            return KeysView(self)

        def values(self):
            return [value for _, value in self.__items]

        def itervalues(self):
            return ValuesView(self)

        def items(self):
            return list(self.__items)

        def iteritems(self):
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
        """Adds a (name, value) pair, doesn't overwrite the value if it already
        exists."""
        self.__items.append((key, value))

        try:
            dict_getitem(self, key).append(value)
        except KeyError:
            dict_setitem(self, key, [value])

    def extend(self, *args, **kwargs):
        """Add key value pairs for an iterable."""
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))

        iterable = args[0] if args else None
        if iterable:
            if isinstance(iterable, Mapping) or hasattr(iterable, 'items'):
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

    def getlist(self, key):
        """Returns a list of all the values for the named field. Returns an
        empty list if the key doesn't exist."""
        try:
            return list(dict_getitem(self, key))
        except KeyError:
            return []

    def popitem(self):
        if not self:
            raise KeyError('popitem(): %s is empty' % type(self).__name__)

        key, _ = item = self.__items.pop()
        values = dict_getitem(self, key)
        values.pop()

        if not values:
            dict_delitem(self, key)

        return item

    def copy(self):
        return type(self)(self)

    def __insert_wrapper(func):
        """Make sure the arguments given to the insert methods are correct"""
        def check_func(self, key, new_item, instance=0):
            if key not in self.keys():
                raise KeyError("%s not a key in label" % (key))
            if not isinstance(new_item, (list, OrderedMultiDict)):
                raise TypeError("The new item must be a list or PVLModule")
            if isinstance(new_item, OrderedMultiDict):
                new_item = list(new_item)
            return func(self, key, new_item, instance)
        return check_func

    def _get_index_for_insert(self, key, instance):
        """Get the index of the key to insert before or after"""
        if instance == 0:
            # Index method will return the first occurence of the key
            index = self.keys().index(key)
        else:
            occurrence = -1
            for index, k in enumerate(self.keys()):
                if k == key:
                    occurrence += 1
                    if occurrence == instance:
                        # Found the key and the correct occurence of the key
                        break

            if occurrence != instance:
                # Gone through the entire list of keys and the instance number
                # given is too high for the number of occurences of the key
                raise ValueError(
                    (
                        "Cannot insert before/after the %d "
                        "instance of the key '%s' since there are "
                        "only %d occurences of the key" % (
                            instance, key, occurrence)
                    ))
        return index

    def _insert_item(self, key, new_item, instance, is_after):
        """Insert a new item before or after another item"""
        index = self._get_index_for_insert(key, instance)
        index = index + 1 if is_after else index
        self.__items = self.__items[:index] + new_item + self.__items[index:]
        # Make sure indexing works with new items
        for new_key, new_value in new_item:
            if new_key in self:
                value_list = [val for k, val in self.__items if k == new_key]
                dict_setitem(self, new_key, value_list)
            else:
                dict_setitem(self, new_key, [new_value])

    @__insert_wrapper
    def insert_after(self, key, new_item, instance=0):
        """Insert an item after a key"""
        self._insert_item(key, new_item, instance, True)

    @__insert_wrapper
    def insert_before(self, key, new_item, instance=0):
        """Insert an item before a key"""
        self._insert_item(key, new_item, instance, False)


class PVLModule(OrderedMultiDict):

    def __init__(self, *args, **kwargs):
        super(PVLModule, self).__init__(*args, **kwargs)
        self.errors = []

    @property
    def valid(self):
        return not self.errors


class PVLGroup(OrderedMultiDict):
    pass


class PVLObject(OrderedMultiDict):
    pass


class Units(namedtuple('Units', ['value', 'units'])):
    pass
