#!/usr/bin/env python3

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from flask_login import UserMixin

Base = declarative_base()

DATABASE = {
    'drivername': 'postgres',
    'host': '',
    'port': '5432',
    'username': 'baza', 
    'password': 'baza',
    'database': 'catalogdb'
}


class User(UserMixin, Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    uniqueId = Column(Integer, nullable=False)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id
        }


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    description = Column(String(250))
    cat_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'title': self.title,
            'description': self.description,
            'id': self.id,
        }


# DATABASE_URI = 'postgres+psycopg2://baza:baza@localhost:5432/catalogdb'

# engine = create_engine('sqlite:///catalogdb.db')

engine = create_engine(URL(**DATABASE))

Base.metadata.create_all(engine)
