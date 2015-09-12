# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import inspect
from functools import partial

from django import forms
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
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
    Date,
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
)

from ..backends.sqlalchemy import SQLAlchemyFilterBackend
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
    Integer: forms.IntegerField,
    Boolean: partial(forms.BooleanField, required=False),
    CHAR: _STRING,
    CLOB: _STRING,
    DATE: forms.DateTimeField,
    Date: forms.DateField,
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

        fields = SQLAlchemyFilterBackend._get_properties_for_model(self.Meta.model)

        for name in self.Meta.fields:
            if name in self.Meta.exclude:
                continue

            field = fields[name]

            try:
                if isinstance(field, ColumnProperty):
                    _filter = self.build_filter_from_field(field)
                elif isinstance(field, RelationshipProperty):
                    _filter = self.build_filterset_from_related_field(field)
                else:
                    _filter = None

            except SkipFilter:
                continue

            else:
                if _filter is not None:
                    filters[name] = _filter

        return filters

    def get_model_field_names(self):
        """
        Get a list of all model fields.

        This is used when ``Meta.fields`` is ``None``
        in which case this method returns all model fields.
        """
        return list(SQLAlchemyFilterBackend._get_properties_for_model(self.Meta.model).keys())

    def get_form_field_for_field(self, field):
        """
        Get form field for the given SQLAlchemy model field.
        """
        column = SQLAlchemyFilterBackend._get_column_for_field(field)

        form_field = SQLALCHEMY_FIELD_MAPPING.get(
            column.type.__class__, None,
        )

        if form_field is None:
            raise SkipFilter

        if inspect.isclass(form_field) or isinstance(form_field, partial):
            return form_field()
        else:
            return form_field(field, column)

    def build_filter_from_field(self, field):
        """
        Build ``Filter`` for a standard SQLAlchemy model field.
        """
        column = SQLAlchemyFilterBackend._get_column_for_field(field)

        return Filter(
            form_field=self.get_form_field_for_field(field),
            is_default=column.primary_key,
        )

    def build_filterset_from_related_field(self, field):
        m = SQLAlchemyFilterBackend._get_related_model_for_field(field)
        meta = {
            'model': m,
            'exclude': [field.back_populates]
        }

        meta = type(str('Meta'), (object,), meta)

        filterset = type(
            str('{}FilterSet'.format(m.__name__)),
            (SQLAlchemyModelFilterSet,),
            {
                'Meta': meta,
                '__module__': self.__module__,
            }
        )

        return filterset()
