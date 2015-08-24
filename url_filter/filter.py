# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.core.exceptions import ValidationError
from django.db.models.sql.constants import QUERY_TERMS

from .utils import FilterSpec


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

        return FilterSpec(self.components, lookup, value, is_negated)
