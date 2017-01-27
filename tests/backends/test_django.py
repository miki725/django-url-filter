# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import mock

from test_project.one_to_one.models import Place
from url_filter.backends.django import DjangoFilterBackend
from url_filter.utils import FilterSpec


class TestDjangoFilterBackend(object):
    def test_init(self):
        backend = DjangoFilterBackend(
            Place.objects.all(),
            context={'context': 'here'},
        )

        assert backend.model is Place
        assert backend.context == {'context': 'here'}

    def test_get_model(self):
        backend = DjangoFilterBackend(Place.objects.all())

        assert backend.get_model() is Place

    def test_bind(self):
        backend = DjangoFilterBackend(Place.objects.all())

        assert backend.specs == []
        backend.bind([1, 2])
        assert backend.specs == [1, 2]

    def test_includes(self):
        backend = DjangoFilterBackend(Place.objects.all())
        backend.bind([
            FilterSpec(['name'], 'exact', 'value', False),
            FilterSpec(['address'], 'contains', 'value', True),
        ])

        assert list(backend.includes) == [
            FilterSpec(['name'], 'exact', 'value', False),
        ]

    def test_excludes(self):
        backend = DjangoFilterBackend(Place.objects.all())
        backend.bind([
            FilterSpec(['name'], 'exact', 'value', False),
            FilterSpec(['address'], 'contains', 'value', True),
        ])

        assert list(backend.excludes) == [
            FilterSpec(['address'], 'contains', 'value', True),
        ]

    def test_prepare_spec(self):
        backend = DjangoFilterBackend(Place.objects.all())
        spec = backend._prepare_spec(FilterSpec(['name'], 'exact', 'value'))

        assert spec == 'name__exact'

    def test_filter(self):
        qs = mock.Mock()

        backend = DjangoFilterBackend(qs)
        backend.bind([
            FilterSpec(['name'], 'exact', 'value', False),
            FilterSpec(['address'], 'contains', 'value', True),
        ])

        result = backend.filter()

        assert result == qs.filter.return_value.exclude.return_value.distinct.return_value
        qs.filter.assert_called_once_with(name__exact='value')
        qs.filter.return_value.exclude.assert_called_once_with(address__contains='value')

    def test_filter_callable_specs(self):
        qs = mock.Mock()

        def foo(queryset, spec):
            return queryset.filter(spec)

        spec = FilterSpec(['name'], 'exact', 'value', False, foo)
        backend = DjangoFilterBackend(qs)
        backend.bind([spec])

        result = backend.filter()

        assert result == qs.distinct.return_value.filter.return_value
        qs.distinct.return_value.filter.assert_called_once_with(spec)
