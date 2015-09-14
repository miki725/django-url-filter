# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import abc

import six
from cached_property import cached_property


class BaseFilterBackend(six.with_metaclass(abc.ABCMeta, object)):
    supported_lookups = set()
    enforce_same_models = True

    def __init__(self, queryset, context=None):
        self.queryset = queryset
        self.context = context or {}
        self.specs = []

    @cached_property
    def model(self):
        return self.get_model()

    def bind(self, specs):
        self.specs = specs

    @abc.abstractmethod
    def get_model(self):
        """
        Get the queryset model.

        .. note:: **MUST** be implemented by subclasses
        """

    @abc.abstractmethod
    def filter(self):
        """
        Main method for filtering queryset.

        .. note:: **MUST** be implemented by subclasses
        """
