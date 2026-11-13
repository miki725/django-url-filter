# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models.constants import LOOKUP_SEP
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend

from ..fields import MultipleValuesField
from ..filtersets import FilterSet, ModelFilterSet

DESCRIPTION = {
    "contains": "Match when string contains given substring",
    "date": "Match by the date value of the timestamp",
    "day": "Match by day of the month",
    "endswith": "Match when string ends with given substring",
    "exact": "Match exactly the value as is",
    "gt": "Match when value is greater then given value",
    "gte": "Match when value is greater or equal then given value",
    "hour": "Match by the hour (24 hour) value of the timestamp",
    "icontains": "Case insensitive match when string contains given substring",
    "iendswith": "Case insensitive match when string ends with given substring",
    "iexact": "Case insensitive match exactly the value as is",
    "iin": "Case insensitive match when value is any of given comma separated values",
    "in": "Match when value is any of given comma separated values",
    "iregex": "Case insensitive match string by regex pattern",
    "isnull": "Match when value is NULL",
    "istartswith": "Case insensitive match when string starts with given substring",
    "lt": "Match when value is less then given value",
    "lte": "Match when value is less or equal then given value",
    "minute": "Match by the minute value of the timestamp",
    "month": "Match by the month value of the timestamp",
    "range": "Match when value is within comma separated range",
    "regex": "Match string by regex pattern",
    "second": "Match by the second value of the timestamp",
    "startswith": "Match when string starts with given substring",
    "week_day": "Match by week day (1-Sunday to 7-Saturday) of the timestamp",
    "year": "Match by the year value of the timestamp",
}
"""
Human-readable descriptions of lookups used in generated API schemas
"""

FORM_FIELD_TO_OPENAPI_SCHEMA = {
    MultipleValuesField: {"type": "array", "items": {"type": "string"}},
    forms.BooleanField: {"type": "boolean"},
    forms.IntegerField: {"type": "integer"},
    forms.FloatField: {"type": "number"},
}
"""
Mapping of form field classes to OpenAPI schema definitions.
Any form field not listed here is documented as ``string``.
"""


def iter_filters(filterset, prefix=()):
    """
    Iterate over all leaf filters within a filterset including all supported lookups

    Nested filtersets are recursively traversed.

    Yields
    ------
    tuple
        ``(query_param_name, filter, lookup)`` for every query parameter
        the filterset accepts
    """
    for name, field in filterset.filters.items():
        if isinstance(field, FilterSet):
            for i in iter_filters(field, prefix=prefix + (name,)):
                yield i
            continue

        yield LOOKUP_SEP.join(prefix + (name,)), field, field.default_lookup
        if field.no_lookup:
            continue
        for lookup in field.lookups:
            yield LOOKUP_SEP.join(prefix + (name, lookup)), field, lookup


