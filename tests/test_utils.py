# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from url_filter.utils import FilterSpec, LookupConfig, SubClassDict


class TestFilterSpec(object):
    def test_repr(self):
        assert repr(FilterSpec(['a', 'b'], 'exact', 'value', False)) == (
            '<FilterSpec a.b exact {}>'.format(repr('value'))
        )
        assert repr(FilterSpec(['a', 'b'], 'exact', 'value', True)) == (
            '<FilterSpec a.b NOT exact {}>'.format(repr('value'))
        )

    def test_equality(self):
        a = FilterSpec(['a', 'b'], 'exact', 'value', False)
        b = FilterSpec(['a', 'b'], 'exact', 'value', False)
        c = FilterSpec(['a', 'b'], 'exact', 'value', True)
        d = FilterSpec(['a', 'b'], 'contains', 'value', False)

        assert a == b
        assert a != c
        assert a != d


class TestLookupConfig(object):
    def test_repr(self):
        data = {
            'key': 'value',
        }
        config = LookupConfig('foo', data)

        assert repr(config) == (
            '<LookupConfig foo=>{}>'.format(repr({'key': 'value'}))
        )

    def test_properties(self):
        data = {
            'key': 'value',
        }
        config = LookupConfig('foo', data)

        assert config.name == 'key'
        assert config.value.data == 'value'
        assert config.is_key_value()

    def test_as_dict(self):
        data = {
            'one': {
                'two': {
                    'three': 'value',
                }
            }
        }

        config = LookupConfig('key', data)

        assert config.as_dict() == data


class TestSubClassDict(object):
    def test_get(self):
        class Klass(object):
            pass

        class Foo(object):
            pass

        class Bar(Foo):
            pass

        mapping = SubClassDict({
            Foo: 'foo',
            Klass: 'klass',
            'key': 'value',
        })

        assert mapping.get('key') == 'value'
        assert mapping.get(Klass) == 'klass'
        assert mapping.get(Foo) == 'foo'
        assert mapping.get(Bar) == 'foo'
        assert mapping.get('not-there') is None
