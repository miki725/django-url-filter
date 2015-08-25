# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.db.models.constants import LOOKUP_SEP


class DjangoFilterBackend(object):
    def __init__(self, specs, queryset, context=None):
        self.specs = specs
        self.queryset = queryset
        self.context = context or {}

    @property
    def includes(self):
        return filter(
            lambda i: not i.is_negated,
            self.specs
        )

    @property
    def excludes(self):
        return filter(
            lambda i: i.is_negated,
            self.specs
        )

    def prepare_spec(self, spec):
        return '{}{}{}'.format(
            LOOKUP_SEP.join(spec.components),
            LOOKUP_SEP,
            spec.lookup,
        )

    def filter(self):
        include = {self.prepare_spec(i): i.value for i in self.includes}
        exclude = {self.prepare_spec(i): i.value for i in self.excludes}

        qs = self.queryset

        if include:
            qs = qs.filter(**include)
        if exclude:
            qs = qs.exclude(**exclude)

        return qs
