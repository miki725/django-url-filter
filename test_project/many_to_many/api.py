# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from url_filter.constants import StrictMode
from url_filter.filtersets import ModelFilterSet

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


class ArticleFilterSet(ModelFilterSet):
    default_strict_mode = StrictMode.fail

    class Meta(object):
        model = Article
        exclude = []


class PublicationViewSet(ReadOnlyModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationNestedSerializer
    filter_class = PublicationFilterSet


class ArticleViewSet(ReadOnlyModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleNestedSerializer
    filter_class = ArticleFilterSet
