# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import abc

import six
from cached_property import cached_property


class BaseFilterBackend(six.with_metaclass(abc.ABCMeta, object)):
    supported_lookups = set()

    def __init__(self, queryset, context=None):
        self.queryset = queryset
        self.context = context or {}

    @cached_property
    def model(self):
        return self.get_model()

    def bind(self, specs):
        self.specs = specs

    @abc.abstractmethod
    def get_model(self):
        pass

    @abc.abstractmethod
    def filter(self):
        pass
