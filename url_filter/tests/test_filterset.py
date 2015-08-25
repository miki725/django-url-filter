# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import pytest
from django import forms
from django.core.management import call_command
from django.http import QueryDict

from test_project.one_to_one.models import Restaurant, Waiter
from url_filter.filter import Filter
from url_filter.filterset import FilterSet
from url_filter.utils import FilterSpec


class TestFilterSet(object):

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

        def _test(data, expected):
            fs = FooFilterSet(
                data=QueryDict(data),
                queryset=[],
                strict_mode='drop',
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
        _test('bar__thing__range=5,10,15', [])
        _test('bar__thing=100', [])
        _test('bar__thing__in=100,5', [])

    def test_filter_one_to_one(self, db):
        call_command('loaddata', 'one_to_one.json')

        class PlaceFilterSet(FilterSet):
            pk = Filter(form_field=forms.IntegerField(min_value=0))
            name = Filter(form_field=forms.CharField(max_length=50))
            address = Filter(form_field=forms.CharField(max_length=80))

        class RestaurantFilterSet(FilterSet):
            pk = Filter(form_field=forms.IntegerField(min_value=0))
            place = PlaceFilterSet()
            serves_hot_dogs = Filter(form_field=forms.BooleanField(required=False))
            serves_pizza = Filter(form_field=forms.BooleanField(required=False))

        class WaiterFilterSet(FilterSet):
            pk = Filter(form_field=forms.IntegerField(min_value=0))
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
            WaiterFilterSet,
            'restaurant__place__pk=1',
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
