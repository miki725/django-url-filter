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

LOOKUP_CALLABLE_FROM_METHOD_REGEX = re.compile(r'^filter_([\w\d]+)_for_[\w\d]+$')


class BaseFilter(six.with_metaclass(abc.ABCMeta, object)):
    def __init__(self, source=None, *args, **kwargs):
        self._source = source
        self.parent = None
        self.name = None

    def __repr__(self):
        data = self.repr()
        data = data if six.PY3 else data.encode('utf-8')
        return data

    @abc.abstractmethod
    def repr(self, prefix=''):
        """
        """

    @property
    def source(self):
        """
        Source field/attribute in queryset model to be used for filtering.

        This property is helpful when ``source`` parameter is not provided
        when instantiating ``Filter`` since it will use the filter name
        as it is defined in the ``FilterSet``. For example::

            >>> class MyFilterSet(FilterSet):
            ...     foo = Filter(form_field=CharField())
            ...     bar = Filter(source='stuff', form_field=CharField())
            >>> fs = MyFilterSet()
            >>> print(fs.fields['foo'].source)
            foo
            >>> print(fs.fields['bar'].source)
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

        This method should be used by the parent ``FilterSet``
        since it allows to specify the parent and name of each
        filter within the filterset.
        """
        self.name = name
        self.parent = parent

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
    Filter class which main job is to convert leaf ``LookupConfig``
    to ``FilterSpec``.

    Each filter by itself is meant to be used a "field" in the
    ``FilterSpec``.

    Parameters
    ----------
    source : str
        Name of the attribute for which which filter applies to
        within the model of the queryset to be filtered
        as given to the ``FilterSet``.
    form_field : Field
        Instance of Django's ``forms.Field`` which will be used
        to clean the filter value as provided in the queryset.
        For example if field is ``IntegerField``, this filter
        will make sure to convert the filtering value to integer
        before creating a ``FilterSpec``.
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
        filter in the parent ``FilterSet``.
        By default it is ``False``.
        Primarily this is used when querystring lookup key
        refers to a nested ``FilterSet`` however it does not specify
        which filter to use. For example lookup key ``user__profile``
        intends to filter something in the user's profile however
        it does not specify by which field to filter on.
        In that case the default filter within profile ``FilterSet``
        will be used. At most, one default filter should be provided
        in the ``FilterSet``.

    Attributes
    ----------
    parent : FilterSet
        Parent ``FilterSet`` to which this filter is bound to
    name : str
        Name of the field as it is defined in parent ``FilterSet``
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
        return (
            '{name}('
            'form_field={form_field}, '
            'lookups={lookups}, '
            'default_lookup="{default_lookup}", '
            'is_default={is_default}, '
            'no_lookup={no_lookup}'
            ')'
            ''.format(name=self.__class__.__name__,
                      form_field=self.form_field.__class__.__name__,
                      lookups=self._given_lookups or 'ALL',
                      default_lookup=self.default_lookup,
                      is_default=self.is_default,
                      no_lookup=self.no_lookup)
        )

    @cached_property
    def lookups(self):
        if self._given_lookups:
            return set(self._given_lookups)
        if hasattr(self.root, 'filter_backend'):
            return self.root.filter_backend.supported_lookups
        return set()

    def get_form_field(self, lookup):
        """
        Get the form field for a particular lookup.

        This method does not blindly return ``form_field`` attribute
        since some lookups require to use different validations.
        For example for if the ``form_field`` is ``CharField`` but
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
    def wrapper(f):
        @wraps(f)
        def inner(self, *args, **kwargs):
            return f(self, *args, **kwargs)

        inner.form_field = form_field

        return inner

    return wrapper


class CallableFilter(Filter):
    def __init__(self, form_field=None, *args, **kwargs):
        # need to overwrite to make form_field optional
        super(CallableFilter, self).__init__(form_field, *args, **kwargs)

    @cached_property
    def lookups(self):
        lookups = super(CallableFilter, self).lookups

        r = LOOKUP_CALLABLE_FROM_METHOD_REGEX
        custom_lookups = {m.group(0) for m in (r.match(i) for i in dir(self)) if m}

        return lookups | custom_lookups

    def _get_filter_method_for_lookup(self, lookup):
        name = 'filter_{}_for_{}'.format(lookup, self.root.filter_backend.name)
        return getattr(self, name, None)

    def _is_callable_filter(self, lookup):
        return bool(self._get_filter_method_for_lookup(lookup))

    def get_form_field(self, lookup):
        if self._is_callable_filter(lookup):
            filter_method = self._get_filter_method_for_lookup(lookup)

            form_field = getattr(filter_method, 'form_field', None)
            if form_field is not None:
                return form_field

        form_field = super(CallableFilter, self).get_form_field(lookup)

        assert form_field is not None, (
            '{name} was not provided form_field parameter in initialization '
            '(e.g. {name}(form_field=CharField)) and form_field was not '
            'provided for the lookup. If the lookup is a custom filter callable '
            'you should profile form_field by using @form_field_for_filter '
            'decorator. If the lookup is a normal lookup, then please either '
            'provide form_field paramer or overwrite get_form_field().'
            ''.format(name=self.__class__.__name__)
        )

        return form_field

    def get_spec(self, config):
        spec = super(CallableFilter, self).get_spec(config)
        spec.filter_callable = self._get_filter_method_for_lookup(spec.lookup)
        return spec
