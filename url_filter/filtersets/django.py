# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import operator

from django import forms
from django.db import models
from django.db.models.fields.related import ForeignObjectRel, RelatedField

from ..exceptions import SkipField
from ..filter import Filter
from ..utils import SubClassDict
from .base import FilterSet


__all__ = ['ModelFilterSet']


MODEL_FIELD_OVERWRITES = SubClassDict({
    models.AutoField: forms.IntegerField(min_value=0),
    models.FileField: lambda m, f: forms.CharField(max_length=m.max_length),
})


class ModelFilterSetOptions(object):
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', [])


class ModelFilterSet(FilterSet):
    filter_options_class = ModelFilterSetOptions

    def get_filters(self):
        filters = super(ModelFilterSet, self).get_filters()

        assert self.Meta.model, (
            '{}.Meta.model is missing. Please specify the model '
            'in order to use ModelFilterSet.'
            ''.format(self.__class__.__name__)
        )

        if self.Meta.fields is None:
            self.Meta.fields = self.get_model_field_names()

        for name in self.Meta.fields:
            if name in self.Meta.exclude:
                continue

            field = self.Meta.model._meta.get_field(name)

            try:
                if isinstance(field, RelatedField):
                    _filter = self.build_filterset_from_field(field)
                elif isinstance(field, ForeignObjectRel):
                    continue
                elif isinstance(field, models.Field):
                    _filter = self.build_filter_from_field(field)
                else:
                    continue

            except SkipField:
                continue

            else:
                if _filter is not None:
                    filters[name] = _filter

        return filters

    def get_model_field_names(self):
        return list(map(
            operator.attrgetter('name'),
            self.Meta.model._meta.get_fields()
        ))

    def get_form_field_for_field(self, field):
        overwrite = MODEL_FIELD_OVERWRITES.get(field.__class__)
        if overwrite is not None:
            if callable(overwrite):
                return overwrite(field)
            else:
                return overwrite

        field = field.formfield()

        if field is None:
            raise SkipField

        return field

    def build_filter_from_field(self, field):
        return Filter(
            form_field=self.get_form_field_for_field(field),
        )

    def build_filterset_from_field(self, field):
        m = field.related_model

        class Meta(object):
            model = m

        filterset = type(
            str('{}FilterSet'.format(m.__name__)),
            (ModelFilterSet,),
            {
                'Meta': Meta,
                '__module__': self.__module__,
            }
        )

        return filterset()
