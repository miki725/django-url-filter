# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import pytest
from django import forms

from test_project.one_to_one.models import Place, Restaurant
from url_filter.filters import Filter
from url_filter.filtersets import ModelFilterSet


class TestModelFilterSet(object):
    def test_get_filters_no_model(self):
        class PlaceFilterSet(ModelFilterSet):
            pass

        with pytest.raises(AssertionError):
            PlaceFilterSet().get_filters()

    def test_get_filters_no_relations(self):
        class PlaceFilterSet(ModelFilterSet):
            class Meta(object):
                model = Place

        filters = PlaceFilterSet().get_filters()

        assert set(filters.keys()) == {'id', 'name', 'address'}

        assert isinstance(filters['id'], Filter)
        assert isinstance(filters['id'].form_field, forms.IntegerField)
        assert isinstance(filters['name'], Filter)
        assert isinstance(filters['name'].form_field, forms.CharField)
        assert isinstance(filters['address'], Filter)
        assert isinstance(filters['address'].form_field, forms.CharField)

    def test_get_filters_with_relations(self):
        class RestaurantFilterSet(ModelFilterSet):
            class Meta(object):
                model = Restaurant

        filters = RestaurantFilterSet().get_filters()

        assert set(filters.keys()) == {
            'place',
            'serves_hot_dogs',
            'serves_pizza',
        }

        assert isinstance(filters['serves_hot_dogs'], Filter)
        assert isinstance(filters['serves_hot_dogs'].form_field, forms.BooleanField)
        assert isinstance(filters['serves_pizza'], Filter)
        assert isinstance(filters['serves_pizza'].form_field, forms.BooleanField)
        assert isinstance(filters['place'], ModelFilterSet)
