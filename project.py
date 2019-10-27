#!/usr/bin/env python3

from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from flask import session as login_session
from oauthlib.oauth2 import WebApplicationClient
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import httplib2
from database_setup import Base, Category, Item, User
import json
from flask import make_response
import requests


app = Flask(__name__)
app.secret_key = os.urandom(24)
APPLICATION_NAME = "Catalog Application"
# disable check SSL
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configuration
GOOGLE_CLIENT_ID = os.environ.get(
    "GOOGLE_CLIENT_ID",
    "412392477818-2l5m7m1mvne5duo38lc6j0es5su0l55r.apps.googleusercontent.com")
GOOGLE_CLIENT_SECRET = os.environ.get(
    "GOOGLE_CLIENT_SECRET", "MCzBxSTbUGAM-ZWYP4sXh_Zd")
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)


# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalogdb.db',
                       connect_args={'check_same_thread': False},
                       poolclass=StaticPool)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# User Helper Functions
def createUser(user):
    """ Add new user. """
    session.add(user)
    session.commit()
    user = session.query(User).filter_by(email=user.email).first()
    return user.id


def getUserInfo(user_id):
    """ Get user information. """
    user = session.query(User).filter_by(uniqueId=user_id).first()
    return user


def getUserID(email):
    """ Get user id. """
    user = session.query(User).filter_by(email=email).one()
    return user.id


@app.route("/login")
def login():
    """ Login to the app using google authentification. """

    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in our db with the information provided
    # by Google

    user = User(
        uniqueId=unique_id, name=users_name, email=users_email, picture=picture
    )

    # Doesn't exist? Add to database
    if not getUserInfo(unique_id):
        createUser(user)

    # Begin user session by logging the user in
    login_session['username'] = user.name
    login_session['picture'] = user.picture
    login_session['email'] = user.email
    login_session['uniqueId'] = user.uniqueId
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # Send user back to homepage
    return redirect(url_for("showCategoriesAndItems"))


@app.route("/logout")
def logout():
    """ Logout from the app. """
    if 'provider' in login_session:
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['uniqueId']
        del login_session['provider']
        flash("You have successfully been logged out.")
    return redirect(url_for("showCategoriesAndItems"))


def get_google_provider_cfg():
    """ Retrieve Google's provider configuration. """
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route('/')
@app.route('/catalog/')
def showCategoriesAndItems():
    """ Show all catalog. """
    categories = session.query(Category).order_by(
        asc(Category.name))  # get all categories
    items = session.query(Item).order_by(asc(Item.title))  # get all items
    if 'username' in login_session:
        return render_template(
            'catalog.html',
            categories=categories,
            items=items)
    else:
        return render_template(
            'publicCatalog.html',
            categories=categories,
            items=items)


@app.route('/catalog/newItem/', methods=['GET', 'POST'])
def newItem():
    """ Create a new item. """
    if 'username' in login_session:
        if request.method == 'POST':
            user = session.query(User).filter_by(
                email=login_session['email']).one()
            title = request.form['title']
            description = request.form['description']
            category = request.form['category']

            if title == '':
                flash('Title must have a value')
                categories = session.query(
                    Category).order_by(asc(Category.name))
                return render_template('newItem.html', data=categories)

            newItem = Item(title=title, description=description,
                           cat_id=category, user_id=user.id)
            session.add(newItem)
            session.commit()
            flash('Item with title %s Successfully Created' % (newItem.title))
            return redirect(url_for('showCategoriesAndItems'))
        else:
            categories = session.query(Category).order_by(asc(Category.name))
            return render_template('newItem.html', data=categories)
    else:
        categories = session.query(Category).order_by(
            asc(Category.name))  # get all categories
        items = session.query(Item).order_by(asc(Item.title))  # get all items
        flash('You must be logged in to access this content.')
        return render_template(
            'publicCatalog.html',
            categories=categories,
            items=items)


