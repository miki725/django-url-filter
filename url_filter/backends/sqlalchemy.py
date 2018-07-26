# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import itertools

from sqlalchemy import false, func
from sqlalchemy.orm import class_mapper
from sqlalchemy.sql.expression import not_

from .base import BaseFilterBackend


__all__ = ['SQLAlchemyFilterBackend']


def lower(value):
    try:
        return value.lower()
    except AttributeError:
        return value


class SQLAlchemyFilterBackend(BaseFilterBackend):
    """
    Filter backend for filtering SQLAlchemy query objects.

    .. warning::
        The filter backend can **ONLY** filter SQLAlchemy's query objects.
        Passing any other datatype for filtering will kill happy bunnies
        under rainbow.

    .. warning::
        The filter backend can **ONLY** filter query objects which query a single
        entity (e.g. query a single model or model column).
        If query object queries multiple entities, ``AssertionError``
        will be raised.
    """
    name = 'sqlalchemy'
    supported_lookups = {
        'contains',
        'endswith',
        'exact',
        'gt',
        'gte',
        'icontains',
        'iendswith',
        'iexact',
        'iin',
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

    def empty(self):
        """
        Get empty queryset
        """
        return self.queryset.filter(false())

    def get_model(self):
        """
        Get the model from the given queryset
        """
        return self.queryset._only_entity_zero().mapper.class_

    def filter_by_specs(self, queryset):
        """
        Filter SQLAlchemy query object by applying all filter specifications

        The filtering is done by calling ``filter`` with all appropriate
        filter clauses. Additionally if any filter specifications filter
        by related models, those models are joined as necessary.
        """
        if not self.regular_specs:
            return queryset

        clauses = [self.build_clause(spec) for spec in self.regular_specs]
        conditions, joins = zip(*clauses)
        joins = list(itertools.chain(*joins))

        if joins:
            queryset = queryset.join(*joins)

        return queryset.filter(*conditions)

    def build_clause(self, spec):
        """
        Construct SQLAlchemy binary expression filter clause from the
        given filter specification.

        Parameters
        ----------
        spec : FilterSpec
            Filter specification for which to construct filter clause

        Returns
        -------
        tuple
            Tuple of filter binary expression clause and and a list of
            model attributes/descriptors which should be joined when
            doing filtering. If these attributes are not joined,
            SQLAlchemy will not join appropriate tables hence
            wont be able to correctly filter data.
        """
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

    def _build_clause_iin(self, spec, column):
        return func.lower(column).in_(lower(i) for i in spec.value)

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
        """
        Get column properties dict for the given model where
        keys are field names and values are column properties
        (e.g. ``ColumnProperty``) or related classes.
        """
        mapper = class_mapper(model)
        return {
            i.key: i
            for i in mapper.iterate_properties
        }

    @classmethod
    def _get_column_for_field(cls, field):
        """
        Get a ``Column`` instance from the model property instance
        (e.g. ``ColumnProperty`` class or related)
        """
        return field.columns[0]

    @classmethod
    def _get_attribute_for_field(cls, field):
        """
        Get the model class attribute/descriptor from property instance
        (e.g. ``ColumnProperty`` class or related)
        """
        return field.class_attribute

    @classmethod
    def _get_related_model_for_field(cls, field):
        """
        Get related model to which field has relationship to
        from property instance (e.g. ``ColumnProperty`` class or related)
        """
        return field._dependency_processor.mapper.class_
