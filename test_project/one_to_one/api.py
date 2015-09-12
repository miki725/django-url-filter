# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from url_filter.backends.sqlalchemy import SQLAlchemyFilterBackend
from url_filter.filtersets import ModelFilterSet
from url_filter.filtersets.sqlalchemy import SQLAlchemyModelFilterSet

from . import alchemy
from .models import Place, Restaurant, Waiter


class PlaceSerializer(ModelSerializer):
    class Meta(object):
        model = Place


class RestaurantSerializer(ModelSerializer):
    place = PlaceSerializer()

    class Meta(object):
        model = Restaurant


class WaiterNestedSerializer(ModelSerializer):
    restaurant = RestaurantSerializer()

    class Meta(object):
        model = Waiter


class WaiterSerializer(ModelSerializer):
    class Meta(object):
        model = Waiter


class RestaurantNestedSerializer(ModelSerializer):
    place = PlaceSerializer()
    waiters = WaiterSerializer(source='waiter_set', many=True)

    class Meta(object):
        model = Restaurant


class RestaurantNestedWithoutPlaceSerializer(ModelSerializer):
    waiters = WaiterSerializer(source='waiter_set', many=True)

    class Meta(object):
        model = Restaurant


class PlaceNestedSerializer(ModelSerializer):
    restaurant = RestaurantNestedWithoutPlaceSerializer()

    class Meta(object):
        model = Place


class PlaceFilterSet(ModelFilterSet):
    class Meta(object):
        model = Place


class SQAPlaceFilterSet(SQLAlchemyModelFilterSet):
    filter_backend_class = SQLAlchemyFilterBackend

    class Meta(object):
        model = alchemy.Place


class RestaurantFilterSet(ModelFilterSet):
    class Meta(object):
        model = Restaurant


class SQARestaurantFilterSet(SQLAlchemyModelFilterSet):
    filter_backend_class = SQLAlchemyFilterBackend

    class Meta(object):
        model = alchemy.Restaurant


class WaiterFilterSet(ModelFilterSet):
    class Meta(object):
        model = Waiter


class SQAWaiterFilterSet(SQLAlchemyModelFilterSet):
    filter_backend_class = SQLAlchemyFilterBackend

    class Meta(object):
        model = alchemy.Waiter


class PlaceViewSet(ReadOnlyModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceNestedSerializer
    filter_class = PlaceFilterSet


class SQAPlaceViewSet(ReadOnlyModelViewSet):
    serializer_class = PlaceNestedSerializer
    filter_class = SQAPlaceFilterSet

    def get_queryset(self):
        return self.request.sqa_session.query(alchemy.Place)


class RestaurantViewSet(ReadOnlyModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantNestedSerializer
    filter_class = RestaurantFilterSet


class SQARestaurantViewSet(ReadOnlyModelViewSet):
    serializer_class = RestaurantNestedSerializer
    filter_class = SQARestaurantFilterSet

    def get_queryset(self):
        return self.request.sqa_session.query(alchemy.Restaurant)


class WaiterViewSet(ReadOnlyModelViewSet):
    queryset = Waiter.objects.all()
    serializer_class = WaiterNestedSerializer
    filter_class = WaiterFilterSet


class SQAWaiterViewSet(ReadOnlyModelViewSet):
    serializer_class = WaiterNestedSerializer
    filter_class = SQAWaiterFilterSet

    def get_queryset(self):
        return self.request.sqa_session.query(alchemy.Waiter)
