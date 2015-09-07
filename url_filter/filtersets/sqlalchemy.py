# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import inspect

from django import forms
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.types import (
    BIGINT,
    CHAR,
    CLOB,
    DATE,
    DECIMAL,
    INTEGER,
    SMALLINT,
    TIMESTAMP,
    VARCHAR,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    Numeric,
    String,
)

from ..exceptions import SkipFilter
from ..filters import Filter
from ..utils import SubClassDict
from .base import FilterSet
from .django import ModelFilterSetOptions


__all__ = ['SQLAlchemyModelFilterSet']


_STRING = lambda field, column: forms.CharField(max_length=column.type.length)

SQLALCHEMY_FIELD_MAPPING = SubClassDict({
    BIGINT: forms.IntegerField,
    BigInteger: forms.IntegerField,
    Boolean: forms.BooleanField,
    CHAR: _STRING,
    CLOB: _STRING,
    DATE: forms.DateTimeField,
    DateTime: forms.DateTimeField,
    DECIMAL: forms.DecimalField,
    Float: forms.FloatField,
    INTEGER: forms.IntegerField,
    Numeric: forms.IntegerField,
    SMALLINT: forms.IntegerField,
    String: _STRING,
    TIMESTAMP: forms.DateTimeField,
    VARCHAR: _STRING,
})


class SQLAlchemyModelFilterSet(FilterSet):
    """
    ``FilterSet`` for SQLAlchemy models.

    The filterset can be configured via ``Meta`` class attribute,
    very much like Django's ``ModelForm`` is configured.
    """
    filter_options_class = ModelFilterSetOptions

    def get_filters(self):
        """
        Get all filters defined in this filterset including
        filters corresponding to Django model fields.
        """
        filters = super(SQLAlchemyModelFilterSet, self).get_filters()

        assert self.Meta.model, (
            '{}.Meta.model is missing. Please specify the model '
            'in order to use ModelFilterSet.'
            ''.format(self.__class__.__name__)
        )

        if self.Meta.fields is None:
            self.Meta.fields = self.get_model_field_names()

        fields = self._get_properties_for_model()

        for name in self.Meta.fields:
            if name in self.Meta.exclude:
                continue

            field = fields[name]

            try:
                if isinstance(field, ColumnProperty):
                    _filter = self.build_filter_from_field(field)
                else:
                    _filter = None

            except SkipFilter:
                continue

            else:
                if _filter is not None:
                    filters[name] = _filter

        return filters

    def _get_properties_for_model(self):
        mapper = class_mapper(self.Meta.model)
        return {
            i.key: i
            for i in mapper.iterate_properties
        }

    def _get_column_for_field(self, field):
        return field.columns[0]

    def get_model_field_names(self):
        """
        Get a list of all model fields.

        This is used when ``Meta.fields`` is ``None``
        in which case this method returns all model fields.
        """
        return list(self._get_properties_for_model().keys())

    def get_form_field_for_field(self, field):
        """
        Get form field for the given SQLAlchemy model field.
        """
        column = self._get_column_for_field(field)

        form_field = SQLALCHEMY_FIELD_MAPPING.get(
            column.type.__class__, None,
        )

        if form_field is None:
            raise SkipFilter

        if inspect.isclass(form_field):
            return form_field()
        else:
            return form_field(field, column)

    def build_filter_from_field(self, field):
        """
        Build ``Filter`` for a standard SQLAlchemy model field.
        """
        column = self._get_column_for_field(field)

        return Filter(
            form_field=self.get_form_field_for_field(field),
            is_default=column.primary_key,
        )
