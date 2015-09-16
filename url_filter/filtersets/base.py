# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import abc
import enum
import re
from collections import defaultdict
from copy import deepcopy

import six
from cached_property import cached_property
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models.constants import LOOKUP_SEP
from django.http import QueryDict

from ..backends.django import DjangoFilterBackend
from ..exceptions import SkipFilter
from ..filters import Filter
from ..utils import LookupConfig


__all__ = [
    'BaseModelFilterSet',
    'FilterSet',
    'FilterSetOptions',
    'ModelFilterSetOptions',
    'StrictMode',
]


class StrictMode(enum.Enum):
    """
    Strictness mode enum.

    :``drop`` (default):
        ignores all filter failures. when any occur, ``FilterSet``
        simply then does not filter provided queryset.
    :``fail``:
        when validation fails for any filter within ``FilterSet``,
        all error are compiled and cumulative ``ValidationError`` is raised.
    """
    drop = 'drop'
    fail = 'fail'


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


class FilterSetOptions(object):
    """
    Base class for handling options passed to ``FilterSet``
    via ``Meta`` attribute.
    """
    def __init__(self, options=None):
        pass


class FilterSetMeta(abc.ABCMeta):
    """
    Metaclass for creating ``FilterSet`` classes.

    Its primary job is to do:

    * collect all declared filters in all bases
      and set them as ``_declared_filters`` on created
      ``FilterSet`` class.
    * instantiate ``Meta`` by using ``filter_options_class`` attribute
    """

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
        new_class.Meta = new_class.filter_options_class(
            getattr(new_class, 'Meta', None)
        )

        return new_class


class FilterSet(six.with_metaclass(FilterSetMeta, Filter)):
    """
    Main user-facing classes to use filtersets.

    ``FilterSet`` primarily does:

    * takes queryset to filter
    * takes querystring data which will be used to filter
      given queryset
    * from the querystring, it constructs a list of ``LookupConfig``
    * loops over the created configs and attemps to get
      ``FilterSpec`` for each
    * in the process, if delegates the job of constructing spec
      to child filters when any match is found between filter
      defined on the filter and name in the config

    Parameters
    ----------
    source : str
        Name of the attribute for which which filter applies to
        within the model of the queryset to be filtered
        as given to the ``FilterSet``.
    data : QueryDict, optional
        QueryDict of querystring data.
        Only optional when ``FilterSet`` is used a nested filter
        within another ``FilterSet``.
    queryset : iterable, optional
        Can be any iterable as supported by the filter backend.
        Only optional when ``FilterSet`` is used a nested filter
        within another ``FilterSet``.
    context : dict, optional
        Context for filtering. This is passed to filtering backend.
        Usually this would consist of passing ``request`` and ``view``
        object from the Django view.
    strict_mode : str, optional
        Strict mode how ``FilterSet`` should behave when any validation
        fails. See ``StrictMode`` doc for more information.
        Default is ``drop``.

    Attributes
    ----------
    filter_backend_class
        Class to be used as filter backend. By default
        ``DjangoFilterBackend`` is used.
    filter_options_class
        Class to be used to construct ``Meta`` during
        ``FilterSet`` class creation time in its metalclass.
    """
    filter_backend_class = DjangoFilterBackend
    filter_options_class = FilterSetOptions

    def _init(self, data=None, queryset=None, context=None,
              strict_mode=StrictMode.drop):
        self.data = data
        self.queryset = queryset
        self.context = context or {}
        self.strict_mode = strict_mode

    def repr(self, prefix=''):
        header = '{name}()'.format(name=self.__class__.__name__)
        lines = [header] + [
            '{prefix}{key} = {value}'.format(
                prefix=prefix + '  ',
                key=k,
                value=v.repr(prefix=prefix + '  '),
            )
            for k, v in sorted(self.filters.items())
        ]
        return '\n'.join(lines)

    def get_filters(self):
        """
        Get all filters defined in this filterset.
        By default only declared filters are returned however
        this methoc can be used a hook to customize that.
        """
        return deepcopy(self._declared_filters)

    @cached_property
    def filters(self):
        """
        Cached property for accessing filters available in this filteset.
        In addition to getting filters via ``get_filters``,
        this property binds all filters to the filtset by using ``bind``.

        See Also
        --------
        get_filters
        bind
        """
        filters = self.get_filters()

        for name, _filter in filters.items():
            _filter.bind(name, self)

        return filters

    @cached_property
    def default_filter(self):
        """
        Cached property for looking up default filter.
        Default filter is a filter which is defined with ``is_default=True``.
        Useful when lookup config references nested filter without
        specifying which field to filter. In that case default filter
        will be used.
        """
        return next(iter(filter(
            lambda i: getattr(i, 'is_default', False),
            self.filters.values()
        )), None)

    def validate_key(self, key):
        """
        Validate that ``LookupConfig`` key is correct.

        This is the key as provided in the querystring.
        Currently key is validated against a regex expression.
        """
        filter_key_validator(key)

    def get_filter_backend(self):
        """
        Get instantiated filter backend class.

        This backend is then used to actually filter queryset.
        """
        return self.filter_backend_class(
            queryset=self.queryset,
            context=self.context,
        )

    @cached_property
    def filter_backend(self):
        """
        Property for getting instantiated filter backend.

        Primarily useful when accessing filter_backend outside
        of the filterset such as leaf filters or integration
        layers since backend has useful information for both of
        those examples.
        """
        assert self.data is not None, (
            'Filter backend can only be used when data is provided '
            'to filterset.'
        )
        return self.get_filter_backend()

    def filter(self):
        """
        Main method which should be used on root ``FilterSet``
        to filter queryset.

        This method:

        * asserts that filtering is being done on root ``FilterSet``
          and that all necessary data is provided
        * creates ``LookupConfig``s from the provided data (querystring)
        * loops over all configs and attemps to get ``FilterSpec``
          for all of them
        * instantiates filter backend
        * uses the created filter specs to filter queryset by using specs

        Returns
        -------
        querystring
            Filtered queryset
        """
        assert self.root is self, (
            '``filter`` can only be called on root ``FilterSet``.'
        )
        assert self.queryset is not None, (
            '``queryset`` was not passed for filtering.'
        )
        assert isinstance(self.data, QueryDict), (
            '``data`` should be an instance of QueryDict.'
        )

        specs = self.get_specs()
        self.filter_backend.bind(specs)

        return self.filter_backend.filter()

    def get_specs(self):
        """
        Get ``FilterSpecs`` for the given querystring data.

        This function does:

        * unpacks the querystring data to ``LookupConfig``s
        * loops throught all configs and uses appropriate children
          filters to generate ``FilterSpec``s
        * if any validations fails while generating specs,
          all errors are collected and depending on ``strict_mode``
          it reraises the errors or ignores them.

        Returns
        -------
        list
            List of ``FilterSpec``s
        """
        configs = self._generate_lookup_configs()
        specs = []
        errors = defaultdict(list)

        for data in configs:
            try:
                self.validate_key(data.key)
                specs.append(self.get_spec(data))
            except SkipFilter:
                pass
            except ValidationError as e:
                errors[data.key].extend(
                    getattr(e, 'error_list', [getattr(e, 'message', '')])
                )

        if errors and self.strict_mode == StrictMode.fail:
            raise ValidationError(dict(errors))

        return specs

    def get_spec(self, config):
        """
        Get ``FilterSpec`` for the given ``LookupConfig``.

        If the config is non leaf config (it has more nested fields),
        then the appropriate matching child filter is used
        to get the spec.
        If the config however is a leaf config, then ``default_filter``
        is used to get the spec, when available, and if not,
        this filter is skipped.

        Parameters
        ----------
        config : LookupConfig
            Config for which to generate ``FilterSpec``

        Returns
        -------
        FilterSpec
            Individual filter spec
        """
        if isinstance(config.data, dict):
            name, value = config.name, config.value
        else:
            if self.default_filter is None:
                raise SkipFilter
            name = self.default_filter.source
            value = LookupConfig(config.key, config.data)

        if name not in self.filters:
            raise SkipFilter

        return self.filters[name].get_spec(value)

    def _generate_lookup_configs(self):
        """
        Generate ``LookupConfig``s for all data in querystring data.
        """
        for key, values in self.data.lists():
            for value in values:
                yield LookupConfig(key, six.moves.reduce(
                    lambda a, b: {b: a},
                    (key.replace('!', '').split(LOOKUP_SEP) + [value])[::-1]
                ))


