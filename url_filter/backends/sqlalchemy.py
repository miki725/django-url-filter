# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import itertools

from sqlalchemy import func
from sqlalchemy.orm import class_mapper
from sqlalchemy.sql.expression import not_

from .base import BaseFilterBackend


def lower(value):
    try:
        return value.lower()
    except AttributeError:
        return value


class SQLAlchemyFilterBackend(BaseFilterBackend):
    supported_lookups = {
        'contains',
        'endswith',
        'exact',
        'gt',
        'gte',
        'icontains',
        'iendswith',
        'iexact',
        'in',
        'isnull',
        'istartswith',
        'lt',
        'lte',
        'range',
        'startswith',
    }

    def __init__(self, *args, **kwargs):
        super(SQLAlchemyFilterBackend, self).__init__(*args, **kwargs)

        assert len(self.queryset._entities) == 1, (
            '{} does not support filtering when multiple entities '
            'are being queried (e.g. session.query(Foo, Bar)).'
            ''.format(self.__class__.__name__)
        )

    def get_model(self):
        return self.queryset._primary_entity.entities[0]

    def filter(self):
        if not self.specs:
            return self.queryset

        clauses = [self.build_clause(spec) for spec in self.specs]
        conditions, joins = zip(*clauses)
        joins = list(itertools.chain(*joins))

        qs = self.queryset
        if joins:
            qs = qs.join(*joins)

        return qs.filter(*conditions)

    def build_clause(self, spec):
        to_join = []

        model = self.model
        for component in spec.components:
            _field = getattr(model, component)
            field = self._get_properties_for_model(model)[component]
            try:
                model = self._get_related_model_for_field(field)
            except AttributeError:
                break
            else:
                to_join.append(_field)

        builder = getattr(self, '_build_clause_{}'.format(spec.lookup))
        column = self._get_attribute_for_field(field)
        clause = builder(spec, column)

        if spec.is_negated:
            clause = not_(clause)

        return clause, to_join

    def _build_clause_contains(self, spec, column):
        return column.contains(spec.value)

    def _build_clause_endswith(self, spec, column):
        return column.endswith(spec.value)

    def _build_clause_exact(self, spec, column):
        return column == spec.value

    def _build_clause_gt(self, spec, column):
        return column > spec.value

    def _build_clause_gte(self, spec, column):
        return column >= spec.value

    def _build_clause_icontains(self, spec, column):
        return func.lower(column).contains(lower(spec.value))

    def _build_clause_iendswith(self, spec, column):
        return func.lower(column).endswith(lower(spec.value))

    def _build_clause_iexact(self, spec, column):
        return func.lower(column) == lower(spec.value)

    def _build_clause_in(self, spec, column):
        return column.in_(spec.value)

    def _build_clause_isnull(self, spec, column):
        if spec.value:
            return column == None  # noqa
        else:
            return column != None  # noqa

    def _build_clause_istartswith(self, spec, column):
        return func.lower(column).startswith(lower(spec.value))

    def _build_clause_lt(self, spec, column):
        return column < spec.value

    def _build_clause_lte(self, spec, column):
        return column <= spec.value

    def _build_clause_range(self, spec, column):
        return column.between(*spec.value)

    def _build_clause_startswith(self, spec, column):
        return column.startswith(spec.value)

    @classmethod
    def _get_properties_for_model(cls, model):
        mapper = class_mapper(model)
        return {
            i.key: i
            for i in mapper.iterate_properties
        }

    @classmethod
    def _get_column_for_field(cls, field):
        return field.columns[0]

    @classmethod
    def _get_attribute_for_field(cls, field):
        return field.class_attribute

    @classmethod
    def _get_related_model_for_field(self, field):
        return field._dependency_processor.mapper.class_
