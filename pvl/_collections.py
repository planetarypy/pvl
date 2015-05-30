# -*- coding: utf-8 -*-
import sys
import pprint
from collections import Mapping, MutableMapping, namedtuple


PY3 = sys.version_info[0] == 3

dict_setitem = dict.__setitem__
dict_getitem = dict.__getitem__
dict_delitem = dict.__delitem__
dict_contains = dict.__contains__


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
        return dict_getitem(self, key)[0][1]

    def __delitem__(self, key):
        dict_delitem(self, key)
        self.__items = [item for item in self.__items if item[0] != key]

    values = MutableMapping.values
    get = MutableMapping.get
    update = MutableMapping.update
    pop = MutableMapping.pop
    popitem = MutableMapping.popitem
    clear = MutableMapping.clear

    if not PY3:  # Python 2
        iterkeys = MutableMapping.iterkeys
        itervalues = MutableMapping.itervalues

    def discard(self, key):
        try:
            del self[key]
        except KeyError:
            pass

    def append(self, key, value):
        """Adds a (name, value) pair, doesn't overwrite the value if it already
        exists."""
        item = (key, value)
        self.__items.append(item)

        try:
            dict_getitem(self, key).append(item)
        except KeyError:
            dict_setitem(self, key, [item])

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
            return [item[1] for item in dict_getitem(self, key)]
        except KeyError:
            return []

    def __repr__(self):
        if not self.__items:
            return '%s([])' % type(self).__name__

        lines = []
        for item in self.__items:
            for line in pprint.pformat(item).splitlines():
                lines.append('  ' + line)

        return "%s([\n%s\n])" % (type(self).__name__, '\n'.join(lines))

    def copy(self):
        return type(self)(self)

    if PY3:
        def items(self):
            return iter(self.__items)

    else:
        def items(self):
            return list(self.__items)

        def iteritems(self):
            return iter(self.__items)


class Label(OrderedMultiDict):
    pass


class LabelGroup(OrderedMultiDict):
    pass


class LabelObject(OrderedMultiDict):
    pass


class Units(namedtuple('Units', ['value', 'units'])):
    pass
