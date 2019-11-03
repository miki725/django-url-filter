# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend

from ..filtersets import ModelFilterSet


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
                assert issubclass(model, filter_model), (
                    "FilterSet model {} does not match queryset model {}"
                    "".format(filter_model, model)
                )

            try:
                return _filter.filter()
            except DjangoValidationError as e:
                raise ValidationError(e.message_dict)

        return queryset


URLFilterBackend = DjangoFilterBackend
