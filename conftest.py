# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

collect_ignore = []

try:
    import coreapi  # noqa: F401
    import coreschema  # noqa: F401
except ImportError:
    # coreapi is deprecated and cannot be imported on Python 3.13+
    # so skip doctest collection of the legacy integration module
    collect_ignore.append("url_filter/integrations/drf_coreapi.py")
