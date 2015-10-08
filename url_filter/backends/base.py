# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import abc

import six
from cached_property import cached_property


class BaseFilterBackend(six.with_metaclass(abc.ABCMeta, object)):
    """
    Base filter backend from which all other backends must subclass.

    Parameters
    ----------
    queryset
        Iterable which this filter backend will eventually filter.
        The type of the iterable depends on the filter backend.
        For example for ``DjangoFilterBackend``, ``QuerySet`` needs
        to be passed.
    context: dict
        Context dictionary. It could contain any information
        which potentially could be useful to filter given
        queryset. That can include, request, view, view kwargs, etc.
        The idea is similar to DRF serializers. By passing the context,
        it allows custom filters to reference all the information
        they need to be able to effectively filter data.
    """
    name = None
    supported_lookups = set()
    enforce_same_models = True

    def __init__(self, queryset, context=None):
        self.queryset = queryset
        self.context = context or {}
        self.specs = []

    @cached_property
    def model(self):
        """
        Property for getting model on which this filter backend operates.

        The main use for this is being able to validate that correct
        filterset is being used to filter some data.
        """
        return self.get_model()

    def bind(self, specs):
        """
        Bind the given specs to the filter backend.

        This allows the filterset to be instantiated first before
        filter specs are constructed and later, specs can be binded.
        """
        self.specs = specs

    @cached_property
    def regular_specs(self):
        """
        Property for getting standard filter specifications
        which can be used directly by the filter backend
        to filter queryset.
        """
        return [i for i in self.specs if not i.is_callable]

    @cached_property
    def callable_specs(self):
        """
        Property for getting custom filter specifications
        which have a filter callable for filtering querysets.
        These specifications cannot be directly used by filter
        backend and have to be called manually to filter data.
        """
        return [i for i in self.specs if i.is_callable]

    @abc.abstractmethod
    def get_model(self):
        """
        Get the queryset model.

        .. note:: **MUST** be implemented by subclasses
        """

    def filter(self):
        """
        Main public method for filtering querysets.
        """
        qs = self.filter_by_specs(self.queryset)
        qs = self.filter_by_callables(qs)
        return qs

    @abc.abstractmethod
    def filter_by_specs(self, queryset):
        """
        Method for filtering queryset by using standard filter specs.

        .. note:: **MUST** be implemented by subclasses
        """

    def filter_by_callables(self, queryset):
        """
        Method for filtering queryset by using custom filter callables
        as given in the ``Filter`` definition.

        This is really meant to accomodate filtering with simple
        filter keys having complex filtering logic behind them.
        """
        if not self.callable_specs:
            return queryset

        for spec in self.callable_specs:
            queryset = spec.filter_callable(
                queryset=queryset,
                spec=spec,
            )

        return queryset
