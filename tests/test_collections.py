# -*- coding: utf-8 -*-
import pytest
import six
import pvl


class DictLike(object):
    def keys(self):
        return ['a', 'b', 'a']

    def __getitem__(self, key):
        return 42


def test_empty():
    module = pvl.PVLModule()

    assert len(module) == 0
    assert module.get('c', 42) == 42

    with pytest.raises(KeyError):
        module['c']


def test_list_creation():
    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    assert len(module) == 3
    assert module['a'] == 1
    assert module['b'] == 2
    assert module.getlist('a') == [1, 3]

    with pytest.raises(KeyError):
        module['c']

    assert module.get('c', 42) == 42

    with pytest.raises(TypeError):
        pvl.PVLModule([], [])

    module = pvl.PVLModule(DictLike())
    assert len(module) == 3
    assert module['a'] == 42
    assert module['b'] == 42
    assert module.getlist('a') == [42, 42]

    with pytest.raises(KeyError):
        module['c']


def test_dict_creation():
    module = pvl.PVLModule({'a': 1, 'b': 2})

    assert module['a'] == 1
    assert module['b'] == 2
    assert len(module) == 2

    with pytest.raises(KeyError):
        module['c']

    assert module.get('c', 42) == 42


def test_keyword_creation():
    module = pvl.PVLModule(a=1, b=2)

    assert module['a'] == 1
    assert module['b'] == 2
    assert len(module) == 2

    with pytest.raises(KeyError):
        module['c']

    assert module.get('c', 42) == 42


def test_key_access():
    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    assert module['a'] == 1
    assert module['b'] == 2

    with pytest.raises(KeyError):
        module['c']


def test_index_access():
    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    assert module[0] == ('a', 1)
    assert module[1] == ('b', 2)
    assert module[2] == ('a', 3)

    with pytest.raises(IndexError):
        module[3]


def test_slice_access():
    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    assert module[0:3] == [('a', 1), ('b', 2), ('a', 3)]
    assert module[1:] == [('b', 2), ('a', 3)]
    assert module[:-1] == [('a', 1), ('b', 2)]


def test_set():
    module = pvl.PVLModule()
    module['a'] = 1
    module['b'] = 2
    module['a'] = 3

    assert module['a'] == 3
    assert module['b'] == 2
    assert module.getlist('a') == [3]
    assert len(module) == 2

    with pytest.raises(KeyError):
        module['c']

    assert module.get('c', 42) == 42
    assert list(module) == [('a', 3), ('b', 2)]


def test_delete():
    module = pvl.PVLModule(a=1, b=2)

    assert len(module) == 2
    assert module['a'] == 1

    del module['a']
    assert len(module) == 1

    with pytest.raises(KeyError):
        module['a']

    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    assert len(module) == 3
    assert module['a'] == 1

    del module['a']
    assert len(module) == 1

    with pytest.raises(KeyError):
        module['a']

    with pytest.raises(KeyError):
        del module['c']


def test_clear():
    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    assert len(module) == 3
    assert module['a'] == 1

    module.clear()
    assert len(module) == 0
    assert module.getlist('a') == []

    with pytest.raises(KeyError):
        module['a']

    with pytest.raises(KeyError):
        module['b']

    module['a'] = 42
    assert len(module) == 1
    assert module['a'] == 42


def test_discard():
    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    assert len(module) == 3
    assert module['a'] == 1

    module.discard('a')
    assert len(module) == 1
    assert module.getlist('a') == []

    with pytest.raises(KeyError):
        module['a']

    assert module['b'] == 2
    module.discard('b')

    assert len(module) == 0

    with pytest.raises(KeyError):
        module['b']

    module.discard('c')
    assert len(module) == 0


def test_pop():
    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    assert len(module) == 3
    assert module.pop('a') == 1
    assert len(module) == 1

    with pytest.raises(KeyError):
        module['a']

    with pytest.raises(KeyError):
        module.pop('a')

    assert module.pop('a', 42) == 42

    assert module.pop('b') == 2
    assert len(module) == 0

    with pytest.raises(KeyError):
        module.pop('b')

    with pytest.raises(KeyError):
        module['b']

    assert module.pop('b', 42) == 42

    with pytest.raises(KeyError):
        module.pop('c')

    assert module.pop('c', 42) == 42


def test_popitem():
    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    assert len(module) == 3

    assert module.popitem() == ('a', 3)
    assert len(module) == 2

    assert module.popitem() == ('b', 2)
    assert len(module) == 1

    assert module.popitem() == ('a', 1)
    assert len(module) == 0

    with pytest.raises(KeyError):
        module.popitem()


def test_update():
    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    module.update({'a': 42, 'c': 7})
    assert len(module) == 3
    assert module['a'] == 42
    assert module['b'] == 2
    assert module['c'] == 7

    module.update()
    assert len(module) == 3
    assert module['a'] == 42
    assert module['b'] == 2
    assert module['c'] == 7


def test_append():
    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    module.append('a', 42)
    assert len(module) == 4
    assert module['a'] == 1
    assert module.getlist('a') == [1, 3, 42]

    module.append('c', 43)
    assert len(module) == 5
    assert module['c'] == 43
    assert module.getlist('c') == [43]


