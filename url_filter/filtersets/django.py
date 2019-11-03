# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import operator

from django import forms
from django.conf import settings
from django.db import models
from django.db.models.fields.related import ForeignObjectRel, RelatedField

from ..exceptions import SkipFilter
from ..filters import Filter
from ..utils import SubClassDict
from .base import BaseModelFilterSet, ModelFilterSetOptions


__all__ = ["ModelFilterSet", "DjangoModelFilterSetOptions"]


GenericForeignKey = None


if "django.contrib.contenttypes" in settings.INSTALLED_APPS:
    from django.contrib.contenttypes.fields import GenericForeignKey


MODEL_FIELD_OVERWRITES = SubClassDict(
    {
        models.AutoField: forms.IntegerField(min_value=0),
        models.FileField: lambda m: forms.CharField(max_length=m.max_length),
    }
)


class DjangoModelFilterSetOptions(ModelFilterSetOptions):
    """
    Custom options for ``FilterSet``s used for Django models.

    Attributes
    ----------
    allow_related_reverse : bool, optional
        Flag specifying whether reverse relationships should
        be allowed while creating filter sets for children models.
    """

    def __init__(self, options=None):
        super(DjangoModelFilterSetOptions, self).__init__(options)
        self.allow_related_reverse = getattr(options, "allow_related_reverse", True)


class ModelFilterSet(BaseModelFilterSet):
    """
    :class:`.FilterSet` for Django models.

    The filterset can be configured via ``Meta`` class attribute,
    very much like Django's ``ModelForm`` is configured.
    """

    filter_options_class = DjangoModelFilterSetOptions

    def _get_model_field_names(self):
        """
        Get a list of all model fields.

        This is used when ``Meta.fields`` is ``None``
        in which case this method returns all model fields.
        """
        return list(
            map(operator.attrgetter("name"), self.Meta.model._meta.get_fields())
        )

    def _get_form_field_for_field(self, field):
        """
        Get form field for the given Django model field.

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

    def _build_filter(self, name, state):
        field = self.Meta.model._meta.get_field(
            self._get_filter_extra_kwargs(name).get("source", name)
        )

        if isinstance(field, RelatedField):
            if not self.Meta.allow_related:
                raise SkipFilter
            return self._build_filterset_from_related_field(name, field)

        elif isinstance(field, ForeignObjectRel):
            if not self.Meta.allow_related_reverse:
                raise SkipFilter
            return self._build_filterset_from_reverse_field(name, field)

        elif GenericForeignKey and isinstance(field, GenericForeignKey):
            raise SkipFilter

        else:
            return self._build_filter_from_field(name, field)

    def _build_filter_from_field(self, name, field):
        """
        Build :class:`.Filter` for a standard Django model field.
        """
        return Filter(
            form_field=self._get_form_field_for_field(field),
            is_default=field.primary_key,
            **self._get_filter_extra_kwargs(name)
        )

    def _build_filterset_from_related_field(self, name, field):
        """
        Build a :class:`.FilterSet` for a Django relation model field
        such as ``ForeignKey``.
        """
        # field.rel for Django < 1.9
        remote_field = getattr(field, "remote_field", None) or field.rel

        return self._build_django_filterset(
            name, field, {"exclude": [remote_field.name]}
        )

    def _build_filterset_from_reverse_field(self, name, field):
        """
        Build a :class:`.FilterSet` for a Django reverse relation model field.
        """
        return self._build_django_filterset(
            name, field, {"exclude": [field.field.name]}
        )

    def _build_django_filterset(self, name, field, meta_attrs):
        m = field.related_model
        attrs = {"model": m}
        attrs.update(meta_attrs)

        return self._build_filterset(m.__name__, name, attrs, ModelFilterSet)
