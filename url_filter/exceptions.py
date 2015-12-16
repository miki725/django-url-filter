# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals


class SkipFilter(Exception):
    """
    Exception to be used when any particular filter
    within the :class:`url_filter.filtersets.base.FilterSet` should be skipped.

    Possible reasons for skipping the field:

    * filter lookup config is invalid
      (e.g. using wrong field name -
      field is not present in filter set)
    * filter lookup value is invalid
      (e.g. submitted "a" for integer field)
    """
