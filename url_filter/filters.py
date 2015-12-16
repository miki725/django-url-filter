# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import abc
import re
from functools import partial, wraps

import six
from cached_property import cached_property
from django import forms
from django.core.exceptions import ValidationError

from .fields import MultipleValuesField
from .utils import FilterSpec


MANY_LOOKUP_FIELD_OVERWRITES = {
    'in': partial(MultipleValuesField, min_values=1),
    'range': partial(MultipleValuesField, min_values=2, max_values=2),
}

LOOKUP_FIELD_OVERWRITES = {
    'isnull': forms.BooleanField(required=False),
    'second': forms.IntegerField(min_value=0, max_value=59),
    'minute': forms.IntegerField(min_value=0, max_value=59),
    'hour': forms.IntegerField(min_value=0, max_value=23),
    'week_day': forms.IntegerField(min_value=1, max_value=7),
    'day': forms.IntegerField(min_value=1, max_value=31),
    'month': forms.IntegerField(),
    'year': forms.IntegerField(min_value=0, max_value=9999),
}

LOOKUP_CALLABLE_FROM_METHOD_REGEX = re.compile(
    r'^filter_(?P<filter>[\w\d]+)_for_(?P<backend>[\w\d]+)$'
)


class BaseFilter(six.with_metaclass(abc.ABCMeta, object)):
    """
    Base class to be used for defining both filters and filtersets.

    This class implements the bare-minimum functions which are used across
    both filters and filtersets however all other functionality must be
    implemented in subclasses. Additionally by using a single base class,
    both filters and filtersets inherit from the same base class hence
    instance checks can be easily done by filteset's metaclass in order
    to find all declared filters defined in it.

    Parameters
    ----------
    source : str
        Name of the attribute for which which filter applies to
        within the model of the queryset to be filtered
        as given to the :class:`.FilterSet`.

    Attributes
    ----------
    parent : :class:`.FilterSet`
        Parent :class:`.FilterSet` to which this filter is bound to
    name : str
        Name of the field as it is defined in parent :class:`.FilterSet`
    is_bound : bool
        If this filter has been bound to a parent yet
    """

    def __init__(self, source=None, *args, **kwargs):
        self._source = source
        self.parent = None
        self.name = None
        self.is_bound = False

    def __repr__(self):
        data = self.repr()
        data = data if six.PY3 else data.encode('utf-8')
        return data

    @abc.abstractmethod
    def repr(self, prefix=''):
        """
        Get the representation of the filter or its subclasses.

        Subclasses **must** overwrite this method.

        .. note::
            This class should return unicode text data

        Parameters
        ----------
        prefix : str
            All nested filtersets provide useful representation of the complete
            filterset including all descendants however in that case descendants
            need to be indented in order for the representation to get structure.
            This parameter is used to do just that. It specifies the prefix
            the representation must use before returning any of its representations.
        """

    @property
    def source(self):
        """
        Source field/attribute in queryset model to be used for filtering.

        This property is helpful when ``source`` parameter is not provided
        when instantiating :class:`.BaseFilter` or its subclasses since it will
        use the filter name as it is defined in the :class:`.FilterSet`.
        For example::

            >>> from .filtersets import FilterSet
            >>> class MyFilterSet(FilterSet):
            ...     foo = Filter(form_field=forms.CharField())
            ...     bar = Filter(source='stuff', form_field=forms.CharField())
            >>> fs = MyFilterSet()
            >>> print(fs.filters['foo'].source)
            foo
            >>> print(fs.filters['bar'].source)
            stuff
        """
        return self._source or self.name

    @property
    def components(self):
        """
        List of all components (source names) of all parent filtersets.
        """
        if self.parent is None:
            return []
        return self.parent.components + [self.source]

    def bind(self, name, parent):
        """
        Bind the filter to the filterset.

        This method should be used by the parent :class:`.FilterSet`
        since it allows to specify the parent and name of each
        filter within the filterset.
        """
        self.name = name
        self.parent = parent
        self.is_bound = True

    @property
    def root(self):
        """
        This gets the root filterset.
        """
        if self.parent is None:
            return self
        return self.parent.root


