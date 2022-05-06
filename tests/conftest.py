# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import pytest
from django.core.management import call_command


@pytest.fixture
def one_to_one(db):
    call_command("loaddata", "one_to_one.json")


@pytest.fixture
def many_to_one(db):
    call_command("loaddata", "many_to_one.json")


@pytest.fixture
def many_to_many(db):
    call_command("loaddata", "many_to_many.json")
