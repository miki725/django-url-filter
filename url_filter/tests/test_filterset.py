# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import pytest
from django import forms
from django.http import QueryDict

from url_filter.filter import Filter
from url_filter.filterset import FilterSet
from url_filter.utils import FilterSpec


def test_filter_no_queryset():
    fs = FilterSet()
    with pytest.raises(AssertionError):
        fs.filter()


def test_filter_data_not_querydict():
    fs = FilterSet(queryset=[])
    with pytest.raises(AssertionError):
        fs.filter()


def test_get_specs():
    class Bar(FilterSet):
        other = Filter(source='stuff',
                       form_field=forms.CharField(),
                       default_lookup='contains')
        thing = Filter(form_field=forms.IntegerField(min_value=0, max_value=15))

    class Foo(FilterSet):
        field = Filter(form_field=forms.CharField())
        bar = Bar()

    def _test(data, expected):
        fs = Foo(data=QueryDict(data),
                 queryset=[],
                 strict_mode='drop')

        assert set(fs.get_specs()) == set(expected)

    _test('field=earth&bar__other=mars', [
        FilterSpec(['field'], 'exact', 'earth', False),
        FilterSpec(['bar', 'stuff'], 'contains', 'mars', False),
    ])
    _test('field!=earth&bar__other=mars', [
        FilterSpec(['field'], 'exact', 'earth', True),
        FilterSpec(['bar', 'stuff'], 'contains', 'mars', False),
    ])
    _test('field__in=earth,pluto&bar__other__icontains!=mars', [
        FilterSpec(['field'], 'in', ['earth', 'pluto'], False),
        FilterSpec(['bar', 'stuff'], 'icontains', 'mars', True),
    ])
    _test('fields__in=earth,pluto&bar__other__icontains!=mars', [
        FilterSpec(['bar', 'stuff'], 'icontains', 'mars', True),
    ])
    _test('field__in=earth,pluto&bar__ot!her__icontains!=mars', [
        FilterSpec(['field'], 'in', ['earth', 'pluto'], False),
    ])
    _test('bar__thing=5', [
        FilterSpec(['bar', 'thing'], 'exact', 5, False),
    ])
    _test('bar__thing__in=5,10,15', [
        FilterSpec(['bar', 'thing'], 'in', [5, 10, 15], False),
    ])
    _test('bar__thing__range=5,10', [
        FilterSpec(['bar', 'thing'], 'range', [5, 10], False),
    ])
    _test('bar__thing__range=5,10,15', [])
    _test('bar__thing=100', [])
    _test('bar__thing__in=100,5', [])
