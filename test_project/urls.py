# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.routers import DefaultRouter

from test_project.many_to_many import api as m2m_api
from test_project.many_to_one import api as m2o_api
from test_project.one_to_one import api as o2o_api


router = DefaultRouter()

router.register('one-to-one/places/alchemy', o2o_api.SQLAlchemyPlaceViewSet, 'one-to-one-alchemy:place')
router.register('one-to-one/places/plain', o2o_api.PlainPlaceViewSet, 'one-to-one-plain:place')
router.register('one-to-one/places', o2o_api.PlaceViewSet, 'one-to-one:place')
router.register('one-to-one/restaurants/alchemy', o2o_api.SQLAlchemyRestaurantViewSet, 'one-to-one-alchemy:restaurant')
router.register('one-to-one/restaurants', o2o_api.RestaurantViewSet, 'one-to-one:restaurant')
router.register('one-to-one/waiters/alchemy', o2o_api.SQLAlchemyWaiterViewSet, 'one-to-one-alchemy:waiter')
router.register('one-to-one/waiters', o2o_api.WaiterViewSet, 'one-to-one:waiter')

router.register('many-to-one/reporters/alchemy', m2o_api.SQLAlchemyReporterViewSet, 'many-to-one-alchemy:reporter')
router.register('many-to-one/reporters', m2o_api.ReporterViewSet, 'many-to-one:reporter')
router.register('many-to-one/articles/alchemy', m2o_api.SQLAlchemyArticleViewSet, 'many-to-one-alchemy:article')
router.register('many-to-one/articles', m2o_api.ArticleViewSet, 'many-to-one:article')

router.register('many-to-many/publications/alchemy', m2m_api.SQLAlchemyPublicationViewSet, 'many-to-many-alchemy:publication')
router.register('many-to-many/publications', m2m_api.PublicationViewSet, 'many-to-many:publication')
router.register('many-to-many/articles/alchemy', m2m_api.SQLAlchemyArticleViewSet, 'many-to-many-alchemy:article')
router.register('many-to-many/articles', m2m_api.ArticleViewSet, 'many-to-many:article')

urlpatterns = router.urls