class DjangoFilterBackend(BaseFilterBackend):
    """
    DRF filter backend which integrates with ``django-url-filter``

    This integration backend can be specified in global DRF settings::

        # settings.py
        REST_FRAMEWORK = {
            'DEFAULT_FILTER_BACKENDS': [
                'url_filter.integrations.drf.DjangoFilterBackend',
            ]
        }

    Alternatively filter backend can be specified per view/viewset bases::

        class MyViewSet(ModelViewSet):
            queryset = MyModel.objects.all()
            filter_backends = [DjangoFilterBackend]
            filter_fields = ['field1', 'field2']

    The following attributes can be specified on the view:

    * ``filter_class`` - explicit filter (:class:`.FilterSet` to be specific) class
      which should be used for filtering. When this attribute is supplied, this
      filterset will be used and all other attributes described below will are ignored.
    * ``filter_fields`` - list of strings which should be names
      of fields which should be included in the generated :class:`.FilterSet`.
      This is equivalent::

          class MyFilterSet(ModelFilterSet):
              class Meta(object):
                  model = MyModel
                  fields = ['fields1', ...]
    * ``filter_class_meta_kwargs`` - additional kwargs which should be passed
      in ``Meta`` for the generated :class:`.FilterSet`.
    * ``filter_class_default`` - base class to use while creating new :class:`.FilterSet`.
      This is primarily useful when using non-Django data-sources.
      By default :attr:`.default_filter_set` is used.

    See Also
    --------
    :py:class:`url_filter.integrations.drf_coreapi.CoreAPIURLFilterBackend`
    """

    default_filter_set = ModelFilterSet
    """
    Default base class which will be used while dynamically creating :class:`.FilterSet`
    """

    def get_filter_class(self, view, queryset=None):
        """
        Get filter class which will be used for filtering.

        Parameters
        ----------
        view : View
            DRF view/viewset where this filter backend is being used.
            Please refer to :class:`.DjangoFilterBackend` documentation
            for list of attributes which can be supplied in view
            to customize how filterset will be determined.
        queryset
            Query object for filtering

        Returns
        -------
        :class:`.FilterSet`
            :class:`.FilterSet` class either directly specified in the view or
            dynamically constructed for the queryset model.
        None
            When appropriate :class:`.FilterSet` cannot be determined
            for filtering
        """
        filter_class_default = getattr(
            view, "filter_class_default", self.default_filter_set
        )
        filter_class = getattr(view, "filter_class", None)
        filter_class_meta_kwargs = getattr(view, "filter_class_meta_kwargs", {})
        filter_fields = getattr(view, "filter_fields", None)

        if filter_class:
            return filter_class

        if filter_fields:
            model = filter_class_default.filter_backend_class(queryset).get_model()

            meta_kwargs = filter_class_meta_kwargs.copy()
            meta_kwargs.update({"model": model, "fields": filter_fields})
            meta = type(str("Meta"), (object,), meta_kwargs)

            return type(
                str("{}FilterSet".format(model.__name__)),
                (filter_class_default,),
                {"Meta": meta},
            )

    def get_filter_context(self, request, view):
        """
        Get context to be passed to :class:`.FilterSet` during initialization

        Parameters
        ----------
        request : HttpRequest
            Request object from the view
        view : View
            View where this filter backend is being used

        Returns
        -------
        dict
            Context to be passed to :class:`.FilterSet`
        """
        return {"request": request, "view": view}

    def filter_queryset(self, request, queryset, view):
        """
        Main method for filtering query object

        Parameters
        ----------
        request : HttpRequest
            Request object from the view
        queryset
            Query object for filtering
        view : View
            View where this filter backend is being used

        Returns
        -------
        object
            Filtered query object if filtering class was determined by
            :meth:`.get_filter_class`. If not given ``queryset`` is returned.
        """
        filter_class = self.get_filter_class(view, queryset)

        if filter_class:
            _filter = filter_class(
                data=request.query_params,
                queryset=queryset,
                context=self.get_filter_context(request, view),
            )

            filter_model = getattr(_filter.Meta, "model", None)
            if filter_model and _filter.filter_backend.enforce_same_models:
                model = _filter.filter_backend.model
                assert issubclass(
                    model, filter_model
                ), "FilterSet model {} does not match queryset model {}" "".format(
                    filter_model, model
                )

            try:
                return _filter.filter()
            except DjangoValidationError as e:
                raise ValidationError(e.message_dict)

        return queryset

    def get_schema_filterset(self, view):
        """
        Get :class:`.FilterSet` instance used to describe filters in API schemas

        Returns
        -------
        :class:`.FilterSet`
            Filterset instance for the view
        None
            When filtering is not configured on the view
        """
        queryset = view.get_queryset()
        filter_class = self.get_filter_class(view, queryset)
        if not filter_class:
            return None
        return filter_class(data={}, queryset=queryset)

    def get_schema_operation_parameters(self, view):
        """
        Get OpenAPI query parameter definitions for all supported filters

        Used by DRF's OpenAPI schema generator
        (``rest_framework.schemas.openapi.AutoSchema``).
        Returns all filters including their supported lookups.
        """
        filterset = self.get_schema_filterset(view)
        if filterset is None:
            return []

        parameters = []
        for name, field, lookup in iter_filters(filterset):
            form_field = field.get_form_field(lookup)
            schema = dict(
                FORM_FIELD_TO_OPENAPI_SCHEMA.get(type(form_field), {"type": "string"})
            )
            parameter = {
                "name": name,
                "required": False,
                "in": "query",
                "schema": schema,
            }
            if lookup in DESCRIPTION:
                parameter["description"] = DESCRIPTION[lookup]
            if schema["type"] == "array":
                parameter["style"] = "form"
                parameter["explode"] = False
            parameters.append(parameter)
        return parameters


URLFilterBackend = DjangoFilterBackend
