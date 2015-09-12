# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from url_filter.backends.sqlalchemy import SQLAlchemyFilterBackend
from url_filter.filtersets import ModelFilterSet
from url_filter.filtersets.sqlalchemy import SQLAlchemyModelFilterSet

from . import alchemy
from .models import Article, Publication


class PublicationSerializer(ModelSerializer):
    class Meta(object):
        model = Publication


class ArticleSerializer(ModelSerializer):
    class Meta(object):
        model = Article
        exclude = ['publications']


class PublicationNestedSerializer(ModelSerializer):
    articles = ArticleSerializer(many=True)

    class Meta(object):
        model = Publication


class ArticleNestedSerializer(ModelSerializer):
    publications = PublicationSerializer(many=True)

    class Meta(object):
        model = Article


class PublicationFilterSet(ModelFilterSet):
    class Meta(object):
        model = Publication


class SQAPublicationFilterSet(SQLAlchemyModelFilterSet):
    filter_backend_class = SQLAlchemyFilterBackend

    class Meta(object):
        model = alchemy.Publication


class ArticleFilterSet(ModelFilterSet):
    class Meta(object):
        model = Article


class SQAArticleFilterSet(SQLAlchemyModelFilterSet):
    filter_backend_class = SQLAlchemyFilterBackend

    class Meta(object):
        model = alchemy.Article


class PublicationViewSet(ReadOnlyModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationNestedSerializer
    filter_class = PublicationFilterSet


class SQAPublicationViewSet(ReadOnlyModelViewSet):
    serializer_class = PublicationNestedSerializer
    filter_class = SQAPublicationFilterSet

    def get_queryset(self):
        return self.request.sqa_session.query(alchemy.Publication)


class ArticleViewSet(ReadOnlyModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleNestedSerializer
    filter_class = ArticleFilterSet


class SQAArticleViewSet(ReadOnlyModelViewSet):
    serializer_class = ArticleNestedSerializer
    filter_class = SQAArticleFilterSet

    def get_queryset(self):
        return self.request.sqa_session.query(alchemy.Article)
