# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.conf import settings
from sqlalchemy.orm import sessionmaker


Session = sessionmaker(bind=settings.SQLALCHEMY_ENGINE)


def dbs():
    return {"default": settings.SQLALCHEMY_ENGINE}


class SQLAlchemySessionMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.alchemy_session = Session()
        try:
            return self.get_response(request)
        finally:
            request.alchemy_session.close()
