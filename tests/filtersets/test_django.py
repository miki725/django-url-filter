# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import pytest
from django import forms

from test_project.many_to_many.models import Article, Publication
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
                allow_related = False
                allow_related_reverse = False

        filters = PlaceFilterSet().get_filters()

        assert set(filters.keys()) == {
            'id', 'name', 'address',
        }

        assert isinstance(filters['id'], Filter)
        assert isinstance(filters['id'].form_field, forms.IntegerField)
        assert isinstance(filters['name'], Filter)
        assert isinstance(filters['name'].form_field, forms.CharField)
        assert isinstance(filters['address'], Filter)
        assert isinstance(filters['address'].form_field, forms.CharField)

    def test_get_filters_with_only_reverse_relations(self):
        class PlaceFilterSet(ModelFilterSet):
            class Meta(object):
                model = Place

        filters = PlaceFilterSet().get_filters()

        assert set(filters.keys()) == {
            'id', 'name', 'address', 'restaurant',
        }
        assert set(filters['restaurant'].filters.keys()) == {
            'serves_pizza', 'serves_hot_dogs', 'waiter',
        }

        assert isinstance(filters['id'], Filter)
        assert isinstance(filters['id'].form_field, forms.IntegerField)
        assert isinstance(filters['name'], Filter)
        assert isinstance(filters['name'].form_field, forms.CharField)
        assert isinstance(filters['address'], Filter)
        assert isinstance(filters['address'].form_field, forms.CharField)
        assert isinstance(filters['restaurant'], ModelFilterSet)

    def test_get_filters_with_both_reverse_and_direct_relations(self):
        class RestaurantFilterSet(ModelFilterSet):
            class Meta(object):
                model = Restaurant

        filters = RestaurantFilterSet().get_filters()

        assert set(filters.keys()) == {
            'place', 'waiter', 'serves_hot_dogs', 'serves_pizza',
        }
        assert set(filters['place'].filters.keys()) == {
            'id', 'name', 'address',
        }
        assert set(filters['waiter'].filters.keys()) == {
            'id', 'name',
        }

        assert isinstance(filters['serves_hot_dogs'], Filter)
        assert isinstance(filters['serves_hot_dogs'].form_field, forms.BooleanField)
        assert isinstance(filters['serves_pizza'], Filter)
        assert isinstance(filters['serves_pizza'].form_field, forms.BooleanField)
        assert isinstance(filters['place'], ModelFilterSet)
        assert isinstance(filters['waiter'], ModelFilterSet)

    def test_get_filters_with_reverse_many_to_many_relations(self):
        class PublicationFilterSet(ModelFilterSet):
            class Meta(object):
                model = Publication

        filters = PublicationFilterSet().get_filters()

        assert set(filters.keys()) == {
            'id', 'title', 'articles',
        }
        assert set(filters['articles'].filters.keys()) == {
            'id', 'headline',
        }

        assert isinstance(filters['id'], Filter)
        assert isinstance(filters['id'].form_field, forms.IntegerField)
        assert isinstance(filters['title'], Filter)
        assert isinstance(filters['title'].form_field, forms.CharField)
        assert isinstance(filters['articles'], ModelFilterSet)

    def test_get_filters_with_many_to_many_relations(self):
        class ArticleFilterSet(ModelFilterSet):
            class Meta(object):
                model = Article

        filters = ArticleFilterSet().get_filters()

        assert set(filters.keys()) == {
            'id', 'headline', 'publications',
        }
        assert set(filters['publications'].filters.keys()) == {
            'id', 'title',
        }

        assert isinstance(filters['id'], Filter)
        assert isinstance(filters['id'].form_field, forms.IntegerField)
        assert isinstance(filters['headline'], Filter)
        assert isinstance(filters['headline'].form_field, forms.CharField)
        assert isinstance(filters['publications'], ModelFilterSet)
