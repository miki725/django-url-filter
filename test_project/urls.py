# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.routers import DefaultRouter

from test_project.many_to_many import api as m2m_api
from test_project.one_to_one import api as o2o_api


router = DefaultRouter()

router.register('one-to-one/places', o2o_api.PlaceViewSet, 'one-to-one:place')
router.register('one-to-one/restaurants', o2o_api.RestaurantViewSet, 'one-to-one:restaurant')
router.register('one-to-one/waiters', o2o_api.WaiterViewSet, 'one-to-one:waiter')

router.register('many-to-many/publications', m2m_api.PublicationViewSet, 'many-to-many:publication')
router.register('many-to-many/articles', m2m_api.ArticleViewSet, 'many-to-many:article')

urlpatterns = router.urls
