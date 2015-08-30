# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from functools import partial

from django import forms
from django.core.exceptions import ValidationError
from django.db.models.sql.constants import QUERY_TERMS

from .fields import MultipleValuesField
from .utils import FilterSpec


MANY_LOOKUP_FIELD_OVERWRITES = {
    'in': partial(MultipleValuesField, min_values=1),
    'range': partial(MultipleValuesField, min_values=2, max_values=2),
}

LOOKUP_FIELD_OVERWRITES = {
    'isnull': forms.BooleanField(),
    'second': forms.IntegerField(min_value=0, max_value=59),
    'minute': forms.IntegerField(min_value=0, max_value=59),
    'hour': forms.IntegerField(min_value=0, max_value=23),
    'week_day': forms.IntegerField(min_value=1, max_value=7),
    'day': forms.IntegerField(min_value=1, max_value=31),
    'month': forms.IntegerField(),
    'year': forms.IntegerField(min_value=0, max_value=9999),
}


class Filter(object):
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

    def __init__(self, source=None, *args, **kwargs):
        self._source = source
        self.parent = None
        self.name = None
        self._init(*args, **kwargs)

    def _init(self, form_field, lookups=None, default_lookup='exact', is_default=False):
        self.form_field = form_field
        self.lookups = lookups or list(QUERY_TERMS)
        self.default_lookup = default_lookup or self.default_lookup
        self.is_default = is_default

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