@app.route('/catalog/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    """ Edit an item. """
    if 'username' in login_session:  # check if the user is connected
        editedItem = session.query(Item).filter_by(id=item_id).one()
        user = session.query(User).filter_by(
            email=login_session['email']).one()
        # check if this item is the user item
        if editedItem.user_id != user.id:
            categories = session.query(Category).order_by(
                asc(Category.name))  # get all categories
            items = session.query(Item).order_by(
                asc(Item.title))  # get all items
            flash(
                'You are not authorized to edit this item.')
            return render_template(
                'catalog.html',
                categories=categories,
                items=items)
        if request.method == 'POST':
            if request.form['title']:
                editedItem.title = request.form['title']
            else:
                flash('Title must have a value')
                categories = session.query(
                    Category).order_by(asc(Category.name))
                return render_template('editItem.html', item_id=item_id,
                                       item=editedItem, data=categories)
            if request.form['description']:
                editedItem.description = request.form['description']
            if request.form['category']:
                editedItem.cat_id = request.form['category']

            session.add(editedItem)
            session.commit()
            flash('Item Successfully Edited')
            return redirect(url_for('showCategoriesAndItems'))
        else:
            categories = session.query(Category).order_by(asc(Category.name))
            return render_template(
                'editItem.html',
                item_id=item_id,
                item=editedItem,
                data=categories)
    else:
        categories = session.query(Category).order_by(
            asc(Category.name))  # get all categories
        items = session.query(Item).order_by(asc(Item.title))  # get all items
        flash('You must be logged in to access this content.')
        return render_template(
            'publicCatalog.html',
            categories=categories,
            items=items)


@app.route('/catalog/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    """ Delete an item. """
    if 'username' in login_session:  # check if the user is connected
        itemToDelete = session.query(Item).filter_by(id=item_id).one()
        user = session.query(User).filter_by(
            email=login_session['email']).one()
        # check if this item is the user item
        if itemToDelete.user_id != user.id:
            categories = session.query(Category).order_by(
                asc(Category.name))  # get all categories
            items = session.query(Item).order_by(
                asc(Item.title))  # get all items
            flash('You are not authorized to delete this item.')
            return render_template(
                'catalog.html',
                categories=categories,
                items=items)

        if request.method == 'POST':
            session.delete(itemToDelete)
            session.commit()
            flash('Item Successfully Deleted')
            return redirect(url_for('showCategoriesAndItems'))
        else:
            return render_template('deleteItem.html', item=itemToDelete)
    else:
        categories = session.query(Category).order_by(
            asc(Category.name))  # get all categories
        items = session.query(Item).order_by(asc(Item.title))  # get all items
        flash('You must be logged in to access this content.')
        return render_template(
            'publicCatalog.html',
            categories=categories,
            items=items)


@app.route('/catalog/<int:item_id>/show')
def showItem(item_id):
    """ Show an item. """
    itemToShow = session.query(Item).filter_by(id=item_id).one()
    return render_template('itemDetail.html', item=itemToShow)


@app.route('/category/<int:category_id>/items/')
def showCategoryItem(category_id):
    """ Show the items of the selected category. """
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).filter_by(cat_id=category.id).all()
    nbrItems = session.query(Item).filter_by(cat_id=category.id).count()
    if 'username' in login_session:
        return render_template(
            'category.html',
            items=items,
            categories=categories,
            category=category,
            nbrItems=nbrItems)
    else:
        return render_template(
            'publicCategory.html',
            items=items,
            categories=categories,
            category=category,
            nbrItems=nbrItems)


@app.route("/catalog.json", methods=["GET"])
def catalogJSON():
    """ Return all categories with their items in JSON format."""
    categories = [c.serialize for c in session.query(Category).all()]
    for c in range(len(categories)):
        items = [
            i.serialize for i in session.query(Item).filter_by(
                cat_id=categories[c]["id"]).all()]
        if items:
            categories[c]["Items"] = items
    return jsonify(Category=categories)


@app.route('/catalog/categories/JSON')
def categoriesJSON():
    """ JSON APIs to view categories Information."""
    categories = session.query(Category).all()
    return jsonify(categories=[r.serialize for r in categories])


@app.route('/catalog/categories/<int:cat_id>/JSON')
def categoryJSON(cat_id):
    """ JSON APIs to view single category Information."""
    category = session.query(Category).filter_by(id=cat_id).one()
    return jsonify(Category=category.serialize)


@app.route('/catalog/item/<string:title>/JSON')
def itemJSON(title):
    """ JSON APIs to view single item Information."""
    item = session.query(Item).filter_by(title=title).one()
    return jsonify(Item=item.serialize)


@app.route('/catalog/items/JSON')
def itemsJSON():
    """ JSON APIs to view items Information."""
    items = session.query(Item).all()
    return jsonify(items=[r.serialize for r in items])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
