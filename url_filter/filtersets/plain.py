# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from datetime import date, datetime, time
from decimal import Decimal

import six
from django import forms

from ..exceptions import SkipFilter
from ..filters import Filter
from ..utils import SubClassDict, dictify
from .base import FilterSet
from .django import ModelFilterSetOptions


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


class PlainModelFilterSet(FilterSet):
    filter_options_class = ModelFilterSetOptions

    def get_filters(self):
        filters = super(PlainModelFilterSet, self).get_filters()

        assert self.Meta.model, (
            '{}.Meta.model is missing. Please specify the model '
            'in order to use ModelFilterSet.'
            ''.format(self.__class__.__name__)
        )

        if self.Meta.fields is None:
            self.Meta.fields = self.get_model_field_names()

        model = dictify(self.Meta.model)

        for name in self.Meta.fields:
            if name in self.Meta.exclude:
                continue

            value = model.get(name)
            _filter = None
            primitive = DATA_TYPES_MAPPING.get(type(value))

            try:
                if primitive:
                    _filter = self.build_filter_from_field(value)
                elif isinstance(value, (list, tuple, set)) and value:
                    value = list(value)[0]
                    if not isinstance(value, dict):
                        raise SkipFilter
                    if not self.Meta.allow_related:
                        raise SkipFilter
                    _filter = self.build_filterset_from_related_field(name, value)
                elif isinstance(value, dict):
                    if not self.Meta.allow_related:
                        raise SkipFilter
                    _filter = self.build_filterset_from_related_field(name, value)

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
        return list(dictify(self.Meta.model).keys())

    def build_filter_from_field(self, field):
        return Filter(form_field=DATA_TYPES_MAPPING.get(type(field)))

    def build_filterset_from_related_field(self, name, field):
        meta = type(str('Meta'), (object,), {'model': field})

        filterset = type(
            str('{}FilterSet'.format(name.title())),
            (PlainModelFilterSet,),
            {
                'Meta': meta,
                '__module__': self.__module__,
            }
        )

        return filterset()
