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
from ..filters import BaseFilter
from ..utils import LookupConfig


__all__ = [
    'FilterSet',
    'FilterSetOptions',
    'ModelFilterSetOptions',
    'StrictMode',
]


class StrictMode(enum.Enum):
    """
    Strictness mode enum.

    :``drop`` (default):
        ignores all filter failures. when any occur, :class:`.FilterSet`
        simply then does not filter provided queryset.
    :``fail``:
        when validation fails for any filter within :class:`.FilterSet`,
        all error are compiled and cumulative ``ValidationError`` is raised.
    """
    drop = 'drop'
    fail = 'fail'


LOOKUP_RE = re.compile(
    r'^(?:[^\d\W]\w*)(?:{}?[^\d\W]\w*)*(?:!)?$'
    r''.format(LOOKUP_SEP), re.IGNORECASE
)


class FilterKeyValidator(RegexValidator):
    """
    Custom regex validator for validating the querystring filter
    is of correct syntax::

        name[__<relation>]*[__<lookup_method>][!]
    """
    regex = LOOKUP_RE
    message = (
        'Filter key is of invalid format. '
        'It must be `name[__<relation>]*[__<lookup_method>][!]`.'
    )


filter_key_validator = FilterKeyValidator()


class FilterSetOptions(object):
    """
    Base class for handling options passed to :class:`.FilterSet`
    via ``Meta`` attribute.
    """
    def __init__(self, options=None):
        pass


class FilterSetMeta(type(BaseFilter)):
    """
    Metaclass for creating :class:`.FilterSet` classes.

    Its primary job is to do:

    * collect all declared filters in all bases
      and set them as ``_declared_filters`` on created
      :class:`.FilterSet` class.
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
            filters.update({k: v for k, v in base.items() if isinstance(v, BaseFilter)})

        new_class._declared_filters = filters
        new_class.Meta = new_class.filter_options_class(
            getattr(new_class, 'Meta', None)
        )

        return new_class


class FilterSet(six.with_metaclass(FilterSetMeta, BaseFilter)):
    """
    Main user-facing classes to use filtersets.

    It primarily does:

    * takes queryset to filter
    * takes querystring data which will be used to filter
      given queryset
    * from the querystring, it constructs a list of :class:`.LookupConfig`
    * loops over the created configs and attempts to get
      :class:`.FilterSpec` for each
    * in the process, it delegates the job of constructing spec
      to child filters when any match is found between filter
      defined on the filter and lookup name in the config

    Parameters
    ----------
    data : QueryDict, optional
        ``QueryDict`` of querystring data.
        Only optional when :class:`.FilterSet` is used as a nested filter
        within another :class:`.FilterSet`.
    queryset : iterable, optional
        Can be any iterable as supported by the filter backend.
        Only optional when :class:`.FilterSet` is used as a nested filter
        within another :class:`.FilterSet`.
    context : dict, optional
        Context for filtering. This is passed to filtering backend.
        Usually this would consist of passing ``request`` and ``view``
        object from the Django view.
    strict_mode : str, optional
        Strict mode how :class:`.FilterSet` should behave when any validation
        fails. See :class:`.StrictMode` doc for more information.
        Default is ``drop``.
    """
    filter_backend_class = DjangoFilterBackend
    """
    Class to be used as filter backend. By default
    :class:`.DjangoFilterBackend` is used.
    """
    filter_options_class = FilterSetOptions
    """
    Class to be used to construct ``Meta`` during
    :class:`.FilterSet` class creation time in its metaclass.
    """
    default_strict_mode = StrictMode.drop
    """
    Default strict mode which should be used when one is not
    provided in initialization.
    """

    def __init__(self, data=None, queryset=None, context=None,
                 strict_mode=None,
                 *args, **kwargs):
        super(FilterSet, self).__init__(*args, **kwargs)
        self.data = data
        self.queryset = queryset
        self.context = context or {}
        self.strict_mode = strict_mode or self.default_strict_mode

    def repr(self, prefix=''):
        """
        Custom representation of the filterset


        Parameters
        ----------
        prefix : str
            Prefix with which each line of the representation should
            be prefixed with. This allows to recursively get the
            representation of all descendants with correct indentation
            (children are indented compared to parent)
        """
        header = '{name}({source})'.format(
            name=self.__class__.__name__,
            source='source="{}"'.format(self.source) if self.is_bound else '',
        )
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
        this method is meant to be used as a hook in subclasses
        in order to enhance functionality such as automatically
        adding filters from model fields.
        """
        return deepcopy(self._declared_filters)

    @cached_property
    def filters(self):
        """
        Cached property for accessing filters available in this filteset.
        In addition to getting filters via :meth:`.get_filters`,
        this property binds all filters to the filterset by using
        :meth:`.BaseFilter.bind`.

        See Also
        --------
        get_filters
        :meth:`.BaseFilter.bind`
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
        Validate that :class:`.LookupConfig` key is correct.

        This is the key as provided in the querystring.
        Currently key is validated against a regex expression.

        Useful to filter out invalid filter querystring pairs
        since not whole querystring is not dedicated for filter
        purposes but could contain other information such as
        pagination information. In that case if the key is
        invalid key for filtering, we can simply ignore it
        without wasting time trying to get filter specification
        for it.

        Parameters
        ----------
        key : str
            Key as provided in the querystring
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
        Main method which should be used on root :class:`.FilterSet`
        to filter queryset.

        This method:

        * asserts that filtering is being done on root :class:`.FilterSet`
          and that all necessary data is provided
        * creates :class:`.LookupConfig` from the provided data (querystring)
        * loops over all configs and attempts to get :class:`.FilterSet`
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
        Get list of :class:`.FilterSpec` for the given querystring data.

        This function does:

        * unpacks the querystring data to a list of :class:`.LookupConfig`
        * loops through all configs and uses appropriate children
          filters to generate list of :class:`.FilterSpec`
        * if any validations fails while generating specs,
          all errors are collected and depending on ``strict_mode``
          it re-raises the errors or ignores them.

        Returns
        -------
        list
            List of :class:`.FilterSpec`
        """
        configs = self._generate_lookup_configs()
        specs = []
        errors = defaultdict(list)

        for data in configs:
            try:
                self.validate_key(data.key)
            except ValidationError:
                continue

            try:
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
        Get :class:`.FilterSpec` for the given :class:`.LookupConfig`.

        If the config is non leaf config (it has more nested fields),
        then the appropriate matching child filter is used
        to get the spec.
        If the config however is a leaf config, then ``default_filter``
        is used to get the spec, when available, and if not,
        this filter is skipped.

        Parameters
        ----------
        config : LookupConfig
            Config for which to generate :class:`.FilterSpec`

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
            if self.default_filter and self is not self.root:
                # if name is not found as a filter, there is a possibility
                # it is a lookup made on the default filter of this filterset
                # in which case we try to get that spec directly from the child
                # however that is only allowed on nested filtersets
                # since on root filterset filter must be specified
                return self.default_filter.get_spec(config)
            else:
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