class ModelFilterSetOptions(object):
    """
    Custom options for ``FilterSet``s used for model-generated filtersets.

    Attributes
    ----------
    model : Model
        Model class from which ``FilterSet`` will
        extract necessary filters.
    fields : None, list, optional
        Specific model fields for which filters
        should be created for.
        By default it is ``None`` in which case for all
        fields filters will be created for.
    exclude : list, optional
        Specific model fields for which filters
        should not be created for.
    allow_related : bool, optional
        Whether related/nested fields should be allowed
        when model fields are automatically determined
        (e.g. when explicit ``fields`` is not provided).
    """
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', [])
        self.allow_related = getattr(options, 'allow_related', True)


class BaseModelFilterSet(FilterSet):
    """
    Base ``FilterSet`` for model-generated filtersets.

    The filterset can be configured via ``Meta`` class attribute,
    very much like how Django's ``ModelForm`` is configured.
    """
    filter_options_class = ModelFilterSetOptions

    def get_filters(self):
        """
        Get all filters defined in this filterset by introspecing
        the given model in ``Meta.model``.
        """
        filters = super(BaseModelFilterSet, self).get_filters()

        assert self.Meta.model, (
            '{name}.Meta.model is missing. Please specify the model '
            'in order to use {name}.'
            ''.format(name=self.__class__.__name__)
        )

        if self.Meta.fields is None:
            self.Meta.fields = self._get_model_field_names()

        state = self._build_state()

        for name in self.Meta.fields:
            if name in self.Meta.exclude:
                continue

            try:
                _filter = self._build_filter(name, state)

            except SkipFilter:
                continue

            else:
                if _filter is not None:
                    filters[name] = _filter

        return filters

    @abc.abstractmethod
    def _get_model_field_names(self):
        """
        Get a list of all model fields.

        This is used when ``Meta.fields`` is ``None``
        in which case this method returns all model fields.

        .. note::
            This method is an abstract method and must be implemented
            in subclasses.
        """

    @abc.abstractmethod
    def _build_filter(self, name, state):
        """
        Build a filter for the field within the model by its name.

        .. note::
            This method is an abstract method and must be implemented
            in subclasses.

        Parameters
        ----------
        name : str
            Name of the field for which to build the filter within the ``Meta.model``
        state
            State of the model as returned by ``build_state``.
            Since state is computed outside of the loop which builds
            filters, state can be useful to store information outside
            of the loop so that it can be reused for all filters.
        """

    def _build_state(self):
        """
        Hook function to build state to be used while building all the filters.
        Useful to compute common data between all filters such as some
        data about the data so that the computation can be avoided while
        building inidividual filters.
        """
