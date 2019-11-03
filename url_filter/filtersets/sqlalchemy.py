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
from .base import BaseModelFilterSet


__all__ = ["SQLAlchemyModelFilterSet"]


def _string(field, column):
    return forms.CharField(max_length=column.type.length)


SQLALCHEMY_FIELD_MAPPING = SubClassDict(
    {
        BIGINT: forms.IntegerField,
        BigInteger: forms.IntegerField,
        Integer: forms.IntegerField,
        Boolean: partial(forms.BooleanField, required=False),
        CHAR: _string,
        CLOB: _string,
        DATE: forms.DateTimeField,
        Date: forms.DateField,
        DateTime: forms.DateTimeField,
        DECIMAL: forms.DecimalField,
        Float: forms.FloatField,
        INTEGER: forms.IntegerField,
        Numeric: forms.IntegerField,
        SMALLINT: forms.IntegerField,
        String: _string,
        TIMESTAMP: forms.DateTimeField,
        VARCHAR: _string,
    }
)


class SQLAlchemyModelFilterSet(BaseModelFilterSet):
    """
    :class:`.FilterSet` for SQLAlchemy models.

    The filterset can be configured via ``Meta`` class attribute,
    very much like Django's ``ModelForm`` is configured.
    """

    filter_backend_class = SQLAlchemyFilterBackend

    def _build_filter(self, name, fields):
        field = fields[self._get_filter_extra_kwargs(name).get("source", name)]

        if isinstance(field, ColumnProperty):
            return self._build_filter_from_field(name, field)

        elif isinstance(field, RelationshipProperty):
            if not self.Meta.allow_related:
                raise SkipFilter
            return self._build_filterset_from_related_field(name, field)

    def _build_state(self):
        """
        Build state of all column properties for the SQLAlchemy model
        which normalizes to a dict where keys are field names and values
        are column property instances.
        This state is computed before main loop which builds all filters
        for all fields. As a result all helper builder methods
        can use this state to get column property instances for necessary
        fields by simply doing a dictionary lookup instead of requiring
        search operations to find appropriate properties.
        """
        return SQLAlchemyFilterBackend._get_properties_for_model(self.Meta.model)

    def _get_model_field_names(self):
        """
        Get a list of all model fields.

        This is used when ``Meta.fields`` is ``None``
        in which case this method returns all model fields.
        """
        return list(
            SQLAlchemyFilterBackend._get_properties_for_model(self.Meta.model).keys()
        )

    def _get_form_field_for_field(self, field):
        """
        Get form field for the given SQLAlchemy model field.
        """
        column = SQLAlchemyFilterBackend._get_column_for_field(field)

        form_field = SQLALCHEMY_FIELD_MAPPING.get(column.type.__class__, None)

        if form_field is None:
            raise SkipFilter

        if inspect.isclass(form_field) or isinstance(form_field, partial):
            return form_field()
        else:
            return form_field(field, column)

    def _build_filter_from_field(self, name, field):
        """
        Build :class:`.Filter` for a standard SQLAlchemy model field.
        """
        column = SQLAlchemyFilterBackend._get_column_for_field(field)

        return Filter(
            form_field=self._get_form_field_for_field(field),
            is_default=column.primary_key,
            **self._get_filter_extra_kwargs(name)
        )

    def _build_filterset_from_related_field(self, name, field):
        """
        Build :class:`.FilterSet` for a relation SQLAlchemy model field.
        """
        m = SQLAlchemyFilterBackend._get_related_model_for_field(field)

        return self._build_filterset(
            m.__name__,
            name,
            {"model": m, "exclude": [field.back_populates]},
            SQLAlchemyModelFilterSet,
        )
