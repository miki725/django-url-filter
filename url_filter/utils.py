# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import inspect


class FilterSpec(object):
    __slots__ = ['components', 'lookup', 'value', 'is_negated']

    def __init__(self, components, lookup, value, is_negated=False):
        self.components = components
        self.lookup = lookup
        self.value = value
        self.is_negated = is_negated

    def __repr__(self):
        return '<{} {} {}{} {}>'.format(
            self.__class__.__name__,
            '.'.join(self.components),
            'NOT ' if self.is_negated else '',
            self.lookup,
            repr(self.value),
        )

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(repr(self))


class ExpandedData(object):
    __slots__ = ['key', 'data']

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


class SubClassDict(dict):
    def get(self, k, d=None):
        """
        If no value is found by using Python's default implementation,
        try to find the value where the key is a base class of the
        provided search class.

        This is useful for finding field overwrites by class
        for custom Django model fields (illustrated below).

        Example
        -------

        ::

            >>> from django import forms
            >>> class ImgField(forms.ImageField):
            ...     pass
            >>> overwrites = SubClassDict({
            ...     forms.CharField: 'foo',
            ...     forms.FileField: 'bar',
            ... })
            >>> print(overwrites.get(forms.CharField))
            foo
            >>> print(overwrites.get(ImgField))
            bar
        """
        value = super(SubClassDict, self).get(k, d)

        # try to match by value
        if value is d and inspect.isclass(k):
            for klass, v in self.items():
                if not inspect.isclass(klass):
                    continue
                if issubclass(k, klass):
                    return v

        return value
