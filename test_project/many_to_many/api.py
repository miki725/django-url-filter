# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from url_filter.filtersets import ModelFilterSet

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


class PublicationViewSet(ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationNestedSerializer
    filter_class = PublicationFilterSet


class ArticleFilterSet(ModelFilterSet):
    class Meta(object):
        model = Article


class ArticleViewSet(ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleNestedSerializer
    filter_class = ArticleFilterSet
