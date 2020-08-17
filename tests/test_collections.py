# -*- coding: utf-8 -*-
"""This module has tests for the pvl collections module."""

# Copyright 2015, 2017, 2019-2020, ``pvl`` library authors.
#
# Reuse is permitted under the terms of the license.
# The AUTHORS file and the LICENSE file are at the
# top level of this library.

from collections import abc
import pytest
import unittest

import pvl
from pvl.collections import OrderedMultiDict, PVLMultiDict

class DictLike(abc.Mapping):

    def __init__(self):
        self.list = ['a', 'b', 'a']

    def __getitem__(self, key):
        return 42

    def __iter__(self):
        return iter(self.list)

    def __len__(self):
        return len(self.list)


class TestMultiDicts(unittest.TestCase):

    def setUp(self):
        self.classes = (OrderedMultiDict, PVLMultiDict)

    def test_empty(self):
        for cls in self.classes:
            module = cls()
            with self.subTest(type=type(module)):
                self.assertEqual(len(module), 0)
                self.assertEqual(module.get('c', 42), 42)
                self.assertRaises(KeyError, module.__getitem__, 'c')

    def test_list_creation(self):
        class DictLike(abc.Mapping):

            def __init__(self):
                self.list = ['a', 'b', 'a']

            def __getitem__(self, key):
                return 42

            def __iter__(self):
                return iter(self.list)

            def __len__(self):
                return len(self.list)

        for cls in self.classes:
            module = cls([('a', 1), ('b', 2), ('a', 3)])
            with self.subTest(type=type(module)):
                self.assertEqual(len(module), 3)
                self.assertEqual(module.__getitem__('a'), 1)
                self.assertEqual(module.__getitem__('b'), 2)
                self.assertListEqual(module.getall('a'), [1, 3])
                self.assertRaises(KeyError, module.__getitem__, 'c')
                self.assertEqual(module.get('c', 42), 42)

                self.assertRaises(TypeError, cls, [], [])

                fromdict = cls(DictLike())
                self.assertEqual(len(fromdict), 3)
                self.assertEqual(fromdict.__getitem__('a'), 42)
                self.assertEqual(fromdict.__getitem__('b'), 42)
                self.assertListEqual(fromdict.getall('a'), [42, 42])
                self.assertRaises(KeyError, fromdict.__getitem__, 'c')

    def test_dict_creation(self):
        for cls in self.classes:
            module = cls({'a': 1, 'b': 2})
            with self.subTest(type=type(module)):
                self.assertEqual(len(module), 2)
                self.assertEqual(module.__getitem__('a'), 1)
                self.assertEqual(module.__getitem__('b'), 2)
                self.assertRaises(KeyError, module.__getitem__, 'c')
                self.assertEqual(module.get('c', 42), 42)

    def test_keyword_creation(self):
        for cls in self.classes:
            module = cls(a=1, b=2)
            with self.subTest(type=type(module)):
                self.assertEqual(len(module), 2)
                self.assertEqual(module.__getitem__('a'), 1)
                self.assertEqual(module.__getitem__('b'), 2)
                self.assertRaises(KeyError, module.__getitem__, 'c')
                self.assertEqual(module.get('c', 42), 42)

    def test_key_access(self):
        for cls in self.classes:
            module = cls([('a', 1), ('b', 2), ('a', 3)])
            with self.subTest(type=type(module)):
                self.assertEqual(module.__getitem__('a'), 1)
                self.assertEqual(module.__getitem__('b'), 2)
                self.assertRaises(KeyError, module.__getitem__, 'c')

    def test_index_access(self):
        for cls in self.classes:
            module = cls([('a', 1), ('b', 2), ('a', 3)])
            with self.subTest(type=type(module)):
                self.assertEqual(module.__getitem__(0), ('a', 1))
                self.assertEqual(module.__getitem__(1), ('b', 2))
                self.assertEqual(module.__getitem__(2), ('a', 3))
                self.assertRaises(IndexError, module.__getitem__, 3)

    def test_slice_access(self):
        for cls in self.classes:
            module = cls([('a', 1), ('b', 2), ('a', 3)])
            with self.subTest(type=type(module)):
                self.assertListEqual(
                    module.__getitem__(slice(0, 3)),
                    [('a', 1), ('b', 2), ('a', 3)]
                )
                self.assertListEqual(
                    module.__getitem__(slice(1, None)),
                    [('b', 2), ('a', 3)]
                )
                self.assertListEqual(
                    module.__getitem__(slice(None, -1)),
                    [('a', 1), ('b', 2)]
                )

    def test_set(self):
        for cls in self.classes:
            module = cls()
            with self.subTest(type=type(module)):
                module['a'] = 1
                module['b'] = 2
                module['a'] = 3

                self.assertEqual(module['a'], 3)
                self.assertEqual(module['b'], 2)
                self.assertListEqual(module.getall('a'), [3])
                self.assertEqual(len(module), 2)

                self.assertRaises(KeyError, module.__getitem__, 'c')

                self.assertEqual(module.get('c', 42), 42)

    def test_delete(self):
        for cls in self.classes:
            module = cls([('a', 1), ('b', 2), ('a', 3)])
            with self.subTest(type=type(module)):
                del module['a']
                self.assertEqual(len(module), 1)
                self.assertRaises(KeyError, module.__getitem__, 'a')
                self.assertRaises(KeyError, module.__getitem__, 'c')

    def test_clear(self):
        for cls in self.classes:
            module = cls([('a', 1), ('b', 2), ('a', 3)])
            with self.subTest(type=type(module)):
                module.clear()
                self.assertEqual(len(module), 0)
                self.assertRaises(KeyError, module.__getitem__, 'a')
                self.assertRaises(KeyError, module.__getitem__, 'b')
                self.assertRaises(KeyError, module.getall, 'a')

                module['a'] = 42
                self.assertEqual(len(module), 1)
                self.assertEqual(module.__getitem__('a'), 42)

    def test_pop_noarg(self):
        for cls in self.classes:
            module = cls([('a', 1), ('b', 2), ('a', 3)])
            with self.subTest(type=type(module)):
                self.assertTupleEqual(module.pop(), ('a', 3))
                self.assertEqual(len(module), 2)

    def test_update(self):
        for cls in self.classes:
            module = cls([('a', 1), ('b', 2), ('a', 3)])
            with self.subTest(type=type(module)):
                module.update({'a': 42, 'c': 7})
                self.assertEqual(len(module), 3)
                self.assertEqual(module.__getitem__('a'), 42)
                self.assertEqual(module.__getitem__('b'), 2)
                self.assertEqual(module.__getitem__('c'), 7)

                module.update()
                self.assertEqual(len(module), 3)
                self.assertEqual(module.__getitem__('a'), 42)
                self.assertEqual(module.__getitem__('b'), 2)
                self.assertEqual(module.__getitem__('c'), 7)

    def test_append(self):
        for cls in self.classes:
            module = cls([('a', 1), ('b', 2), ('a', 3)])
            with self.subTest(type=type(module)):
                module.append('a', 42)
                self.assertEqual(len(module), 4)
                self.assertEqual(module.__getitem__('a'), 1)
                self.assertListEqual(module.getall('a'), [1, 3, 42])

                module.append('c', 43)
                self.assertEqual(len(module), 5)
                self.assertEqual(module.__getitem__('c'), 43)
                self.assertListEqual(module.getall('c'), [43])

    def test_len(self):
        for cls in self.classes:
            module = cls()
            with self.subTest(type=type(module)):
                self.assertEqual(len(module), 0)

                module = cls([('a', 1), ('b', 2), ('a', 3)])
                self.assertEqual(len(module), 3)

    def test_iterators(self):
        for cls in self.classes:
            module = cls()
            with self.subTest(type=type(module)):
                self.assertListEqual(list(module.items()), [])
                self.assertEqual(len(module.items()), 0)
                self.assertNotIn(('a', 1), module.items())

                self.assertListEqual(list(module.keys()), [])
                self.assertEqual(len(module.keys()), 0)
                self.assertNotIn(('a'), module.keys())

                self.assertListEqual(list(module.values()), [])
                self.assertEqual(len(module.values()), 0)
                self.assertNotIn(('1'), module.values())

                the_list = [('a', 1), ('b', 2), ('a', 3)]
                module = cls(the_list)

                self.assertListEqual(list(module.items()), the_list)
                self.assertEqual(len(module.items()), 3)
                self.assertIn(('a', 1), module.items())
                self.assertIn(('b', 2), module.items())
                self.assertIn(('a', 3), module.items())
                self.assertNotIn(('c', 4), module.items())

                self.assertListEqual(list(module.keys()), ['a', 'b', 'a'])
                self.assertEqual(len(module.keys()), 3)
                self.assertIn('a', module.keys())
                self.assertIn('b', module.keys())
                self.assertNotIn('c', module.keys())

                self.assertListEqual(list(module.values()), [1, 2, 3])
                self.assertEqual(len(module.values()), 3)
                self.assertIn(1, module.values())
                self.assertIn(2, module.values())
                self.assertIn(3, module.values())
                self.assertNotIn(4, module.values())

    def test_copy(self):
        for cls in self.classes:
            module = cls()
            with self.subTest(type=type(module)):
                copy = module.copy()
                self.assertEqual(module, copy)
                self.assertIsNot(module, copy)

                module['c'] = 42
                self.assertNotEqual(module, copy)

                module = cls([('a', 1), ('b', 2), ('a', 3)])
                copy = module.copy()
                self.assertEqual(module, copy)
                self.assertIsNot(module, copy)

                module['c'] = 42
                self.assertNotEqual(module, copy)

    def test_equality(self):
        for modcls, grpcls, objcls in (
            (
                pvl.collections.PVLModule,
                pvl.collections.PVLGroup,
                pvl.collections.PVLObject
            ),
            (
                pvl.collections.PVLModuleNew,
                pvl.collections.PVLGroupNew,
                pvl.collections.PVLObjectNew
            )
        ):
            module = modcls()
            group = grpcls()
            obj = objcls()
            with self.subTest(type=type(module)):
                self.assertFalse(module)
                self.assertFalse(group)
                self.assertFalse(obj)

                self.assertTrue(modcls(a=1))
                self.assertTrue(grpcls(a=1))
                self.assertTrue(objcls(a=1))

                self.assertNotEqual(modcls(), modcls(a=1))
                self.assertEqual(modcls(a=1), modcls(a=1))
                self.assertEqual(modcls(a=1), modcls([('a', 1)]))
                self.assertEqual(modcls(a=1), modcls({'a': 1}))
                self.assertNotEqual(modcls(a=1), modcls(b=1))
                self.assertNotEqual(modcls(a=1), modcls(a=2))

                self.assertNotIsInstance(group, modcls)
                self.assertNotIsInstance(group, objcls)

    def test_insert(self):
        the_list = [('a', 1), ('b', 2), ('a', 3)]
        for cls in self.classes:
            module = cls()
            with self.subTest(type=type(module)):
                self.assertRaises(TypeError, module.insert, 'a')
                self.assertRaises(TypeError, module.insert, 0)
                module.insert(25, 'key', 'value')
                self.assertEqual(module, cls(key="value"))

                new_list = [('c', 4)] + the_list
                module = cls(the_list)
                module.insert(0, 'c', 4)
                self.assertEqual(module, cls(new_list))

                module = cls(the_list)
                module.insert(0, ('c', 4))
                self.assertEqual(module, cls(new_list))

                module = cls(the_list)
                module.insert(0, {'c': 4})
                self.assertEqual(module, cls(new_list))

                module = cls(the_list)
                module.insert(0, [('c', 4)])
                self.assertEqual(module, cls(new_list))

                listinlist = list(the_list)
                listinlist.insert(1, ('c', 4))
                listinlist.insert(2, ('d', 5))
                module = cls(the_list)
                module.insert(1, [('c', 4), ('d', 5)])
                self.assertEqual(module, cls(listinlist))

    def test_key_index(self):
        for cls in self.classes:
            module = cls([('a', 1), ('b', 2), ('a', 3)])
            with self.subTest(type=type(module)):
                self.assertRaises(KeyError, module.key_index, 'error_key')
                self.assertRaises(IndexError, module.key_index, 'a', 2)
                self.assertEqual(module.key_index('a'), 0)
                self.assertEqual(module.key_index('a', 0), 0)
                self.assertEqual(module.key_index('b'), 1)
                self.assertEqual(module.key_index('a', 1), 2)

    def test_insert_before(self):
        the_list = [('a', 1), ('b', 2), ('a', 3), ('c', 5)]
        expected = (
            (
                [('a', 4), ('a', 1), ('b', 2), ('a', 3), ('c', 5),],
                'a', 0, [4, 1, 3], 4
            ),
            (
                [('a', 1), ('a', 4), ('b', 2), ('a', 3), ('c', 5),],
                'b', 0, [1, 4, 3], 1
            ),
            (
                [('a', 1), ('b', 2), ('a', 4), ('a', 3), ('c', 5),],
                'a', 1, [1, 4, 3], 1
            ),
            (
                [ ('a', 1), ('b', 2), ('a', 3), ('a', 4), ('c', 5),],
                'c', 0, [1, 3, 4], 1
            )
        )
        for cls in self.classes:
            module = cls(the_list)
            with self.subTest(type=type(module)):
                for (
                        expected_label,
                        key,
                        instance,
                        expected_list,
                        expected_value
                ) in expected:
                    module = cls(the_list)
                    with self.subTest(
                            module=module,
                            expected_label=expected_label,
                            key=key,
                            instance=instance,
                            expected_list=expected_list,
                            expected_value=expected_value
                    ):
                        exp_mod = cls(expected_label)
                        module.insert_before(key, [('a', 4)], instance)
                        self.assertEqual(exp_mod, module)
                        self.assertEqual(module['a'], expected_value)
                        self.assertListEqual(module.getall('a'), expected_list)

    def test_insert_after(self):
        the_list = [('a', 1), ('b', 2), ('a', 3), ('c', 5)]
        expected = (
            (
                [('a', 1), ('a', 4), ('b', 2), ('a', 3), ('c', 5),],
                'a', 0, [1, 4, 3], 1
            ),
            (
                [('a', 1), ('b', 2), ('a', 4), ('a', 3), ('c', 5),],
                'b', 0, [1, 4, 3], 1
            ),
            (
                [('a', 1), ('b', 2), ('a', 3), ('a', 4), ('c', 5),],
                'a', 1, [1, 3, 4], 1
            ),
            (
                [ ('a', 1), ('b', 2), ('a', 3), ('c', 5), ('a', 4),],
                'c', 0, [1, 3, 4], 1
            )
        )
        for cls in self.classes:
            module = cls(the_list)
            with self.subTest(type=type(module)):
                for (
                        expected_label,
                        key,
                        instance,
                        expected_list,
                        expected_value
                ) in expected:
                    module = cls(the_list)
                    with self.subTest(
                            expected_label=expected_label,
                            key=key,
                            instance=instance,
                            expected_list=expected_list,
                            expected_value=expected_value
                    ):
                        exp_mod = cls(expected_label)
                        module.insert_after(key, [('a', 4)], instance)
                        self.assertEqual(exp_mod, module)
                        self.assertEqual(module['a'], expected_value)
                        self.assertListEqual(module.getall('a'), expected_list)

    def test_insert_before_after_raises(self):
        for cls in self.classes:
            module = cls([('a', 1), ('b', 2), ('a', 3)])
            with self.subTest(type=type(module)):
                self.assertRaises(
                    KeyError, module.insert_before, 'error_key', [('fo', 'ba')]
                )
                self.assertRaises(
                    KeyError, module.insert_after, 'error_key', [('fo', 'ba')]
                )
                self.assertRaises(
                    TypeError, module.insert_before, 'a', [('fo', 'ba'), 2]
                )
                self.assertRaises(
                    TypeError, module.insert_after, 'a', [('fo', 'ba'), 2]
                )