class Filter(BaseFilter):
    """
    Class which job is to convert leaf :class:`.LookupConfig` to
    :class:`.FilterSpec`

    Each filter by itself is meant to be used a "filter" (field) in the
    :class:`.FilterSet`.

    Examples
    --------

    ::

        >>> from .filtersets import FilterSet
        >>> class MyFilterSet(FilterSet):
        ...     foo = Filter(forms.CharField())
        ...     bar = Filter(forms.IntegerField())

    Parameters
    ----------
    form_field : Field
        Instance of Django's ``forms.Field`` which will be used
        to clean the filter value as provided in the queryset.
        For example if field is ``IntegerField``, this filter
        will make sure to convert the filtering value to integer
        before creating a :class:`.FilterSpec`.
    lookups : list, optional
        List of strings of allowed lookups for this filter.
        By default all supported lookups are allowed.
    default_lookup : str, optional
        If the lookup is not provided in the querystring lookup key,
        this lookup will be used. By default ``exact`` lookup is used.
        For example the default lookup is used when querystring key is
        ``user__profile__email`` which is missing the lookup so ``exact``
        will be used.
    is_default : bool, optional
        Boolean specifying if this filter should be used as a default
        filter in the parent :class:`.FilterSet`.
        By default it is ``False``.
        Primarily this is used when querystring lookup key
        refers to a nested :class:`.FilterSet` however it does not specify
        which filter to use. For example lookup key ``user__profile``
        intends to filter something in the user's profile however
        it does not specify by which field to filter on.
        In that case the default filter within profile :class:`.FilterSet`
        will be used. At most, one default filter should be provided
        in the :class:`.FilterSet`.
    no_lookup : bool, optional
        When ``True``, this filter does not allow to explicitly specify
        lookups in the URL. For example ``id__gt`` will not be allowed.
        This is useful when a given filter should only support a single
        lookup and that lookup name should not be exposed in the URL.
        This is of particular use when defining custom callable filters.
        By default it is ``False``.

    Attributes
    ----------
    form_field : Field
        Django form field which is provided in initialization which
        should be used to validate data as provided in the querystring
    default_lookup : str
        Default lookup to be used as provided in initialization
    is_default : bool
        If this filter should be a default filter as provided in initialization
    no_lookup : str
        If this filter should not support explicit lookups as provided in initialization
    """

    def __init__(self, form_field,
                 lookups=None, default_lookup='exact',
                 is_default=False, no_lookup=False,
                 *args, **kwargs):
        super(Filter, self).__init__(*args, **kwargs)
        self.form_field = form_field
        self._given_lookups = lookups
        self.default_lookup = default_lookup or self.default_lookup
        self.is_default = is_default
        self.no_lookup = no_lookup

    def repr(self, prefix=''):
        """
        Get custom representation of the filter

        The representation includes the following information:

        * filter class name
        * source name (same as :attr:`.source`) when filter is bound to parent
        * primary form field (same as :attr:`.form_field`)
        * which lookups this filter supports
        * default lookup (same as :attr:`.default_lookup`)
        * if the filter is a default filter (same as :attr:`.is_default`) when
          filter is bound to parent
        * if this filter does not support explicit lookups (same as :attr:`.no_lookup`)
        """
        return (
            '{name}('
            '{source}'
            'form_field={form_field}, '
            'lookups={lookups}, '
            'default_lookup="{default_lookup}", '
            '{is_default}'
            'no_lookup={no_lookup}'
            ')'
            ''.format(name=self.__class__.__name__,
                      source='source="{}", '.format(self.source) if self.is_bound else '',
                      form_field=self.form_field.__class__.__name__,
                      lookups=self._given_lookups or 'ALL',
                      default_lookup=self.default_lookup,
                      is_default='is_default={}, '.format(self.is_default) if self.is_bound else '',
                      no_lookup=self.no_lookup)
        )

    @cached_property
    def lookups(self):
        """
        Cached property for getting lookups this filter supports

        The reason why we need as a property is because lookups
        cant be hardcoded. There are 3 main distinct possibilities
        which drive which lookups are supported:

        * lookups were explicitly provided in the filter instantiation
          in which case we use those lookups. For example::

              >>> f = Filter(forms.CharField(), lookups=['exact', 'contains'])
        * when filter is already bound to a parent filterset and root
          filterset has a defined ``filter_backend`` we use supported
          lookups as explicitly defined by the backend. This is necessary
          since different backends support different sets of lookups.
        * when nether lookups are explicitly provided and filter is not bound
          yet we have no choice but not support any lookups and so we
          use empty set as supported lookups
        """
        if self._given_lookups:
            return set(self._given_lookups)
        if hasattr(self.root, 'filter_backend'):
            return self.root.filter_backend.supported_lookups
        return set()

    def get_form_field(self, lookup):
        """
        Get the form field for a particular lookup.

        This method does not blindly return :attr:`.form_field` attribute
        since some lookups require to use different validations.
        For example if the :attr:`.form_field` is ``CharField`` but
        the lookup is ``isnull``, it makes more sense to use
        ``BooleanField`` as form field.

        Parameters
        ----------
        lookup : str
            Name of the lookup

        Returns
        -------
        Field
            Instantiated form field appropriate for the given lookup.
        """
        if lookup in MANY_LOOKUP_FIELD_OVERWRITES:
            return MANY_LOOKUP_FIELD_OVERWRITES[lookup](child=self.form_field)
        elif lookup in LOOKUP_FIELD_OVERWRITES:
            return LOOKUP_FIELD_OVERWRITES[lookup]
        else:
            return self.form_field

    def clean_value(self, value, lookup):
        """
        Clean the filter value as appropriate for the given lookup.

        Parameters
        ----------
        value : str
            Filter value as given in the querystring to be validated
            and cleaned by using appropriate Django form field
        lookup : str
            Name of the lookup

        See Also
        --------
        get_form_field
        """
        form_field = self.get_form_field(lookup)
        return form_field.clean(value)

    def get_spec(self, config):
        """
        Get the ``FilterSpec`` for the provided ``config``.

        Parameters
        ----------
        config : LookupConfig
            Lookup configuration for which to build ``FilterSpec``.
            The lookup should be a leaf configuration otherwise
            ``ValidationError`` is raised.

        Returns
        -------
        FilterSpec
            spec constructed from the given configuration.
        """
        # lookup was explicitly provided
        if isinstance(config.data, dict):
            if not config.is_key_value():
                raise ValidationError(
                    'Invalid filtering data provided. '
                    'Data is more complex then expected. '
                    'Most likely additional lookup was specified '
                    'after the final lookup (e.g. field__in__equal=value).'
                )

            if self.no_lookup:
                raise ValidationError(
                    'Lookup was explicit used in filter specification. '
                    'This filter does not allow to specify lookup.'
                )

            lookup = config.name
            value = config.value.data

        # use default lookup
        else:
            lookup = self.default_lookup
            value = config.data

        if lookup not in self.lookups:
            raise ValidationError('"{}" lookup is not supported'.format(lookup))

        is_negated = '!' in config.key
        value = self.clean_value(value, lookup)

        return FilterSpec(self.components, lookup, value, is_negated)


