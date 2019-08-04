# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import enum


class StrictMode(enum.Enum):
    """
    Strictness mode enum.

    :``empty``:
        when validation fails for any filter within :class:`.FilterSet`,
        empty queryset should be returned
    :``drop`` (default):
        ignores all filter failures. when any occur, :class:`.FilterSet`
        simply then does not filter provided queryset.
    :``fail``:
        when validation fails for any filter within :class:`.FilterSet`,
        all error are compiled and cumulative ``ValidationError`` is raised.
    """

    empty = "empty"
    drop = "drop"
    fail = "fail"
