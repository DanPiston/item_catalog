from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#API Endpoint for Catalog (GET Request)
@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(Category).all()
    return jsonify(Category=[i.serialize for i in categories])

#API Endpoint for Items in a Category (GET Requst)
@app.route('/catalog/category/<int:category_id>/JSON')
def categoryJSON(category_id):
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Item=[i.serialize for i in items])

#Main Catalog page
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    categories = session.query(Category).all()
    return render_template('catalog.html', categories = categories)
    # return "Whole catalog here"

#Create new category
@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    if request.method == 'POST':
        newCategory = Category(name = request.form['name'])
        session.add(newCategory)
        session.commit()
        return redirect(url_for('showCatalog'))
    return render_template('newcategory.html')

#Edit category
@app.route('/category/<int:category_id>/edit/', methods=['POST', 'GET'])
def editCategory(category_id):
    editedCat = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        editedCat.name = request.form['name']
        session.add(editedCat)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('editcategory.html', category_id=category_id, category=editedCat)
    return "Edit category {} here".format(category_id)

#Delete category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    deleteItems = session.query(Item).filter_by(category_id=category_id).all()
    deletedCat = session.query(Category).filter_by(id=category_id).one()
    if request.method == "POST":
        #remove items in category as well
        for item in deleteItems:
            session.delete(item)
        session.delete(deletedCat)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deletecategory.html', category_id=category_id, category = deletedCat)

#Display category
@app.route('/category/<int:category_id>/')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id)
    return render_template('showcategory.html', category=category, items=items)

#Create new item
@app.route('/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
def newItem(category_id):
    if request.method == "POST":
        newItem = Item(name = request.form['name'], description = request.form['description'], category_id=category_id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('newitem.html', category_id=category_id)

    return 'Create new item here'

#Edit item
@app.route('/category/<int:category_id>/item/<int:item_id>/edit', methods=['POST', 'GET'])
def editItem(item_id, category_id):
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == "POST":
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description=request.form['description']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('edititem.html', category_id=category_id, item=editedItem)

#Delete item
@app.route('/category/<int:category_id>/item/<int:item_id>/delete', methods=['POST', 'GET'])
def deleteItem(item_id, category_id):
    deletedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == "POST":
        session.delete(deletedItem)
        session.commit()
        return redirect(url_for('showCategory', category_id=category_id))
    else:
        return render_template('deleteitem.html', category_id=category_id, item=deletedItem)

#Show item
@app.route('/category/<int:category_id>/item/<int:item_id>/')
def showItem(item_id, category_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('showitem.html', category_id=category_id, item=item)

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)