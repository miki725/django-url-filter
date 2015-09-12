# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import backref, relationship

from ..alchemy import Base


class Place(Base):
    __tablename__ = 'one_to_one_place'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    address = Column(String(80))

    @property
    def pk(self):
        return self.id


class Restaurant(Base):
    __tablename__ = 'one_to_one_restaurant'
    place_id = Column(Integer, primary_key=True)
    serves_hot_dogs = Column(Boolean)
    serves_pizza = Column(Boolean)

    place = relationship(
        Place,
        backref=backref('restaurant', uselist=False),
        uselist=False,
        primaryjoin='Restaurant.place_id == Place.id',
        foreign_keys=place_id,
    )

    @property
    def pk(self):
        return self.place_id


class Waiter(Base):
    __tablename__ = 'one_to_one_waiter'
    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer)
    name = Column(String(50))

    restaurant = relationship(
        Restaurant,
        backref=backref('waiter_set', uselist=True),
        uselist=False,
        primaryjoin='Waiter.restaurant_id == Restaurant.place_id',
        foreign_keys=restaurant_id,
    )

    @property
    def pk(self):
        return self.id
