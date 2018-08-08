# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import pytest
import six
from alchemy_mock.comparison import ExpressionMatcher
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.types import String

from test_project.one_to_one.alchemy import Place, Restaurant, Waiter
from url_filter.backends.sqlalchemy import SQLAlchemyFilterBackend
from url_filter.utils import FilterSpec


def assert_alchemy_expressions_equal(exp1, exp2):
    assert ExpressionMatcher(exp1) == exp2


class TestSQLAlchemyFilterBackend(object):
    def test_init(self, alchemy_db):
        backend = SQLAlchemyFilterBackend(
            alchemy_db.query(Place),
            context={'context': 'here'},
        )

        assert backend.model is Place
        assert backend.context == {'context': 'here'}

        with pytest.raises(AssertionError):
            SQLAlchemyFilterBackend(
                alchemy_db.query(Place, Restaurant),
            )

    def test_empty(self, alchemy_db):
        backend = SQLAlchemyFilterBackend(
            alchemy_db.query(Place),
            context={'context': 'here'},
        )

        assert 'WHERE 0 = 1' in six.text_type(backend.empty())

    def test_get_model(self, alchemy_db):
        backend = SQLAlchemyFilterBackend(alchemy_db.query(Place))

        assert backend.get_model() is Place

    def test_filter_no_specs(self, alchemy_db):
        qs = alchemy_db.query(Place)

        backend = SQLAlchemyFilterBackend(qs)
        backend.bind([])

        assert backend.filter() is qs

    def test_filter(self, alchemy_db):
        backend = SQLAlchemyFilterBackend(
            alchemy_db.query(Place),
        )
        backend.bind([
            FilterSpec(['restaurant', 'waiter_set', 'name'], 'exact', 'John', False),
        ])

        filtered = backend.filter()

        sql = six.text_type(filtered)
        assert sql == (
            'SELECT one_to_one_place.id AS one_to_one_place_id, '
            'one_to_one_place.name AS one_to_one_place_name, '
            'one_to_one_place.address AS one_to_one_place_address \n'
            'FROM one_to_one_place '
            'JOIN one_to_one_restaurant '
            'ON one_to_one_restaurant.place_id = one_to_one_place.id '
            'JOIN one_to_one_waiter '
            'ON one_to_one_waiter.restaurant_id = one_to_one_restaurant.place_id '
            '\nWHERE one_to_one_waiter.name ={}'.format(sql.rsplit('=', 1)[-1])
        )

    def test_filter_already_eagerloaded(self, alchemy_db):
        backend = SQLAlchemyFilterBackend(
            alchemy_db.query(Place).options(joinedload(Place.restaurant).joinedload(Restaurant.waiter_set)),
        )
        backend.bind([
            FilterSpec(['restaurant', 'waiter_set', 'name'], 'exact', 'John', False),
        ])

        filtered = backend.filter()

        sql = six.text_type(filtered)
        assert 'place JOIN one_to_one' not in sql
        assert 'place LEFT OUTER JOIN one_to_one' in sql

    def _test_build_clause(self, alchemy_db, name, lookup, value, expected, is_negated=False):
        backend = SQLAlchemyFilterBackend(
            alchemy_db.query(Place),
        )

        clause, to_join = backend.build_clause(
            FilterSpec(['restaurant', 'waiter_set', name], lookup, value, is_negated)
        )

        assert to_join == [Place.restaurant, Restaurant.waiter_set]
        assert_alchemy_expressions_equal(clause, expected)

    def test_build_clause_contains(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'contains', 'John',
            Waiter.name.contains('John')
        )

    def test_build_clause_endswith(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'endswith', 'John',
            Waiter.name.endswith('John')
        )

    def test_build_clause_exact(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'exact', 'John',
            Waiter.name == 'John'
        )

    def test_build_clause_exact_negated(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'exact', 'John',
            Waiter.name != 'John',
            True
        )

    def test_build_clause_gt(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'id', 'gt', 1,
            Waiter.id > 1
        )

    def test_build_clause_gte(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'id', 'gte', 1,
            Waiter.id >= 1
        )

    def test_build_clause_icontains(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'icontains', 'Django',
            func.lower(Waiter.name).contains('django')
        )

    def test_build_clause_icontains_cant_lower(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'icontains', 5,
            func.lower(Waiter.name).contains(5)
        )

    def test_build_clause_iendswith(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'iendswith', 'Django',
            func.lower(Waiter.name).endswith('django')
        )

    def test_build_clause_iexact(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'iexact', 'Django',
            func.lower(Waiter.name) == 'django'
        )

    def test_build_clause_in(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'in', ['Django', 'rocks'],
            Waiter.name.in_(['Django', 'rocks'])
        )

    def test_build_clause_iin(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'iin', ['Django', 'rocks'],
            func.lower(Waiter.name).in_(['django', 'rocks'])
        )

    def test_build_clause_isnull(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'isnull', True,
            Waiter.name == None  # noqa
        )
        self._test_build_clause(
            alchemy_db, 'name', 'isnull', False,
            Waiter.name != None  # noqa
        )

    def test_build_clause_istartswith(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'istartswith', 'Django',
            func.lower(Waiter.name).startswith('django')
        )

    def test_build_clause_lt(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'id', 'lt', 1,
            Waiter.id < 1
        )

    def test_build_clause_lte(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'id', 'lte', 1,
            Waiter.id <= 1
        )

    def test_build_clause_range(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'id', 'range', [1, 5],
            Waiter.id.between(1, 5)
        )

    def test_build_clause_startswith(self, alchemy_db):
        self._test_build_clause(
            alchemy_db, 'name', 'startswith', 'Django',
            Waiter.name.startswith('Django')
        )

    def test__get_properties_for_model(self):
        properties = SQLAlchemyFilterBackend._get_properties_for_model(Waiter)

        assert set(properties) == {'restaurant', 'id', 'restaurant_id', 'name'}

    def test__get_column_for_field(self):
        properties = SQLAlchemyFilterBackend._get_properties_for_model(Waiter)
        name = properties['name']
        column = SQLAlchemyFilterBackend._get_column_for_field(name)

        assert column.key == 'name'
        assert isinstance(column.type, String)
        assert column.table is Waiter.__table__

    def test__get_attribute_for_field(self):
        properties = SQLAlchemyFilterBackend._get_properties_for_model(Waiter)
        name = properties['name']
        attr = SQLAlchemyFilterBackend._get_attribute_for_field(name)

        assert attr is Waiter.name

    def test__get_related_model_for_field(self):
        properties = SQLAlchemyFilterBackend._get_properties_for_model(Waiter)
        restaurant = properties['restaurant']
        model = SQLAlchemyFilterBackend._get_related_model_for_field(restaurant)

        assert model is Restaurant
