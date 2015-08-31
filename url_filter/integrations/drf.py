# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.filters import BaseFilterBackend

from ..filtersets import ModelFilterSet


class DjangoFilterBackend(BaseFilterBackend):
    default_filter_set = ModelFilterSet

    def get_filter_class(self, view, queryset=None):
        filter_class_default = getattr(view, 'filter_class_default', self.default_filter_set)
        filter_class = getattr(view, 'filter_class', None)
        filter_class_meta_kwargs = getattr(view, 'filter_class_meta_kwargs', {})
        filter_fields = getattr(view, 'filter_fields', None)

        if filter_class:
            filter_model = getattr(filter_class.Meta, 'model', None)

            if filter_model:
                assert issubclass(queryset.model, filter_model), (
                    'FilterSet model {} does not match queryset model {}'
                    ''.format(filter_model, queryset.model)
                )

            return filter_class

        if filter_fields:
            model = queryset.model

            meta_kwargs = filter_class_meta_kwargs.copy()
            meta_kwargs.update({
                'model': model,
                'fields': filter_fields,
            })
            meta = type(str('Meta'), (object,), meta_kwargs)

            return type(
                str('{}FilterSet'.format(model.__name__)),
                (filter_class_default,),
                {'Meta': meta}
            )

    def get_filter_context(self, request, view):
        return {
            'request': request,
            'view': view,
        }

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)

        if filter_class:
            _filter = filter_class(
                data=request.query_params,
                queryset=queryset,
                context=self.get_filter_context(request, view),
            )
            return _filter.filter()

        return queryset
