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
        For example for :class:`.DjangoFilterBackend`, Django's
        ``QuerySet`` needs to be passed.
    context: dict
        Context dictionary. It could contain any information
        which potentially could be useful to filter given
        queryset. That can include, request, view, view kwargs, etc.
        The idea is similar to DRF serializers. By passing the context,
        it allows custom filters to reference all the information
        they need to be able to effectively filter data.
    """

    name = None
    """
    Name of the filter backend.

    This is used by custom callable filters to define callables
    for each supported backend. More at :class:`.CallableFilter`
    """
    supported_lookups = set()
    """
    Set of supported lookups this filter backend supports.

    This is used by leaf :class:`.Filter` to determine whether
    it should construct :class:`.FilterSpec` for a particular
    key-value pair from querystring since it if constructs
    specification but then filter backend will not be able to
    filter it, things will blow up. By explicitly checking
    if filter backend supports particular lookup it can
    short-circuit the logic and avoid errors down the road.
    This is pretty much the only coupling between filters
    and filter backends.
    """
    enforce_same_models = True
    """
    Whether same models should be enforced when trying to use
    this filter backend.

    More can be found in :meth:`BaseFilterBackend.model`
    """

    def __init__(self, queryset, context=None):
        self.queryset = queryset
        self.context = context or {}
        self.specs = []

    @cached_property
    def model(self):
        """
        Property for getting model on which this filter backend operates.

        This is meant to be used by the integrations directly shipped with
        django-url-filter which need to be able to validate that the filterset
        will be able to filter given queryset. They can do that by comparing
        the model they are trying to filter matches the model the filterbackend
        got. This primarily will have misconfigurations such as using
        SQLAlchemy filterset to filter Django's ``QuerySet``.
        """
        return self.get_model()

    def bind(self, specs):
        """
        Bind the given specs to the filter backend.

        This allows the filter backend to be instantiated first before
        filter specs are constructed and later, specs can be binded
        to the backend.

        Parameters
        ----------
        specs : list
            List of :class:`.FilterSpec` to be binded for the filter
            backend for filtering
        """
        self.specs = specs

    @cached_property
    def regular_specs(self):
        """
        Property for getting standard filter specifications
        which can be used directly by the filter backend
        to filter queryset.

        See Also
        --------
        callable_specs
        """
        return [i for i in self.specs if not i.is_callable]

    @cached_property
    def callable_specs(self):
        """
        Property for getting custom filter specifications
        which have a filter callable for filtering querysets.
        These specifications cannot be directly used by filter
        backend and have to be called manually to filter data.

        See Also
        --------
        regular_specs
        """
        return [i for i in self.specs if i.is_callable]

    @abc.abstractmethod
    def get_model(self):
        """
        Get the queryset model.

        .. note:: **MUST** be implemented by subclasses.
            :meth:`.model` property  uses this method to get the model.

        See Also
        --------
        model
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

    @abc.abstractmethod
    def empty(self):
        """
        Method for returning empty queryset when any validations failed.
        """

    def filter_by_callables(self, queryset):
        """
        Method for filtering queryset by using custom filter callables
        as given in the :class:`.Filter` definition.

        This is really meant to accommodate filtering with simple
        filter keys having complex filtering logic behind them.
        More about custom callables can be found at :class:`.CallableFilter`
        """
        if not self.callable_specs:
            return queryset

        for spec in self.callable_specs:
            queryset = spec.filter_callable(queryset=queryset, spec=spec)

        return queryset
