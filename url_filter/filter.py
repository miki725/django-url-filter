# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from functools import partial

from django import forms
from django.core.exceptions import ValidationError
from django.db.models.sql.constants import QUERY_TERMS

from .fields import MultipleValuesField
from .utils import FilterSpec


MANY_LOOKUP_FIELD_OVERWRITES = {
    'in': partial(MultipleValuesField, min_values=2),
    'range': partial(MultipleValuesField, min_values=2, max_values=2),
}

LOOKUP_FIELD_OVERWRITES = {
    'isnull': forms.BooleanField(),
    'second': forms.IntegerField(min_value=0, max_value=59),
    'minute': forms.IntegerField(min_value=0, max_value=59),
    'hour': forms.IntegerField(min_value=0, max_value=23),
    'week_day': forms.IntegerField(min_value=1, max_value=7),
    'day': forms.IntegerField(min_value=1, max_value=31),
    'month': forms.IntegerField(),
    'year': forms.IntegerField(min_value=0, max_value=9999),
}


class Filter(object):
    default_lookup = 'exact'

    def __init__(self, source=None, *args, **kwargs):
        self._source = source
        self.parent = None
        self.name = None
        self.init(*args, **kwargs)

    def init(self, form_field, lookups=None, default_lookup=None):
        self.form_field = form_field
        self.lookups = lookups or list(QUERY_TERMS)
        self.default_lookup = default_lookup or self.default_lookup

    @property
    def source(self):
        return self._source or self.name

    @property
    def components(self):
        if self.parent is None:
            return []
        return self.parent.components + [self.source]

    def bind(self, name, parent):
        self.name = name
        self.parent = parent

    @property
    def root(self):
        if self.parent is None:
            return self
        return self.parent.root

    def get_form_field(self, lookup):
        if lookup in MANY_LOOKUP_FIELD_OVERWRITES:
            return MANY_LOOKUP_FIELD_OVERWRITES[lookup](child=self.form_field)
        elif lookup in LOOKUP_FIELD_OVERWRITES:
            return LOOKUP_FIELD_OVERWRITES[lookup]
        else:
            return self.form_field

    def clean_value(self, value, lookup):
        form_field = self.get_form_field(lookup)
        return form_field.clean(value)

    def get_spec(self, data):
        # lookup was explicitly provided
        if isinstance(data.data, dict):
            if not data.is_key_value():
                raise ValidationError(
                    'Invalid filtering data provided. '
                    'Data is more complex then expected. '
                    'Most likely additional lookup was specified '
                    'after the final lookup (e.g. field__in__equal=value).'
                )

            lookup = data.name
            value = data.value.data

        # use default lookup
        else:
            lookup = self.default_lookup
            value = data.data

        if lookup not in self.lookups:
            raise ValidationError('"{}" lookup is not supported'.format(lookup))

        is_negated = '!' in data.key
        value = self.clean_value(value, lookup)

        return FilterSpec(self.components, lookup, value, is_negated)
