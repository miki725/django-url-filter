# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.conf import settings
from sqlalchemy.orm import sessionmaker


Session = sessionmaker(bind=settings.SQLALCHEMY_ENGINE)


class SQLAlchemySessionMiddleware(object):
    def process_request(self, request):
        request.alchemy_session = Session()

    def process_response(self, request, response):
        request.alchemy_session.close()
        return response
