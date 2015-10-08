# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import re

from ..utils import dictify
from .base import BaseFilterBackend


class PlainFilterBackend(BaseFilterBackend):
    name = 'plain'
    enforce_same_models = False
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
        return object

    def filter_by_specs(self, queryset):
        if not self.regular_specs:
            return queryset

        return filter(self.filter_callable, queryset)

    def filter_callable(self, item):
        return all(self.filter_by_spec(item, spec) for spec in self.regular_specs)

    def filter_by_spec(self, item, spec):
        filtered = self._filter_by_spec_and_value(item, spec.components, spec)
        if spec.is_negated:
            return not filtered
        return filtered

    def _filter_by_spec_and_value(self, item, components, spec):
        if not components:
            comparator = getattr(self, '_compare_{}'.format(spec.lookup))
            try:
                return comparator(item, spec)
            except Exception:
                return True

        if isinstance(item, (list, tuple)):
            return any(
                self._filter_by_spec_and_value(i, components, spec)
                for i in item
            )

        if not isinstance(item, dict):
            item = dictify(item)

        return self._filter_by_spec_and_value(
            item.get(components[0], {}),
            components[1:],
            spec,
        )

    def _compare_contains(self, value, spec):
        return spec.value in value

    def _compare_day(self, value, spec):
        return value.day == spec.value

    def _compare_endswith(self, value, spec):
        return value.endswith(spec.value)

    def _compare_exact(self, value, spec):
        return value == spec.value

    def _compare_gt(self, value, spec):
        return value > spec.value

    def _compare_gte(self, value, spec):
        return value >= spec.value

    def _compare_hour(self, value, spec):
        return value.hour == spec.value

    def _compare_icontains(self, value, spec):
        return spec.value.lower() in value.lower()

    def _compare_iendswith(self, value, spec):
        return value.lower().endswith(spec.value.lower())

    def _compare_iexact(self, value, spec):
        return value.lower() == spec.value.lower()

    def _compare_in(self, value, spec):
        return value in spec.value

    def _compare_iregex(self, value, spec):
        return bool(re.match(spec.value, value, re.IGNORECASE))

    def _compare_isnull(self, value, spec):
        if spec.value:
            return value is None
        else:
            return value is not None

    def _compare_istartswith(self, value, spec):
        return value.lower().startswith(spec.value.lower())

    def _compare_lt(self, value, spec):
        return value < spec.value

    def _compare_lte(self, value, spec):
        return value <= spec.value

    def _compare_minute(self, value, spec):
        return value.minute == spec.value

    def _compare_month(self, value, spec):
        return value.month == spec.value

    def _compare_range(self, value, spec):
        return spec.value[0] <= value <= spec.value[1]

    def _compare_regex(self, value, spec):
        return bool(re.match(spec.value, value))

    def _compare_second(self, value, spec):
        return value.second == spec.value

    def _compare_startswith(self, value, spec):
        return value.startswith(spec.value)

    def _compare_week_day(self, value, spec):
        return value.weekday() + 1 == spec.value

    def _compare_year(self, value, spec):
        return value.year == spec.value