def form_field_for_filter(form_field):
    """
    Decorator for specifying form field for a custom callable filter
    on the filter callable method

    Examples
    --------
    ::

        >>> class MyFilterCallable(CallableFilter):
        ...     @form_field_for_filter(forms.CharField())
        ...     def filter_foo_for_django(self, queryset, spec):
        ...         return queryset

    Parameters
    ----------
    form_field : Field
        Django form field which should be used for the decorated
        custom callable filter

    Returns
    -------
    func
        Function which can be used to decorate a class method
    """
    def wrapper(f):
        @wraps(f)
        def inner(self, *args, **kwargs):
            return f(self, *args, **kwargs)

        inner.form_field = form_field

        return inner

    return wrapper


class CallableFilter(Filter):
    """
    Custom filter class meant to be subclassed in order to add
    support for custom lookups via custom callables

    The goal of this filter is to provide:

    * support for custom callbacks (or overwrite existing ones)
    * support different filtering backends

    Custom callable functions for lookups and different backends
    are defined via class methods by using the following method
    name pattern::

        filter_<lookup_name>_for_<backend_name>

    Obviously multiple methods can be used to implement functionality
    for multiple lookups and/or backends. This makes callable filters
    pretty flexible and ideal for implementing custom reusable filtering
    filters which follow DRY.

    Examples
    --------
    ::

        >>> from django.http import QueryDict
        >>> from .filtersets import FilterSet

        >>> class MyCallableFilter(CallableFilter):
        ...     @form_field_for_filter(forms.CharField())
        ...     def filter_foo_for_django(self, queryset, spec):
        ...         f = queryset.filter if not spec.is_negated else queryset.exclude
        ...         return f(foo=spec.value)
        ...     def filter_foo_for_sqlalchemy(self, queryset, spec):
        ...         op = operator.eq if not spec.is_negated else operator.ne
        ...         return queryset.filter(op(Foo.foo, spec.value))

        >>> class MyFilterSet(FilterSet):
        ...     field = MyCallableFilter()

        >>> f = MyFilterSet(data=QueryDict('field__foo=bar'), queryset=[])

    .. note::
        Unlike base class :class:`.Filter` this filter makes
        ``form_field`` parameter optional. Please note however that
        when ``form_field`` parameter is not provided, all custom
        filter callables should define their own appropriate form fields
        by using :func:`.form_field_for_filter`.
    """

    def __init__(self, form_field=None, *args, **kwargs):
        # need to overwrite to make form_field optional
        super(CallableFilter, self).__init__(form_field, *args, **kwargs)

    @cached_property
    def lookups(self):
        """
        Get all supported lookups for the filter

        This property is identical to the super implementation except it also
        finds all custom lookups from the class methods and adds them to the
        set of supported lookups as returned by the super implementation.
        """
        lookups = super(CallableFilter, self).lookups

        r = LOOKUP_CALLABLE_FROM_METHOD_REGEX
        custom_lookups = {
            m.groupdict()['filter'] for m in (r.match(i) for i in dir(self))
            if m and m.groupdict()['backend'] == self.root.filter_backend.name
        }

        return lookups | custom_lookups

    def _get_filter_method_for_lookup(self, lookup):
        name = 'filter_{}_for_{}'.format(lookup, self.root.filter_backend.name)
        return getattr(self, name)

    def get_form_field(self, lookup):
        """
        Get the form field for a particular lookup.

        This method attempts to return form field for custom callables
        as set by :func:`.form_field_for_filter`. When either custom
        lookup is not set or its form field is not set, super implementation
        is used to get the form field. If form field at that point is not
        found, this method raises ``AssertionError``. That can only happen
        when `form_field` parameter is not provided during initialization.
        """
        try:
            return self._get_filter_method_for_lookup(lookup).form_field
        except AttributeError:
            pass

        form_field = super(CallableFilter, self).get_form_field(lookup)

        assert form_field is not None, (
            '{name} was not provided form_field parameter in initialization '
            '(e.g. {name}(form_field=CharField)) and form_field was not '
            'provided for the lookup. If the lookup is a custom filter callable '
            'you should provide form_field by using @form_field_for_filter '
            'decorator. If the lookup is a normal lookup, then please either '
            'provide form_field parameter or overwrite get_form_field().'
            ''.format(name=self.__class__.__name__)
        )

        return form_field

    def get_spec(self, config):
        """
        Get the :class:`.FilterSpec` for the given :class:`.LookupConfig`
        with appropriately set :attr:`.FilterSpec.filter_callable`
        when the lookup is a custom lookup
        """
        spec = super(CallableFilter, self).get_spec(config)
        spec.filter_callable = self._get_filter_method_for_lookup(spec.lookup)
        return spec
