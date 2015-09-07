# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.conf import settings
from sqlalchemy.orm import sessionmaker


Session = sessionmaker(bind=settings.SQA_ENGINE)


class SQASessionMiddleware(object):
    def process_request(self, request):
        request.sqa_session = Session()

    def process_response(self, request, response):
        request.sqa_session.close()
        return response
