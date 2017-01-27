# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from datetime import date, datetime, time
from decimal import Decimal

import six
from django import forms

from ..exceptions import SkipFilter
from ..filters import Filter
from ..utils import SubClassDict, dictify
from .base import BaseModelFilterSet


DATA_TYPES_MAPPING = SubClassDict({
    six.string_types: forms.CharField(),
    six.integer_types: forms.IntegerField(),
    bool: forms.BooleanField(required=False),
    float: forms.FloatField(),
    Decimal: forms.DecimalField(),
    datetime: forms.DateTimeField(),
    date: forms.DateField(),
    time: forms.TimeField(),
})


class PlainModelFilterSet(BaseModelFilterSet):
    """
    :class:`.FilterSet` for plain Python objects.

    The filterset can be configured via ``Meta`` class attribute,
    very much like Django's ``ModelForm`` is configured.
    """

    def _build_state(self):
        return dictify(self.Meta.model)

    def _build_filter(self, name, model):
        value = model.get(name)
        primitive = DATA_TYPES_MAPPING.get(type(value))

        if primitive:
            return self._build_filter_from_field(value)

        elif isinstance(value, (list, tuple, set)) and value:
            value = list(value)[0]
            if DATA_TYPES_MAPPING.get(type(value)):
                return self._build_filter_from_field(value)
            if not isinstance(value, dict):
                raise SkipFilter
            if not self.Meta.allow_related:
                raise SkipFilter
            return self._build_filterset_from_related_field(name, value)

        elif isinstance(value, dict):
            if not self.Meta.allow_related:
                raise SkipFilter
            return self._build_filterset_from_related_field(name, value)

    def _get_model_field_names(self):
        return list(dictify(self.Meta.model).keys())

    def _build_filter_from_field(self, field):
        return Filter(form_field=DATA_TYPES_MAPPING.get(type(field)))

    def _build_filterset_from_related_field(self, name, field):
        if not field:
            raise SkipFilter
        return self._build_filterset(
            name.title(),
            {'model': field},
            PlainModelFilterSet,
        )