def test_len():
    module = pvl.PVLModule()
    assert len(module) == 0

    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])
    assert len(module) == 3


def test_repr():
    module = pvl.PVLModule()
    assert isinstance(repr(module), str)
    assert repr(module) == 'PVLModule([])'

    module = pvl.PVLModule(a=1)
    assert isinstance(repr(module), str)


@pytest.mark.skipif(six.PY3, reason='requires python2')
def test_py2_items():
    module = pvl.PVLModule()

    assert isinstance(module.items(), list)
    assert module.items() == []

    assert isinstance(module.keys(), list)
    assert module.keys() == []

    assert isinstance(module.values(), list)
    assert module.values() == []

    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    assert isinstance(module.items(), list)
    assert module.items() == [('a', 1), ('b', 2), ('a', 3)]

    assert isinstance(module.keys(), list)
    assert module.keys() == ['a', 'b', 'a']

    assert isinstance(module.values(), list)
    assert module.values() == [1, 2, 3]


if six.PY3:
    def iteritems(module):
        return module.items()

    def iterkeys(module):
        return module.keys()

    def itervalues(module):
        return module.values()

else:
    def iteritems(module):
        return module.iteritems()

    def iterkeys(module):
        return module.iterkeys()

    def itervalues(module):
        return module.itervalues()


def test_iterators():
    module = pvl.PVLModule()

    assert isinstance(iteritems(module), pvl._collections.MappingView)
    assert list(iteritems(module)) == []
    assert len(iteritems(module)) == 0
    assert isinstance(repr(iteritems(module)), str)
    assert ('a', 1) not in iteritems(module)

    assert isinstance(iterkeys(module), pvl._collections.MappingView)
    assert list(iterkeys(module)) == []
    assert len(iterkeys(module)) == 0
    assert isinstance(repr(iterkeys(module)), str)
    assert 'a' not in iterkeys(module)

    assert isinstance(itervalues(module), pvl._collections.MappingView)
    assert list(itervalues(module)) == []
    assert len(itervalues(module)) == 0
    assert isinstance(repr(itervalues(module)), str)
    assert 1 not in itervalues(module)

    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    assert isinstance(iteritems(module), pvl._collections.MappingView)
    assert list(iteritems(module)) == [('a', 1), ('b', 2), ('a', 3)]
    assert len(iteritems(module)) == 3
    assert isinstance(repr(iteritems(module)), str)
    assert ('a', 1) in iteritems(module)
    assert ('b', 2) in iteritems(module)
    assert ('a', 3) in iteritems(module)
    assert ('c', 4) not in iteritems(module)

    assert isinstance(iterkeys(module), pvl._collections.MappingView)
    assert list(iterkeys(module)) == ['a', 'b', 'a']
    assert len(iterkeys(module)) == 3
    assert isinstance(repr(iterkeys(module)), str)
    assert 'a' in iterkeys(module)
    assert 'b' in iterkeys(module)
    assert 'c' not in iterkeys(module)

    assert isinstance(itervalues(module), pvl._collections.MappingView)
    assert list(itervalues(module)) == [1, 2, 3]
    assert len(itervalues(module)) == 3
    assert isinstance(repr(itervalues(module)), str)
    assert 1 in itervalues(module)
    assert 2 in itervalues(module)
    assert 3 in itervalues(module)
    assert 4 not in itervalues(module)


def test_equlity():
    assert not pvl.PVLModule()
    assert not pvl.PVLGroup()
    assert not pvl.PVLObject()

    assert not not pvl.PVLModule(a=1)
    assert not not pvl.PVLGroup(a=1)
    assert not not pvl.PVLObject(a=1)

    assert pvl.PVLModule() == pvl.PVLModule()
    assert pvl.PVLModule() != pvl.PVLGroup()
    assert pvl.PVLModule() != pvl.PVLObject()

    assert pvl.PVLGroup() != pvl.PVLModule()
    assert pvl.PVLGroup() == pvl.PVLGroup()
    assert pvl.PVLGroup() != pvl.PVLObject()

    assert pvl.PVLObject() != pvl.PVLModule()
    assert pvl.PVLObject() != pvl.PVLGroup()
    assert pvl.PVLObject() == pvl.PVLObject()

    assert pvl.PVLModule() != pvl.PVLModule(a=1)
    assert pvl.PVLModule(a=1) == pvl.PVLModule(a=1)
    assert pvl.PVLModule(a=1) == pvl.PVLModule([('a', 1)])
    assert pvl.PVLModule(a=1) == pvl.PVLModule({'a': 1})
    assert pvl.PVLModule(a=1) != pvl.PVLModule(b=1)
    assert pvl.PVLModule(a=1) != pvl.PVLModule(a=2)


def test_copy():
    module = pvl.PVLModule()
    copy = module.copy()

    assert module == copy
    assert module is not copy

    module['c'] = 42
    assert module != copy

    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])
    copy = module.copy()

    assert module == copy
    assert module is not copy

    module['c'] = 42
    assert module != copy


def test_conversion():
    module = pvl.PVLModule([
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ])

    expected_dict = {
        'a': [1, 3],
        'b': [2],
    }

    expected_list = [
        ('a', 1),
        ('b', 2),
        ('a', 3),
    ]

    assert dict(module) == expected_dict
    assert list(module) == expected_list
