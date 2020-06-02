import six
from django.db import models


@six.python_2_unicode_compatible
class Reporter(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)


@six.python_2_unicode_compatible
class Article(models.Model):
    headline = models.CharField(max_length=100)
    pub_date = models.DateField()
    reporter = models.ForeignKey(
        Reporter, related_name="articles", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.headline

    class Meta:
        ordering = ("headline",)
