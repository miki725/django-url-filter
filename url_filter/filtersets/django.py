# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import operator

from django import forms
from django.db import models
from django.db.models.fields.related import ForeignObjectRel, RelatedField

from ..exceptions import SkipFilter
from ..filters import Filter
from ..utils import SubClassDict
from .base import FilterSet


__all__ = ['ModelFilterSet', 'ModelFilterSetOptions']


MODEL_FIELD_OVERWRITES = SubClassDict({
    models.AutoField: forms.IntegerField(min_value=0),
    models.FileField: lambda m, f: forms.CharField(max_length=m.max_length),
})


class ModelFilterSetOptions(object):
    """
    Custom options for ``FilterSet``s used for Django models.

    Attributes
    ----------
    model : Model
        Django model class from which ``FilterSet`` will
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
    allow_related_reverse : bool, optional
    """
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', [])
        self.allow_related = getattr(options, 'allow_related', True)
        self.allow_related_reverse = getattr(options, 'allow_related_reverse', True)


class ModelFilterSet(FilterSet):
    """
    ``FilterSet`` for Django models.

    The filterset can be configured via ``Meta`` class attribute,
    very much like Django's ``ModelForm`` is configured.

    """
    filter_options_class = ModelFilterSetOptions

    def get_filters(self):
        """
        Get all filters defined in this filterset including
        filters corresponding to Django model fields.
        """
        filters = super(ModelFilterSet, self).get_filters()

        assert self.Meta.model, (
            '{}.Meta.model is missing. Please specify the model '
            'in order to use ModelFilterSet.'
            ''.format(self.__class__.__name__)
        )

        if self.Meta.fields is None:
            self.Meta.fields = self.get_model_field_names()

        for name in self.Meta.fields:
            if name in self.Meta.exclude:
                continue

            field = self.Meta.model._meta.get_field(name)

            try:
                if isinstance(field, RelatedField):
                    if not self.Meta.allow_related:
                        raise SkipFilter
                    _filter = self.build_filterset_from_related_field(field)
                elif isinstance(field, ForeignObjectRel):
                    if not self.Meta.allow_related_reverse:
                        raise SkipFilter
                    _filter = self.build_filterset_from_reverse_field(field)
                elif isinstance(field, models.Field):
                    _filter = self.build_filter_from_field(field)
                else:
                    continue

            except SkipFilter:
                continue

            else:
                if _filter is not None:
                    filters[name] = _filter

        return filters

    def get_model_field_names(self):
        """
        Get a list of all model fields.

        This is used when ``Meta.fields`` is ``None``
        in which case this method returns all model fields.
        """
        return list(map(
            operator.attrgetter('name'),
            self.Meta.model._meta.get_fields()
        ))

    def get_form_field_for_field(self, field):
        """
        Get form field for the given Djagno model field.

        By default ``Field.formfield()`` is used to get the form
        field unless an overwrite is present for the field.
        Overwrites are useful for non-standard fields like
        ``FileField`` since in that case ``CharField``
        should be used.
        """
        overwrite = MODEL_FIELD_OVERWRITES.get(field.__class__)
        if overwrite is not None:
            if callable(overwrite):
                return overwrite(field)
            else:
                return overwrite

        form_field = field.formfield()

        if form_field is None:
            raise SkipFilter

        return form_field

    def build_filter_from_field(self, field):
        """
        Build ``Filter`` for a standard Django model field.
        """
        return Filter(
            form_field=self.get_form_field_for_field(field),
            is_default=field.primary_key,
        )

    def build_filterset_from_related_field(self, field):
        """
        Build a ``FilterSet`` for a Django relation model field
        such as ``ForeignKey``.
        """
        m = field.related_model

        class Meta(object):
            model = m

        filterset = type(
            str('{}FilterSet'.format(m.__name__)),
            (ModelFilterSet,),
            {
                'Meta': Meta,
                '__module__': self.__module__,
            }
        )

        return filterset()

    def build_filterset_from_reverse_field(self, field):
        """
        Build a ``FilterSet`` for a Django reverse relation model field.
        """
        m = field.related_model

        class Meta(object):
            model = m
            allow_related = False

        filterset = type(
            str('{}FilterSet'.format(m.__name__)),
            (ModelFilterSet,),
            {
                'Meta': Meta,
                '__module__': self.__module__,
            }
        )

        return filterset()
