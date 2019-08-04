# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from url_filter.backends.sqlalchemy import SQLAlchemyFilterBackend
from url_filter.constants import StrictMode
from url_filter.filtersets import ModelFilterSet
from url_filter.filtersets.sqlalchemy import SQLAlchemyModelFilterSet

from . import alchemy
from .models import Article, Publication


class PublicationSerializer(ModelSerializer):
    class Meta(object):
        model = Publication
        exclude = []


class ArticleSerializer(ModelSerializer):
    class Meta(object):
        model = Article
        exclude = ["publications"]


class PublicationNestedSerializer(ModelSerializer):
    articles = ArticleSerializer(many=True)

    class Meta(object):
        model = Publication
        exclude = []


class ArticleNestedSerializer(ModelSerializer):
    publications = PublicationSerializer(many=True)

    class Meta(object):
        model = Article
        exclude = []


class PublicationFilterSet(ModelFilterSet):
    default_strict_mode = StrictMode.fail

    class Meta(object):
        model = Publication
        exclude = []


class SQLAlchemyPublicationFilterSet(SQLAlchemyModelFilterSet):
    default_strict_mode = StrictMode.fail
    filter_backend_class = SQLAlchemyFilterBackend

    class Meta(object):
        model = alchemy.Publication
        exclude = []


class ArticleFilterSet(ModelFilterSet):
    default_strict_mode = StrictMode.fail

    class Meta(object):
        model = Article
        exclude = []


class SQLAlchemyArticleFilterSet(SQLAlchemyModelFilterSet):
    default_strict_mode = StrictMode.fail
    filter_backend_class = SQLAlchemyFilterBackend

    class Meta(object):
        model = alchemy.Article
        exclude = []


class PublicationViewSet(ReadOnlyModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationNestedSerializer
    filter_class = PublicationFilterSet


class SQLAlchemyPublicationViewSet(ReadOnlyModelViewSet):
    serializer_class = PublicationNestedSerializer
    filter_class = SQLAlchemyPublicationFilterSet

    def get_queryset(self):
        return self.request.alchemy_session.query(alchemy.Publication)


class ArticleViewSet(ReadOnlyModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleNestedSerializer
    filter_class = ArticleFilterSet


class SQLAlchemyArticleViewSet(ReadOnlyModelViewSet):
    serializer_class = ArticleNestedSerializer
    filter_class = SQLAlchemyArticleFilterSet

    def get_queryset(self):
        return self.request.alchemy_session.query(alchemy.Article)
