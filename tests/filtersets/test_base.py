# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import pytest
from django import forms
from django.http import QueryDict

from test_project.one_to_one.models import Restaurant, Waiter
from url_filter.backends.django import DjangoFilterBackend
from url_filter.constants import StrictMode
from url_filter.exceptions import Empty
from url_filter.filters import Filter
from url_filter.filtersets.base import FilterSet
from url_filter.utils import FilterSpec


class TestFilterSet(object):
    def test_init(self):
        fs = FilterSet(
            data='some data',
            queryset='queryset',
            context={'context': 'here'},
            strict_mode=StrictMode.fail,
        )

        assert fs.data == 'some data'
        assert fs.queryset == 'queryset'
        assert fs.context == {'context': 'here'}
        assert fs.strict_mode == StrictMode.fail

    def test_repr(self):
        class FooFilterSet(FilterSet):
            foo = Filter(form_field=forms.CharField())

        class BarFilterSet(FilterSet):
            bar = Filter(form_field=forms.IntegerField())
            foo = FooFilterSet()

        assert repr(BarFilterSet()) == (
            'BarFilterSet()\n'
            '  bar = Filter(source="bar", form_field=IntegerField, lookups=ALL, default_lookup="exact", is_default=False, no_lookup=False)\n'
            '  foo = FooFilterSet(source="foo")\n'
            '    foo = Filter(source="foo", form_field=CharField, lookups=ALL, default_lookup="exact", is_default=False, no_lookup=False)'
        )

    def test_get_filters(self):
        class TestFilterSet(FilterSet):
            foo = Filter(form_field=forms.CharField())

        filters = TestFilterSet().get_filters()

        assert isinstance(filters, dict)
        assert list(filters.keys()) == ['foo']
        assert isinstance(filters['foo'], Filter)
        assert filters['foo'].parent is None

    def test_filters(self):
        class TestFilterSet(FilterSet):
            foo = Filter(form_field=forms.CharField())

        fs = TestFilterSet()
        filters = fs.filters

        assert isinstance(filters, dict)
        assert list(filters.keys()) == ['foo']
        assert isinstance(filters['foo'], Filter)
        assert filters['foo'].parent is fs
        assert filters['foo'].name == 'foo'

    def test_default_filter_no_default(self):
        class TestFilterSet(FilterSet):
            foo = Filter(form_field=forms.CharField())

        assert TestFilterSet().default_filter is None

    def test_default_filter(self):
        class TestFilterSet(FilterSet):
            foo = Filter(form_field=forms.CharField(), is_default=True)
            bar = Filter(form_field=forms.CharField())

        default = TestFilterSet().default_filter

        assert isinstance(default, Filter)
        assert default.name == 'foo'

    def test_validate_key(self):
        assert FilterSet().validate_key('foo') is None
        assert FilterSet().validate_key('foo__bar') is None
        assert FilterSet().validate_key('foo__bar!') is None

        with pytest.raises(forms.ValidationError):
            FilterSet().validate_key('f!oo')

    def test_get_filter_backend(self):
        backend = FilterSet().get_filter_backend()

        assert isinstance(backend, DjangoFilterBackend)

    def test_filter_no_queryset(self):
        fs = FilterSet()
        with pytest.raises(AssertionError):
            fs.filter()

    def test_filter_data_not_querydict(self):
        fs = FilterSet(queryset=[])
        with pytest.raises(AssertionError):
            fs.filter()

    def test_get_specs(self):
        class BarFilterSet(FilterSet):
            other = Filter(source='stuff',
                           form_field=forms.CharField(),
                           default_lookup='contains')
            thing = Filter(form_field=forms.IntegerField(min_value=0, max_value=15))

        class FooFilterSet(FilterSet):
            field = Filter(form_field=forms.CharField())
            bar = BarFilterSet()

        def _test(data, expected, **kwargs):
            fs = FooFilterSet(
                data=QueryDict(data),
                queryset=[],
                **kwargs
            )

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
        _test('bar=5', [])
        _test('bar__thing__range=5,10,15', [], strict_mode=StrictMode.drop)
        _test('bar__thing__range=5,100', [], strict_mode=StrictMode.drop)
        _test('bar__thing=100', [], strict_mode=StrictMode.drop)
        _test('bar__thing__in=100,50', [], strict_mode=StrictMode.drop)
        _test('bar__thing__in=100,5', [
            FilterSpec(['bar', 'thing'], 'in', [5], False)
        ], strict_mode=StrictMode.drop)
        _test('bar__thing__in=100,5', [
            FilterSpec(['bar', 'thing'], 'in', [5], False)
        ], strict_mode=StrictMode.empty)

        with pytest.raises(forms.ValidationError):
            _test('bar__thing__in=100,5', [], strict_mode=StrictMode.fail)

        with pytest.raises(Empty):
            _test('bar__thing__in=100,50', [], strict_mode=StrictMode.empty)

        with pytest.raises(Empty):
            _test('bar__thing__range=5,100', [], strict_mode=StrictMode.empty)

    def test_get_specs_using_default_filter(self):
        class BarFilterSet(FilterSet):
            id = Filter(form_field=forms.IntegerField(),
                        is_default=True)
            other = Filter(source='stuff',
                           form_field=forms.CharField(),
                           default_lookup='contains')
            thing = Filter(form_field=forms.IntegerField(min_value=0, max_value=15))

        class FooFilterSet(FilterSet):
            field = Filter(form_field=forms.CharField(), is_default=True)
            bar = BarFilterSet()

        def _test(data, expected, **kwargs):
            fs = FooFilterSet(
                data=QueryDict(data),
                queryset=[],
                **kwargs
            )

            assert set(fs.get_specs()) == set(expected)

        _test('bar=5', [
            FilterSpec(['bar', 'id'], 'exact', 5, False),
        ])
        _test('bar__isnull=True', [
            FilterSpec(['bar', 'id'], 'isnull', True, False),
        ])
        _test('bar__gt=foo', [], strict_mode=StrictMode.drop)
        _test('page=1', [], strict_mode=StrictMode.fail)

        with pytest.raises(forms.ValidationError):
            _test('bar=aa', [], strict_mode=StrictMode.fail)

        with pytest.raises(Empty):
            _test('bar__in=aa', [], strict_mode=StrictMode.empty)

    def test_filter_one_to_one(self, one_to_one):
        class PlaceFilterSet(FilterSet):
            pk = Filter(form_field=forms.IntegerField(min_value=0), is_default=True)
            name = Filter(form_field=forms.CharField(max_length=50))
            address = Filter(form_field=forms.CharField(max_length=80))

        class RestaurantFilterSet(FilterSet):
            pk = Filter(form_field=forms.IntegerField(min_value=0), is_default=True)
            place = PlaceFilterSet()
            place_id = Filter(form_field=forms.IntegerField(min_value=0))
            serves_hot_dogs = Filter(form_field=forms.BooleanField(required=False))
            serves_pizza = Filter(form_field=forms.BooleanField(required=False))

        class WaiterFilterSet(FilterSet):
            pk = Filter(form_field=forms.IntegerField(min_value=0), is_default=True)
            restaurant = RestaurantFilterSet()
            name = Filter(form_field=forms.CharField(max_length=50))

        def _test(fs, data, qs, expected, count):
            _fs = fs(
                data=QueryDict(data),
                queryset=qs,
            )

            filtered = _fs.filter()
            assert filtered.count() == count
            assert set(filtered) == set(expected)

        _test(
            RestaurantFilterSet,
            'pk=hello',
            Restaurant.objects.all(),
            Restaurant.objects.none(),
            0
        )
        _test(
            RestaurantFilterSet,
            'place__name__startswith=Demon',
            Restaurant.objects.all(),
            Restaurant.objects.filter(place__name__startswith='Demon'),
            1
        )
        _test(
            RestaurantFilterSet,
            'place__address__contains!=Ashland',
            Restaurant.objects.all(),
            Restaurant.objects.exclude(place__address__contains='Ashland'),
            1
        )
        _test(
            RestaurantFilterSet,
            'place_id__isnull=True',
            Restaurant.objects.all(),
            Restaurant.objects.filter(place_id__isnull=True),
            0
        )
        _test(
            RestaurantFilterSet,
            'place_id__isnull=False',
            Restaurant.objects.all(),
            Restaurant.objects.filter(place_id__isnull=False),
            2
        )
        _test(
            WaiterFilterSet,
            'restaurant__place__pk=1',
            Waiter.objects.all(),
            Waiter.objects.filter(restaurant__place=1),
            2
        )
        _test(
            WaiterFilterSet,
            'restaurant__place=1',
            Waiter.objects.all(),
            Waiter.objects.filter(restaurant__place=1),
            2
        )
        _test(
            WaiterFilterSet,
            'restaurant__place__name__startswith=Demon',
            Waiter.objects.all(),
            Waiter.objects.filter(restaurant__place__name__startswith="Demon"),
            2
        )
        _test(
            WaiterFilterSet,
            ('restaurant__place__name__startswith=Demon'
             '&name__icontains!=jon'),
            Waiter.objects.all(),
            (Waiter.objects
             .filter(restaurant__place__name__startswith="Demon")
             .exclude(name__icontains='jon')),
            1
        )
