# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.core.validators import (
    MaxLengthValidator as _MaxLengthValidator,
    MinLengthValidator as _MinLengthValidator,
)
from django.utils.deconstruct import deconstructible
from django.utils.translation import ungettext_lazy


@deconstructible
class MinLengthValidator(_MinLengthValidator):
    compare = lambda self, a, b: a < b
    clean = lambda self, x: len(x)
    code = 'min_length'
    message = ungettext_lazy(
        'Ensure this value has at least %(limit_value)d items (it has %(show_value)d).',
        'Ensure this value has at least %(limit_value)d items (it has %(show_value)d).',
        'limit_value'
    )


@deconstructible
class MaxLengthValidator(_MaxLengthValidator):
    compare = lambda self, a, b: a > b
    clean = lambda self, x: len(x)
    code = 'max_length'
    message = ungettext_lazy(
        'Ensure this value has at most %(limit_value)d items (it has %(show_value)d).',
        'Ensure this value has at most %(limit_value)d items (it has %(show_value)d).',
        'limit_value'
    )