class TestDifferences(unittest.TestCase):

    def test_as_list(self):
        the_list = [('a', 1), ('b', 2)]

        # Returns list of tuples:
        old = OrderedMultiDict(the_list)
        self.assertListEqual(list(old), [('a', 1), ('b', 2)])

        # Returns list of keys, which is semantically identical to calling
        # list() on a dict.
        new = PVLMultiDict(the_list)
        self.assertListEqual(list(new), ['a', 'b'])

    def test_discard(self):
        the_list = [('a', 1), ('b', 2), ('a', 3)]

        # Has a set-like .discard() function
        old = OrderedMultiDict(the_list)
        old.discard('a')
        self.assertEqual(len(old), 1)
        self.assertRaises(KeyError, old.getall, 'a')
        self.assertRaises(KeyError, old.__getitem__, 'a')

        self.assertEqual(old.__getitem__('b'), 2)
        old.discard('b')
        self.assertEqual(len(old), 0)
        self.assertRaises(KeyError, old.__getitem__, 'b')

        old.discard('c')
        self.assertEqual(len(old), 0)

        # Does not have a set-like .discard() function, because it isn't a set!
        new = PVLMultiDict(the_list)
        self.assertRaises(AttributeError, getattr, new, "discard")

    def test_pop(self):
        the_list = [('a', 1), ('b', 2), ('a', 3)]

        # Removes all keys that match, but returns only the first value, which
        # is weird
        old = OrderedMultiDict(the_list)
        self.assertEqual(old.pop('a'), 1)
        self.assertEqual(len(old), 1)
        self.assertRaises(KeyError, old.getall, 'a')
        self.assertRaises(KeyError, old.pop, 'a')
        self.assertEqual(old.pop('a', 42), 42)

        self.assertEqual(old.pop('b'), 2)
        self.assertEqual(len(old), 0)
        self.assertRaises(KeyError, old.pop, 'b')
        self.assertRaises(KeyError, old.__getitem__, 'b')

        self.assertRaises(KeyError, old.pop, 'c')
        self.assertEqual(old.pop('c', 42), 42)

        # Removes only the first key
        new = PVLMultiDict(the_list)
        self.assertEqual(new.pop('a'), 1)
        self.assertEqual(len(new), 2)
        self.assertListEqual(new.getall('a'), [3,])
        self.assertEqual(new.pop('a'), 3)
        self.assertEqual(new.pop('a', 42), 42)

        self.assertEqual(new.pop('b'), 2)
        self.assertEqual(len(new), 0)
        self.assertRaises(KeyError, new.pop, 'b')
        self.assertRaises(KeyError, new.__getitem__, 'b')

        self.assertRaises(KeyError, new.pop, 'c')
        self.assertEqual(new.pop('c', 42), 42)

    def test_popitem(self):
        the_list = [('a', 1), ('b', 2), ('a', 3)]

        # Removes the last item
        old = OrderedMultiDict(the_list)
        self.assertTupleEqual(old.popitem(), ('a', 3))
        self.assertEqual(len(old), 2)
        self.assertTupleEqual(old.popitem(), ('b', 2))
        self.assertEqual(len(old), 1)
        self.assertTupleEqual(old.popitem(), ('a', 1))
        self.assertEqual(len(old), 0)
        self.assertRaises(KeyError, old.popitem)

        # Removes a random item, in proper dict-like fashion
        new = PVLMultiDict(the_list)
        self.assertIn(new.popitem(), the_list)
        self.assertEqual(len(new), 2)
        new.popitem()
        new.popitem()
        self.assertRaises(KeyError, new.popitem)

    def test_repr(self):
        # Original repr
        old = OrderedMultiDict()
        self.assertEqual(repr(old), 'OrderedMultiDict([])')

        # MultiDict repr
        new = PVLMultiDict()
        self.assertEqual(repr(new), '<PVLMultiDict()>')

    def test_py3_items(self):
        the_list = [('a', 1), ('b', 2), ('a', 3)]

        # These views are returned as lists!
        old = OrderedMultiDict(the_list)
        self.assertIsInstance(old.items(), pvl.collections.ItemsView)
        self.assertIsInstance(old.keys(), pvl.collections.KeysView)
        self.assertIsInstance(old.values(), pvl.collections.ValuesView)

        # These are proper Python 3 views:
        new = PVLMultiDict(the_list)
        self.assertIsInstance(new.items(), abc.ItemsView)
        self.assertIsInstance(new.keys(), abc.KeysView)
        self.assertIsInstance(new.values(), abc.ValuesView)

        # However, if you wrap the new in a list, this is the same:
        for items, keys, values in (
                (old.items(), old.keys(), old.values()),
                (list(new.items()), list(new.keys()), list(new.values()))
        ):
            self.assertTupleEqual(items[0], ('a', 1))
            self.assertTupleEqual(items[1], ('b', 2))
            self.assertTupleEqual(items[2], ('a', 3))
            self.assertEqual(items.index(('a', 1)), 0)
            self.assertEqual(items.index(('b', 2)), 1)
            self.assertEqual(items.index(('a', 3)), 2)

            self.assertEqual(keys[0], 'a')
            self.assertEqual(keys[1], 'b')
            self.assertEqual(keys[2], 'a')
            self.assertEqual(keys.index('a'), 0)
            self.assertEqual(keys.index('b'), 1)

            self.assertEqual(values[0], 1)
            self.assertEqual(values[1], 2)
            self.assertEqual(values[2], 3)
            self.assertEqual(values.index(1), 0)
            self.assertEqual(values.index(2), 1)
            self.assertEqual(values.index(3), 2)

    def test_conversion(self):
        the_list = [('a', 1), ('b', 2), ('a', 3)]

        # This returns a list of key, value tuple pairs
        old = OrderedMultiDict(the_list)
        self.assertListEqual(list(old), the_list)

        # This returns the same thing that calling list() on a dict would,
        # the list of keys
        new = PVLMultiDict(the_list)
        self.assertListEqual(list(new), ['a', 'b', 'a'])

        # This is the one failing test commited in pvl 0.3:
        # I'm not sure why it was expected to work, as there is no code
        # that does this.
        # expected_dict = {
        #     'a': [1, 3],
        #     'b': [2],
        # }
        # assert dict(module) == expected_dict
        # Since the OrderedMultiDict subclasses from dict, it is a 'mapping
        # object' and Python makes it into a dict with unique keys, inevitably
        # loosing the double value of 'a'.  There does not seem to be any
        # functionality within the pvl library that requires this test to pass.
        self.assertEqual(dict(old), {'a': 1, 'b': 2})
        self.assertEqual(dict(new), {'a': 1, 'b': 2})

    def test_equality(self):

        # There is an isinstance() check in the __eq__ operator
        oldmod = pvl.collections.PVLModule()
        oldgrp = pvl.collections.PVLGroup()
        oldobj = pvl.collections.PVLObject()

        self.assertEqual(oldmod, oldmod)
        self.assertNotEqual(oldmod, oldgrp)
        self.assertNotEqual(oldmod, oldobj)

        self.assertNotEqual(oldgrp, oldmod)
        self.assertEqual(oldgrp, oldgrp)
        self.assertNotEqual(oldgrp, oldobj)

        self.assertNotEqual(oldobj, oldmod)
        self.assertNotEqual(oldobj, oldgrp)
        self.assertEqual(oldobj, oldobj)

        # Value-based notion of equality
        newmod = pvl.collections.PVLModuleNew()
        newgrp = pvl.collections.PVLGroupNew()
        newobj = pvl.collections.PVLObjectNew()

        self.assertEqual(newmod, newgrp)
        self.assertEqual(newmod, newobj)