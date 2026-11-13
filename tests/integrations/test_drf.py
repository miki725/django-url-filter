# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import mock
import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import QueryDict
from rest_framework.exceptions import ValidationError

from test_project.one_to_one.api import PlaceFilterSet
from test_project.one_to_one.models import Place, Restaurant
from url_filter.filtersets import FilterSet, ModelFilterSet
from url_filter.integrations.drf import DjangoFilterBackend


class TestDjangoFilterBackend(object):
    def test_get_filter_class_supplied(self):
        class View(object):
            filter_class = PlaceFilterSet

        filter_class = DjangoFilterBackend().get_filter_class(
            View(), Place.objects.all()
        )

        assert filter_class is PlaceFilterSet

    def test_get_filter_class_by_filter_fields(self):
        class View(object):
            filter_fields = ["name"]

        filter_class = DjangoFilterBackend().get_filter_class(
            View(), Place.objects.all()
        )

        assert issubclass(filter_class, ModelFilterSet)
        assert filter_class.Meta.model is Place
        assert filter_class.Meta.fields == ["name"]

    def test_get_filter_class_all_fields(self):
        class View(object):
            filter_fields = "__all__"

        filter_class = DjangoFilterBackend().get_filter_class(
            View(), Place.objects.all()
        )

        assert issubclass(filter_class, ModelFilterSet)
        assert filter_class.Meta.model is Place
        assert set(filter_class().filters.keys()) == {
            "restaurant",
            "id",
            "name",
            "address",
        }

    def test_get_filter_context(self):
        context = DjangoFilterBackend().get_filter_context(
            request="request", view="view"
        )

        assert context == {"request": "request", "view": "view"}

    def test_get_filter_queryset_not_filtered(self):
        assert DjangoFilterBackend().filter_queryset(None, None, None) is None

    @mock.patch.object(FilterSet, "filter")
    def test_get_filter_queryset(self, mock_filter, db, rf):
        class View(object):
            filter_fields = ["name"]

        request = rf.get("/")
        request.query_params = QueryDict()

        filtered = DjangoFilterBackend().filter_queryset(
            request=request, queryset=Place.objects.all(), view=View()
        )

        assert filtered == mock_filter.return_value

    @mock.patch.object(FilterSet, "filter")
    def test_get_filter_queryset_invalid_query(self, mock_filter, db, rf):
        mock_filter.side_effect = DjangoValidationError({"foo": "bar"})

        class View(object):
            filter_fields = ["name"]

        request = rf.get("/")
        request.query_params = QueryDict()

        with pytest.raises(ValidationError) as e:
            DjangoFilterBackend().filter_queryset(
                request=request, queryset=Place.objects.all(), view=View()
            )

        assert e.value.detail == {"foo": ["bar"]}

    @mock.patch.object(FilterSet, "filter")
    def test_filter_queryset_supplied_model_mismatch(self, mock_filter, db, rf):
        class View(object):
            filter_class = PlaceFilterSet
            filter_fields = ["name"]

        request = rf.get("/")
        request.query_params = QueryDict()

        with pytest.raises(AssertionError):
            DjangoFilterBackend().filter_queryset(
                request=request, queryset=Restaurant.objects.all(), view=View()
            )


class TestDjangoFilterBackendOpenAPI(object):
    @pytest.fixture
    def viewset(self):
        from rest_framework.serializers import ModelSerializer
        from rest_framework.viewsets import ModelViewSet

        class RestaurantSerializer(ModelSerializer):
            class Meta(object):
                model = Restaurant
                fields = ["place", "serves_hot_dogs", "serves_pizza"]

        class RestaurantFilterSet(ModelFilterSet):
            class Meta(object):
                model = Restaurant
                extra_kwargs = {"place": {"id": {"no_lookup": True}}}

        class ViewSet(ModelViewSet):
            queryset = Restaurant.objects.all()
            serializer_class = RestaurantSerializer
            filter_backends = [DjangoFilterBackend]
            filter_class = RestaurantFilterSet

        return ViewSet

    def test_get_schema_operation_parameters_no_filter_class(self):
        from rest_framework.viewsets import ModelViewSet

        class ViewSet(ModelViewSet):
            queryset = Restaurant.objects.all()

        assert DjangoFilterBackend().get_schema_operation_parameters(ViewSet()) == []

    def test_get_schema_operation_parameters(self, viewset):
        parameters = DjangoFilterBackend().get_schema_operation_parameters(viewset())
        by_name = {i["name"]: i for i in parameters}

        assert len(by_name) == len(parameters)
        assert all(i["in"] == "query" and i["required"] is False for i in parameters)

        # no_lookup filter only exposes default lookup
        assert "place__id" in by_name
        assert not any(i.startswith("place__id__") for i in by_name)

        assert by_name["place__name"] == {
            "name": "place__name",
            "required": False,
            "in": "query",
            "description": "Match exactly the value as is",
            "schema": {"type": "string"},
        }
        assert by_name["place__name__in"] == {
            "name": "place__name__in",
            "required": False,
            "in": "query",
            "description": "Match when value is any of given comma separated values",
            "schema": {"type": "array", "items": {"type": "string"}},
            "style": "form",
            "explode": False,
        }
        assert by_name["serves_pizza"]["schema"] == {"type": "boolean"}
        assert by_name["waiter__id"]["schema"] == {"type": "integer"}
        assert by_name["waiter__id__gte"]["schema"] == {"type": "integer"}

    def test_get_schema_operation_parameters_unknown_lookup_description(self, viewset):
        with mock.patch.dict("url_filter.integrations.drf.DESCRIPTION", {}, clear=True):
            parameters = DjangoFilterBackend().get_schema_operation_parameters(
                viewset()
            )

        assert parameters
        assert all("description" not in i for i in parameters)

    def test_openapi_schema_generation(self, viewset):
        from django.urls import include, path
        from rest_framework.routers import SimpleRouter
        from rest_framework.schemas.openapi import SchemaGenerator

        router = SimpleRouter()
        router.register("restaurants", viewset, basename="restaurant")
        patterns = [path("api/", include(router.urls))]

        schema = SchemaGenerator(patterns=patterns).get_schema(public=True)

        list_params = {
            i["name"]: i
            for i in schema["paths"]["/api/restaurants/"]["get"]["parameters"]
        }
        assert list_params["waiter__name__icontains"]["in"] == "query"
        assert list_params["serves_pizza"]["schema"] == {"type": "boolean"}
        assert list_params["place__name__in"]["schema"]["type"] == "array"
