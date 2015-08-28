# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from url_filter.filtersets import ModelFilterSet

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


class RestaurantFilterSet(ModelFilterSet):
    class Meta(object):
        model = Restaurant


class WaiterFilterSet(ModelFilterSet):
    class Meta(object):
        model = Waiter


class PlaceViewSet(ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceNestedSerializer
    filter_class = PlaceFilterSet


class RestaurantViewSet(ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantNestedSerializer
    filter_class = RestaurantFilterSet


class WaiterViewSet(ModelViewSet):
    queryset = Waiter.objects.all()
    serializer_class = WaiterNestedSerializer
    filter_class = WaiterFilterSet
