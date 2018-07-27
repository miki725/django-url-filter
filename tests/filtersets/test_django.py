# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import pytest
from django import forms
from django.db import models

from test_project.generic.models import ModelB
from test_project.many_to_many.models import Article as M2MArticle, Publication
from test_project.many_to_one.models import Article as M2OArticle
from test_project.one_to_one.models import Place, Restaurant
from url_filter.exceptions import SkipFilter
from url_filter.filters import Filter
from url_filter.filtersets import ModelFilterSet


class TestModelFilterSet(object):
    def test_get_filters_no_model(self):
        class PlaceFilterSet(ModelFilterSet):
            pass

        with pytest.raises(AssertionError):
            PlaceFilterSet().get_filters()

    def test_get_filters_no_relations_place(self):
        class PlaceFilterSet(ModelFilterSet):
            class Meta(object):
                model = Place
                allow_related = False
                allow_related_reverse = False
                extra_kwargs = {
                    'id': {'no_lookup': True},
                }

        filters = PlaceFilterSet().get_filters()

        assert set(filters.keys()) == {
            'id', 'name', 'address',
        }

        assert isinstance(filters['id'], Filter)
        assert isinstance(filters['id'].form_field, forms.IntegerField)
        assert filters['id'].no_lookup is True
        assert isinstance(filters['name'], Filter)
        assert isinstance(filters['name'].form_field, forms.CharField)
        assert isinstance(filters['address'], Filter)
        assert isinstance(filters['address'].form_field, forms.CharField)

    def test_get_filters_no_relations_place_diff_source(self):
        class PlaceFilterSet(ModelFilterSet):
            class Meta(object):
                model = Place
                allow_related = False
                allow_related_reverse = False
                fields = ['id', 'name', 'location']
                extra_kwargs = {
                    'id': {'no_lookup': True},
                    'location': {'source': 'address'}
                }

        filters = PlaceFilterSet().get_filters()

        assert set(filters.keys()) == {
            'id', 'name', 'location',
        }

        assert isinstance(filters['id'], Filter)
        assert isinstance(filters['id'].form_field, forms.IntegerField)
        assert filters['id'].no_lookup is True
        assert isinstance(filters['name'], Filter)
        assert isinstance(filters['name'].form_field, forms.CharField)
        assert isinstance(filters['location'], Filter)
        assert isinstance(filters['location'].form_field, forms.CharField)

    def test_get_filters_no_relations_place_exclude_address(self):
        class PlaceFilterSet(ModelFilterSet):
            class Meta(object):
                model = Place
                exclude = ['address']
                allow_related = False
                allow_related_reverse = False

        filters = PlaceFilterSet().get_filters()

        assert set(filters.keys()) == {
            'id', 'name',
        }

        assert isinstance(filters['id'], Filter)
        assert isinstance(filters['id'].form_field, forms.IntegerField)
        assert isinstance(filters['name'], Filter)
        assert isinstance(filters['name'].form_field, forms.CharField)

    def test_get_filters_no_relations_place_address_overwrite(self):
        class PlaceFilterSet(ModelFilterSet):
            address = Filter(forms.IntegerField())

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
        assert isinstance(filters['address'].form_field, forms.IntegerField)

    def test_get_filters_no_relations_restaurant(self):
        class RestaurantFilterSet(ModelFilterSet):
            class Meta(object):
                model = Restaurant
                allow_related = False
                allow_related_reverse = False

        filters = RestaurantFilterSet().get_filters()

        assert set(filters.keys()) == {
            'serves_pizza', 'serves_hot_dogs',
        }

        assert isinstance(filters['serves_pizza'], Filter)
        assert isinstance(filters['serves_pizza'].form_field, forms.BooleanField)
        assert isinstance(filters['serves_hot_dogs'], Filter)
        assert isinstance(filters['serves_hot_dogs'].form_field, forms.BooleanField)

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
                extra_kwargs = {
                    'place': {
                        'id': {'no_lookup': True},
                    },
                }

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

        assert filters['place'].filters['id'].no_lookup is True

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
                model = M2MArticle

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

    def test_get_filters_with_many_to_one_relations(self):
        class ArticleFilterSet(ModelFilterSet):
            class Meta(object):
                model = M2OArticle

        filters = ArticleFilterSet().get_filters()

        assert set(filters.keys()) == {
            'id', 'headline', 'pub_date', 'reporter',
        }
        assert set(filters['reporter'].filters.keys()) == {
            'id', 'email', 'first_name', 'last_name',
        }

        assert isinstance(filters['id'], Filter)
        assert isinstance(filters['id'].form_field, forms.IntegerField)
        assert isinstance(filters['headline'], Filter)
        assert isinstance(filters['headline'].form_field, forms.CharField)
        assert isinstance(filters['pub_date'], Filter)
        assert isinstance(filters['pub_date'].form_field, forms.DateField)
        assert isinstance(filters['reporter'], ModelFilterSet)

    def test_get_filters_without_generic_foreign_key(self):
        class ModelBFilterSet(ModelFilterSet):
            class Meta(object):
                model = ModelB

        filters = ModelBFilterSet().get_filters()

        assert set(filters.keys()) == {
            'id', 'name', 'a', 'content_type', 'object_id',
        }

    def test_get_form_field_for_field(self):
        fs = ModelFilterSet()

        assert isinstance(fs._get_form_field_for_field(models.CharField()), forms.CharField)
        assert isinstance(fs._get_form_field_for_field(models.AutoField()), forms.IntegerField)
        assert isinstance(fs._get_form_field_for_field(models.FileField()), forms.CharField)

        class TestField(models.Field):
            def formfield(self, **kwargs):
                return

        with pytest.raises(SkipFilter):
            fs._get_form_field_for_field(TestField())
