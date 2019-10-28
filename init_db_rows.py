#!/usr/bin/env python3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Item, User

# engine = create_engine('sqlite:///catalogdb.db')
engine = create_engine('postgresql://catalog:1234@localhost/catalog')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

pic = "18debd694829ed78203a5a36dd364160_400x400.png"

# Create dummy user
User1 = User(
    uniqueId="test",
    name="Robo Barista",
    email="tinnyTim@udacity.com",
    picture='https://pbs.twimg.com/profile_images/2671170543/' + pic)
session.add(User1)
session.commit()

category1 = Category(user_id=1, name="Soccer")

session.add(category1)
session.commit()

category2 = Category(user_id=1, name="Basketball")

session.add(category2)
session.commit()

category3 = Category(user_id=1, name="Baseball")

session.add(category3)
session.commit()

category4 = Category(user_id=1, name="Frisbee")

session.add(category4)
session.commit()

category5 = Category(user_id=1, name="Snowboarding")

session.add(category5)
session.commit()

category6 = Category(user_id=1, name="Foosball")

session.add(category6)
session.commit()


print("category added!")
