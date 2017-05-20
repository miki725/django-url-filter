# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from datetime import datetime

from url_filter.backends.plain import PlainFilterBackend
from url_filter.utils import FilterSpec


class Bunch(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs


DATA = [
    {
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
            "serves_pizza": False
        },
        "name": "Demon Dogs",
        "address": "944 W. Fullerton",
        "nicknames": [
            "dogs",
        ],
        "created": datetime(2015, 6, 12, 9, 30, 55),
    },
    {
        "id": 2,
        "restaurant": {
            "place": 2,
            "waiters": [
                Bunch(**{
                    "id": 3,
                    "name": "Steve",
                    "restaurant": 2
                })
            ],
            "serves_hot_dogs": True,
            "serves_pizza": False
        },
        "name": "Ace Hardware",
        "address": "1013 N. Ashland",
        "nicknames": [
            "Ace",
            "ace",
        ],
        "created": datetime(2014, 5, 12, 14, 30, 37),
        "nulldata": None,
    }
]


class TestPlainFilterBackend(object):
    def test_get_model(self):
        backend = PlainFilterBackend([])

        assert backend.get_model() is object
        assert not backend.enforce_same_models

    def test_filter_no_specs(self):
        qs = ['hello']
        backend = PlainFilterBackend(qs)
        backend.bind([])

        assert backend.filter() is qs

    def _test_filter(self, spec, expected):
        backend = PlainFilterBackend(DATA)
        backend.bind([spec])

        assert backend.filter() == expected

    def test_filter_contains(self):
        self._test_filter(
            FilterSpec(['restaurant', 'waiters', 'name'], 'contains', 'Jo', False),
            [DATA[0]]
        )

    def test_filter_endswith(self):
        self._test_filter(
            FilterSpec(['restaurant', 'waiters', 'name'], 'endswith', 'e', False),
            DATA
        )

    def test_filter_exact(self):
        self._test_filter(
            FilterSpec(['restaurant', 'waiters', 'name'], 'exact', 'John', False),
            []
        )

    def test_filter_exact_simple_list(self):
        self._test_filter(
            FilterSpec(['nicknames'], 'exact', 'ace', False),
            [DATA[1]]
        )

    def test_filter_exact_negated(self):
        self._test_filter(
            FilterSpec(['restaurant', 'waiters', 'name'], 'exact', 'John', True),
            DATA
        )

    def test_filter_gt(self):
        self._test_filter(
            FilterSpec(['id'], 'gt', 1, False),
            [DATA[1]]
        )

    def test_filter_gte(self):
        self._test_filter(
            FilterSpec(['id'], 'gte', 1, False),
            DATA
        )

    def test_filter_icontains(self):
        self._test_filter(
            FilterSpec(['restaurant', 'waiters', 'name'], 'icontains', 'jo', False),
            [DATA[0]]
        )

    def test_filter_iendswith(self):
        self._test_filter(
            FilterSpec(['restaurant', 'waiters', 'name'], 'iendswith', 'E', False),
            DATA
        )

    def test_filter_iexact(self):
        self._test_filter(
            FilterSpec(['restaurant', 'waiters', 'name'], 'iexact', 'joe', False),
            [DATA[0]]
        )

    def test_filter_in(self):
        self._test_filter(
            FilterSpec(['restaurant', 'waiters', 'name'], 'in', ['John', 'Steve'], False),
            [DATA[1]]
        )

    def test_filter_in_simple_list(self):
        self._test_filter(
            FilterSpec(['nicknames'], 'in', ['ace', 'dogs'], False),
            DATA
        )

    def test_filter_isnull(self):
        self._test_filter(
            FilterSpec(['nulldata'], 'isnull', True, False),
            [DATA[1]]
        )
        self._test_filter(
            FilterSpec(['nulldata'], 'isnull', False, False),
            [DATA[0]]
        )

    def test_filter_istartswith(self):
        self._test_filter(
            FilterSpec(['restaurant', 'waiters', 'name'], 'istartswith', 'j', False),
            [DATA[0]]
        )

    def test_filter_lt(self):
        self._test_filter(
            FilterSpec(['id'], 'lt', 2, False),
            [DATA[0]]
        )

    def test_filter_lte(self):
        self._test_filter(
            FilterSpec(['id'], 'lte', 2, False),
            DATA
        )

    def test_filter_range(self):
        self._test_filter(
            FilterSpec(['id'], 'range', [1, 2], False),
            DATA
        )

    def test_filter_startswith(self):
        self._test_filter(
            FilterSpec(['restaurant', 'waiters', 'name'], 'startswith', 'J', False),
            [DATA[0]]
        )

    def test_filter_regex(self):
        self._test_filter(
            FilterSpec(['restaurant', 'waiters', 'name'], 'regex', r'^J.*', False),
            [DATA[0]]
        )

    def test_filter_iregex(self):
        self._test_filter(
            FilterSpec(['restaurant', 'waiters', 'name'], 'iregex', r'^j.*', False),
            [DATA[0]]
        )

    def test_filter_day(self):
        self._test_filter(
            FilterSpec(['created'], 'day', 12, False),
            DATA
        )

    def test_filter_hour(self):
        self._test_filter(
            FilterSpec(['created'], 'hour', 9, False),
            [DATA[0]]
        )

    def test_filter_second(self):
        self._test_filter(
            FilterSpec(['created'], 'second', 37, False),
            [DATA[1]]
        )

    def test_filter_minute(self):
        self._test_filter(
            FilterSpec(['created'], 'minute', 30, False),
            DATA
        )

    def test_filter_month(self):
        self._test_filter(
            FilterSpec(['created'], 'month', 5, False),
            [DATA[1]]
        )

    def test_filter_year(self):
        self._test_filter(
            FilterSpec(['created'], 'year', 2015, False),
            [DATA[0]]
        )

    def test_filter_week_day(self):
        self._test_filter(
            FilterSpec(['created'], 'week_day', 1, False),
            [DATA[1]]
        )

    def test_filter_exception_handling(self):
        self._test_filter(
            FilterSpec(['id'], 'week_day', 1, False),
            DATA
        )
