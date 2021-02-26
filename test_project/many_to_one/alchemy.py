# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.orm import backref, relationship

from ..alchemy import Base


class Reporter(Base):
    __tablename__ = "many_to_one_reporter"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(30))
    last_name = Column(String(30))
    email = Column(String(254))

    @property
    def pk(self):
        return self.id


class Article(Base):
    __tablename__ = "many_to_one_article"
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer)
    headline = Column(String(100))
    pub_date = Column(Date)

    reporter = relationship(
        Reporter,
        backref=backref("articles", uselist=True),
        uselist=False,
        primaryjoin="test_project.many_to_one.alchemy.Article.reporter_id == Reporter.id",
        foreign_keys=reporter_id,
    )

    @property
    def pk(self):
        return self.id
