import random
import string
import httplib2
import json
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import requests

from flask import make_response
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Login informstion for session
@app.route('/login')
def showLogin():
    categories = session.query(Category).all()
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, categories=categories)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 100px; height: 100px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# Revoke the current user's token and reset the session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print(access_token)
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
                json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        print(response)
        return redirect(url_for('showCatalog'))
    else:
        response = make_response(json.dumps('Failed to revoke token.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# API Endpoint for Catalog (GET Request)
@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(Category).order_by(Category.name.asc()).all()
    sCats = []
    for c in categories:
        cat = c.serialize
        items = session.query(Item).filter(Item.category_id == c.id).all()
        sItems = []
        for i in items:
            sItems.append(i.serialize)
        cat['items'] = sItems
        sCats.append(cat)
    return jsonify(categories=[sCats])
# def catalogJSON():
#     categories = session.query(Category).all()
#     return jsonify(Category=[i.serialize for i in categories])


# API Endpoint for Items in a Category (GET Requst)
@app.route('/catalog/category/<int:category_id>/JSON')
def categoryJSON(category_id):
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Item=[i.serialize for i in items])


# Main Catalog page
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    categories = session.query(Category).all()
    return render_template('catalog.html', categories=categories,
                           login_session=login_session)
    # return "Whole catalog here"


# Create new category
@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    categories = session.query(Category).all()
    if 'username' in login_session:
        if request.method == 'POST':
            newCategory = Category(name=request.form['name'])
            session.add(newCategory)
            session.commit()
            return redirect(url_for('showCatalog'))
        return render_template('newcategory.html', categories=categories,
                               login_session=login_session)
    else:
        return redirect(url_for('showLogin'))


# Edit category
@app.route('/category/<int:category_id>/edit/', methods=['POST', 'GET'])
def editCategory(category_id):
    categories = session.query(Category).all()
    editedCat = session.query(Category).filter_by(id=category_id).one()
    if 'username' in login_session:
        if request.method == 'POST':
            editedCat.name = request.form['name']
            session.add(editedCat)
            session.commit()
            return redirect(url_for('showCatalog'))
        else:
            return render_template('editcategory.html',
                                   category_id=category_id, category=editedCat,
                                   categories=categories,
                                   login_session=login_session)
        return "Edit category {} here".format(category_id)
    else:
        return redirect(url_for('showLogin'))


# Delete category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    categories = session.query(Category).all()
    deleteItems = session.query(Item).filter_by(category_id=category_id).all()
    deletedCat = session.query(Category).filter_by(id=category_id).one()
    if 'username' in login_session:
        if request.method == "POST":
            # remove items in category as well
            for item in deleteItems:
                session.delete(item)
            session.delete(deletedCat)
            session.commit()
            return redirect(url_for('showCatalog'))
        else:
            return render_template('deletecategory.html',
                                   category_id=category_id,
                                   category=deletedCat,
                                   categories=categories,
                                   login_session=login_session)
    else:
        return redirect(url_for('showLogin'))


# Display category
@app.route('/category/<int:category_id>/')
def showCategory(category_id):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id)
    return render_template('showcategory.html', category=category,
                           items=items, categories=categories,
                           login_session=login_session)


# Create new item
@app.route('/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
def newItem(category_id):
    categories = session.query(Category).all()
    if 'username' in login_session:
        if request.method == "POST":
            newItem = Item(name=request.form['name'],
                           description=request.form['description'],
                           category_id=category_id)
            session.add(newItem)
            session.commit()
            return redirect(url_for('showCategory', category_id=category_id))
        else:
            return render_template('newitem.html', category_id=category_id,
                                   categories=categories,
                                   login_session=login_session)

        return 'Create new item here'
        app.secret_key = 'super_secret_key'
    else:
        return redirect(url_for('showLogin'))


# Edit item
@app.route('/category/<int:category_id>/item/<int:item_id>/edit',
           methods=['POST', 'GET'])
def editItem(item_id, category_id):
    categories = session.query(Category).all()
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if 'username' in login_session:
        if request.method == "POST":
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']
            session.add(editedItem)
            session.commit()
            return redirect(url_for('showCategory', category_id=category_id))
        else:
            return render_template('edititem.html', category_id=category_id,
                                   item=editedItem, categories=categories,
                                   login_session=login_session)
    else:
        return redirect(url_for('showLogin'))


# Delete item
@app.route('/category/<int:category_id>/item/<int:item_id>/delete',
           methods=['POST', 'GET'])
def deleteItem(item_id, category_id):
    deletedItem = session.query(Item).filter_by(id=item_id).one()
    categories = session.query(Category).all()
    if 'username' in login_session:
        if request.method == "POST":
            session.delete(deletedItem)
            session.commit()
            return redirect(url_for('showCategory', category_id=category_id))
        else:
            return render_template('deleteitem.html', category_id=category_id,
                                   item=deletedItem, categories=categories,
                                   login_session=login_session)
    else:
        return redirect(url_for('showLogin'))


# Show item
@app.route('/category/<int:category_id>/item/<int:item_id>/')
def showItem(item_id, category_id):
    categories = session.query(Category).all()
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('showitem.html', category_id=category_id,
                           item=item, categories=categories,
                           login_session=login_session)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
