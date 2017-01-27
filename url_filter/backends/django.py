# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.db.models.constants import LOOKUP_SEP

from .base import BaseFilterBackend


class DjangoFilterBackend(BaseFilterBackend):
    """
    Filter backend for filtering Django querysets.

    .. warning::
        The filter backend can **ONLY** filter Django's ``QuerySet``.
        Passing any other datatype for filtering will kill happy bunnies
        under rainbow.
    """
    name = 'django'
    supported_lookups = {
        'contains',
        'day',
        'endswith',
        'exact',
        'gt',
        'gte',
        'hour',
        'icontains',
        'iendswith',
        'iexact',
        'in',
        'iregex',
        'isnull',
        'istartswith',
        'lt',
        'lte',
        'minute',
        'month',
        'range',
        'regex',
        'second',
        'startswith',
        'week_day',
        'year',
    }

    def get_model(self):
        """
        Get the model from the given queryset
        """
        return self.queryset.model

    @property
    def includes(self):
        """
        Property which gets list of non-negated filters

        By combining all non-negated filters we can optimize filtering by
        calling ``QuerySet.filter`` once rather then calling it for each
        filter specification.
        """
        return filter(
            lambda i: not i.is_negated,
            self.regular_specs
        )

    @property
    def excludes(self):
        """
        Property which gets list of negated filters

        By combining all negated filters we can optimize filtering by
        calling ``QuerySet.exclude`` once rather then calling it for each
        filter specification.
        """
        return filter(
            lambda i: i.is_negated,
            self.regular_specs
        )

    def _prepare_spec(self, spec):
        return '{}{}{}'.format(
            LOOKUP_SEP.join(spec.components),
            LOOKUP_SEP,
            spec.lookup,
        )

    def filter_by_specs(self, queryset):
        """
        Filter queryset by applying all filter specifications

        The filtering is done by calling ``QuerySet.filter`` and
        ``QuerySet.exclude`` as appropriate.
        """
        include = {self._prepare_spec(i): i.value for i in self.includes}
        exclude = {self._prepare_spec(i): i.value for i in self.excludes}

        if include:
            queryset = queryset.filter(**include)
        if exclude:
            queryset = queryset.exclude(**exclude)

        return queryset.distinct()
