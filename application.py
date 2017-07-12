from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

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
    deletedCat = session.query(Category).filter_by(id=category_id).one()
    if request.method == "POST":
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
@app.route('/category/<int:category_id>/item/new/')
def newItem(category_id):
    return 'Create new item here'

#Edit item
@app.route('/category/<int:category_id>/item/<int:item_id>/edit')
def editItem(item_id):
    return 'Editing {}'.format(item_id)

#Delete item
@app.route('/category/<int:category_id>/item/<int:item_id>/delete')
def deleteItem(item_id):
    return 'Deleting {}'.format(item_id)

#Show item
@app.route('/category/<int:category_id>/item/<int:item_id>/')
def showItem(item_id):
    return 'Showing {}'.format(item_id)

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)