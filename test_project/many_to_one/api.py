# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_ufilter.constants import StrictMode
from django_ufilter.filtersets import ModelFilterSet

from .models import Article, Reporter


class ReporterSerializer(ModelSerializer):
    class Meta(object):
        model = Reporter
        exclude = []


class ArticleSerializer(ModelSerializer):
    class Meta(object):
        model = Article
        exclude = ["reporter"]


class ReporterNestedSerializer(ModelSerializer):
    articles = ArticleSerializer(many=True)

    class Meta(object):
        model = Reporter
        exclude = []


class ArticleNestedSerializer(ModelSerializer):
    reporter = ReporterSerializer()

    class Meta(object):
        model = Article
        exclude = []


class ReporterFilterSet(ModelFilterSet):
    default_strict_mode = StrictMode.fail

    class Meta(object):
        model = Reporter
        exclude = []


class ArticleFilterSet(ModelFilterSet):
    default_strict_mode = StrictMode.fail

    class Meta(object):
        model = Article
        exclude = []


class ReporterViewSet(ReadOnlyModelViewSet):
    queryset = Reporter.objects.all()
    serializer_class = ReporterNestedSerializer
    filter_class = ReporterFilterSet


class ArticleViewSet(ReadOnlyModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleNestedSerializer
    filter_class = ArticleFilterSet
