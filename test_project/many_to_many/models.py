from django.db import models


class Publication(models.Model):
    title = models.CharField(max_length=30)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("title",)


class Article(models.Model):
    headline = models.CharField(max_length=100)
    publications = models.ManyToManyField(Publication, related_name="articles")

    def __str__(self):
        return self.headline

    class Meta:
        ordering = ("headline",)
