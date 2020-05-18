from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ModelA(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class ModelB(models.Model):
    name = models.CharField(max_length=64)
    a = models.ForeignKey(
        ModelA, blank=True, null=True, related_name="rel_b", on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(
        ContentType, related_name="+", on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return self.name