class ModelFilterSetOptions(FilterSetOptions):
    """
    Custom options for :class:`.FilterSet` used for model-generated filtersets.

    Attributes
    ----------
    model : Model
        Model class from which :class:`.FilterSet` will
        extract necessary filters.
    fields : None, list, optional
        Specific model fields for which filters
        should be created for.
        By default it is ``None`` in which case for all
        fields filters will be created for.
    exclude : list, optional
        Specific model fields for which filters
        should **not** be created for.
    allow_related : bool, optional
        Whether related/nested fields should be allowed
        when model fields are automatically determined
        (e.g. when explicit :attr:`.fields` is not provided).
    """
    def __init__(self, options=None):
        super(ModelFilterSetOptions, self).__init__(options)
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', [])
        self.allow_related = getattr(options, 'allow_related', True)


class BaseModelFilterSet(FilterSet):
    """
    Base :class:`.FilterSet` for model-generated filtersets.

    The filterset can be configured via ``Meta`` class attribute,
    very much like how Django's ``ModelForm`` is configured.
    """
    filter_options_class = ModelFilterSetOptions

    def get_filters(self):
        """
        Get all filters defined in this filterset by introspecting
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
            if name in self.Meta.exclude or name in filters:
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
        in which case this method returns all model field names.

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
            State of the model as returned by :meth:`._build_state`.
            Since state is computed outside of the loop which builds
            filters, state can be useful to store information outside
            of the loop so that it can be reused for all filters.
        """

    def _build_filterset(self, name, meta_attrs, base):
        """
        Helper method for building child filtersets.

        Parameters
        ----------
        name : str
            Name of the filterset to build. The returned class
            will use the name as a prefix in the class name.
        meta_attrs : dict
            Attributes to use for the ``Meta``.
        base : type
            Class to use as a base class for the filterset.
        """
        meta = type(str('Meta'), (object,), meta_attrs)

        filterset = type(
            str('{}FilterSet'.format(name)),
            (base,),
            {
                'Meta': meta,
                '__module__': self.__module__,
            }
        )

        return filterset()

    def _build_state(self):
        """
        Hook function to build state to be used while building all the filters.
        Useful to compute common data between all filters such as some
        data about model so that the computation can be avoided while
        building individual filters.
        """
