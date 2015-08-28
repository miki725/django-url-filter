# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.routers import DefaultRouter

from test_project.one_to_one.api import (
    PlaceViewSet,
    RestaurantViewSet,
    WaiterViewSet,
)


router = DefaultRouter()
router.register('one-to-one/places', PlaceViewSet, 'one-to-one:place')
router.register('one-to-one/restaurants', RestaurantViewSet, 'one-to-one:restaurant')
router.register('one-to-one/waiters', WaiterViewSet, 'one-to-one:waiter')

urlpatterns = router.urls
