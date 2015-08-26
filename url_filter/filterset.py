# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import re
from collections import defaultdict
from copy import deepcopy

import six
from cached_property import cached_property
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models.constants import LOOKUP_SEP
from django.http import QueryDict

from .backends.django import DjangoFilterBackend
from .exceptions import SkipField
from .filter import Filter
from .utils import ExpandedData


class StrictMode(object):
    fail = 'fail'
    drop = 'drop'


LOOKUP_RE = re.compile(
    r'^(?:[^\d\W]\w*)(?:{}?[^\d\W]\w*)*(?:\!)?$'
    r''.format(LOOKUP_SEP), re.IGNORECASE
)


class FilterKeyValidator(RegexValidator):
    regex = LOOKUP_RE
    message = (
        'Filter key is of invalid format. '
        'It must be `name[__<relation>]*[__<method>][!]`.'
    )

filter_key_validator = FilterKeyValidator()


class FilterSetMeta(type):
    def __new__(cls, name, bases, attrs):
        try:
            parents = [b for b in bases if issubclass(b, FilterSet)]
        except NameError:
            parents = False

        new_class = super(FilterSetMeta, cls).__new__(cls, name, bases, attrs)

        # creating FilterSet itself
        if not parents:
            return new_class

        filters = {}
        for base in [vars(base) for base in bases] + [attrs]:
            filters.update({k: v for k, v in base.items() if isinstance(v, Filter)})

        new_class._declared_filters = filters

        return new_class


class FilterSetBase(Filter):
    filter_backend_class = DjangoFilterBackend

    def __init__(self, *args, **kwargs):
        super(FilterSetBase, self).__init__(*args, **kwargs)

    def init(self, data=None, queryset=None, context=None,
             strict_mode=StrictMode.drop):
        self.data = data
        self.queryset = queryset
        self.context = context or {}
        self.strict_mode = strict_mode

    def get_filters(self):
        return deepcopy(self._declared_filters)

    @cached_property
    def filters(self):
        filters = self.get_filters()

        for name, _filter in filters.items():
            _filter.bind(name, self)

        return filters

    @cached_property
    def default_filter(self):
        return next(iter(filter(
            lambda i: getattr(i, 'is_default', False),
            self.filters.values()
        )), None)

    def validate_key(self, key):
        filter_key_validator(key)

    def get_filter_backend(self):
        return self.filter_backend_class(
            queryset=self.queryset,
            context=self.context,
        )

    def filter(self):
        assert self.queryset is not None, (
            'queryset was not passed for filtering.'
        )
        assert isinstance(self.data, QueryDict), (
            'data should be an instance of QueryDict'
        )

        self.filter_backend = self.get_filter_backend()
        specs = self.get_specs()
        self.filter_backend.bind(specs)

        return self.filter_backend.filter()

    def get_specs(self):
        expanded_data = self._expand_data()
        specs = []
        errors = defaultdict(list)

        for data in expanded_data:
            try:
                self.validate_key(data.key)
                specs.append(self.get_spec(data))
            except SkipField:
                pass
            except ValidationError as e:
                if hasattr(e, 'error_list'):
                    errors[data.key].extend(e.error_list)
                elif hasattr(e, 'message'):
                    errors[data.key].append(e.message)
                else:
                    errors[data.key].append(six.text_type(e))

        if errors and self.strict_mode == StrictMode.fail:
            raise ValidationError(dict(errors))

        return specs

    def get_spec(self, data):
        if isinstance(data.data, dict):
            name, value = data.name, data.value
        else:
            if self.default_filter is None:
                raise SkipField
            name = self.default_filter.source
            value = ExpandedData(data.key, data.data)

        if name not in self.filters:
            raise SkipField

        return self.filters[name].get_spec(value)

    def _expand_data(self):
        for key, values in self.data.lists():
            for value in values:
                yield ExpandedData(key, six.moves.reduce(
                    lambda a, b: {b: a},
                    (key.replace('!', '').split(LOOKUP_SEP) + [value])[::-1]
                ))


class FilterSet(six.with_metaclass(FilterSetMeta, FilterSetBase)):
    pass
