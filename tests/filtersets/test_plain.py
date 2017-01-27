# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django import forms

from url_filter.filters import Filter
from url_filter.filtersets.plain import PlainModelFilterSet


class TestPlainModelFilterSet(object):
    def test_get_filters_no_relations_place(self):
        class PlaceFilterSet(PlainModelFilterSet):
            class Meta(object):
                model = {
                    "id": 1,
                    "restaurant": {
                        "place": 1,
                        "waiters": [
                            {
                                "id": 1,
                                "name": "Joe",
                                "restaurant": 1
                            },
                            {
                                "id": 2,
                                "name": "Jonny",
                                "restaurant": 1
                            }
                        ],
                        "serves_hot_dogs": True,
                        "serves_pizza": False,
                    },
                    "nicknames": ["dogs"],
                    "name": "Demon Dogs",
                    "address": "944 W. Fullerton",
                    "ignored": [{}],
                }
                allow_related = False

        filters = PlaceFilterSet().get_filters()

        assert set(filters.keys()) == {
            'id', 'name', 'address', 'nicknames',
        }

        assert isinstance(filters['id'], Filter)
        assert isinstance(filters['id'].form_field, forms.IntegerField)
        assert isinstance(filters['name'], Filter)
        assert isinstance(filters['name'].form_field, forms.CharField)
        assert isinstance(filters['address'], Filter)
        assert isinstance(filters['address'].form_field, forms.CharField)

    def test_get_filters_with_both_reverse_and_direct_relations(self):
        class PlaceFilterSet(PlainModelFilterSet):
            class Meta(object):
                model = {
                    "id": 1,
                    "restaurant": {
                        "place": 1,
                        "waiters": [
                            {
                                "id": 1,
                                "name": "Joe",
                                "restaurant": 1
                            },
                            {
                                "id": 2,
                                "name": "Jonny",
                                "restaurant": 1
                            },
                        ],
                        "serves_hot_dogs": True,
                        "serves_pizza": False,
                        "dummy": [{}],
                        "ignored": [object()],
                    },
                    "nicknames": ["dogs"],
                    "name": "Demon Dogs",
                    "address": "944 W. Fullerton"
                }

        filters = PlaceFilterSet().get_filters()

        assert set(filters.keys()) == {
            'id', 'address', 'name', 'nicknames', 'restaurant',
        }
        assert set(filters['restaurant'].filters.keys()) == {
            'place', 'serves_hot_dogs', 'serves_pizza', 'waiters',
        }
        assert set(filters['restaurant'].filters['waiters'].filters.keys()) == {
            'id', 'name', 'restaurant',
        }

        assert isinstance(filters['id'], Filter)
        assert isinstance(filters['id'].form_field, forms.IntegerField)
        assert isinstance(filters['address'], Filter)
        assert isinstance(filters['address'].form_field, forms.CharField)
        assert isinstance(filters['name'], Filter)
        assert isinstance(filters['name'].form_field, forms.CharField)
        assert isinstance(filters['restaurant'], PlainModelFilterSet)
        assert isinstance(filters['restaurant'].filters['waiters'], PlainModelFilterSet)
