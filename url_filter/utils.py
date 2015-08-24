# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals


class FilterSpec(object):
    __slots__ = ['components', 'lookup', 'value', 'is_negated']

    def __init__(self, components, lookup, value, is_negated=False):
        self.components = components
        self.lookup = lookup
        self.value = value
        self.is_negated = is_negated

    def __repr__(self):
        return '<{} {} {}{} "{}">'.format(
            self.__class__.__name__,
            '.'.join(self.components),
            'NOT ' if self.is_negated else '',
            self.lookup,
            self.value,
        )

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(repr(self))


class ExpandedData(object):
    def __init__(self, key, data):
        if isinstance(data, dict):
            data = {k: self.__class__(key, v) for k, v in data.items()}

        self.key = key
        self.data = data

    def is_key_value(self):
        return len(self.data) == 1 and not isinstance(self.value, dict)

    @property
    def name(self):
        return next(iter(self.data.keys()))

    @property
    def value(self):
        return next(iter(self.data.values()))

    def as_dict(self):
        if isinstance(self.data, dict):
            return {k: v.as_dict() for k, v in self.data.items()}
        return self.data

    def __repr__(self):
        return '<{} {}=>{}>'.format(
            self.__class__.__name__,
            self.key,
            self.as_dict(),
        )
