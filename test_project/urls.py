# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.routers import DefaultRouter

from test_project.many_to_many import api as m2m_api
from test_project.many_to_one import api as m2o_api
from test_project.one_to_one import api as o2o_api


router = DefaultRouter()

router.register('one-to-one/places/sqa', o2o_api.SQAPlaceViewSet, 'one-to-one-sqa:place')
router.register('one-to-one/places', o2o_api.PlaceViewSet, 'one-to-one:place')
router.register('one-to-one/restaurants/sqa', o2o_api.SQARestaurantViewSet, 'one-to-one-sqa:restaurant')
router.register('one-to-one/restaurants', o2o_api.RestaurantViewSet, 'one-to-one:restaurant')
router.register('one-to-one/waiters/sqa', o2o_api.SQAWaiterViewSet, 'one-to-one-sqa:waiter')
router.register('one-to-one/waiters', o2o_api.WaiterViewSet, 'one-to-one:waiter')

router.register('many-to-one/reporters/sqa', m2o_api.SQAReporterViewSet, 'many-to-one-sqa:reporter')
router.register('many-to-one/reporters', m2o_api.ReporterViewSet, 'many-to-one:reporter')
router.register('many-to-one/articles/sqa', m2o_api.SQAArticleViewSet, 'many-to-one-sqa:article')
router.register('many-to-one/articles', m2o_api.ArticleViewSet, 'many-to-one:article')

router.register('many-to-many/publications/sqa', m2m_api.SQAPublicationViewSet, 'many-to-many-sqa:publication')
router.register('many-to-many/publications', m2m_api.PublicationViewSet, 'many-to-many:publication')
router.register('many-to-many/articles/sqa', m2m_api.SQAArticleViewSet, 'many-to-many-sqa:article')
router.register('many-to-many/articles', m2m_api.ArticleViewSet, 'many-to-many:article')

urlpatterns = router.urls
