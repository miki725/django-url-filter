# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import pytest
from django.conf import settings
from django.core.management import call_command
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def one_to_one(db):
    call_command('loaddata', 'one_to_one.json')


@pytest.fixture
def many_to_one(db):
    call_command('loaddata', 'many_to_one.json')


@pytest.fixture
def many_to_many(db):
    call_command('loaddata', 'many_to_many.json')


@pytest.fixture
def alchemy_db(request):
    session = sessionmaker(bind=settings.SQLALCHEMY_ENGINE)()

    def fin():
        session.close()

    request.addfinalizer(fin)

    return session
