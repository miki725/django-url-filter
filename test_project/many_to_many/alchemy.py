# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import ForeignKey, Table

from ..alchemy import Base


class Publication(Base):
    __tablename__ = "many_to_many_publication"
    id = Column(Integer, primary_key=True)
    title = Column(String(30))

    @property
    def pk(self):
        return self.id


publication_article_association_table = Table(
    "many_to_many_article_publications",
    Base.metadata,
    Column("id", Integer),
    Column("publication_id", Integer, ForeignKey("many_to_many_publication.id")),
    Column("article_id", Integer, ForeignKey("many_to_many_article.id")),
)


class Article(Base):
    __tablename__ = "many_to_many_article"
    id = Column(Integer, primary_key=True)
    headline = Column(String(100))

    publications = relationship(
        Publication,
        secondary=publication_article_association_table,
        backref=backref("articles", uselist=True),
        uselist=True,
    )

    @property
    def pk(self):
        return self.id
