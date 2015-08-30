# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from url_filter.filtersets import ModelFilterSet

from .models import Article, Reporter


class ReporterSerializer(ModelSerializer):
    class Meta(object):
        model = Reporter


class ArticleSerializer(ModelSerializer):
    class Meta(object):
        model = Article
        exclude = ['reporter']


class ReporterNestedSerializer(ModelSerializer):
    articles = ArticleSerializer(many=True)

    class Meta(object):
        model = Reporter


class ArticleNestedSerializer(ModelSerializer):
    reporter = ReporterSerializer()

    class Meta(object):
        model = Article


class ReporterFilterSet(ModelFilterSet):
    class Meta(object):
        model = Reporter


class ArticleFilterSet(ModelFilterSet):
    class Meta(object):
        model = Article


class ReporterViewSet(ModelViewSet):
    queryset = Reporter.objects.all()
    serializer_class = ReporterNestedSerializer
    filter_class = ReporterFilterSet


class ArticleViewSet(ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleNestedSerializer
    filter_class = ArticleFilterSet
