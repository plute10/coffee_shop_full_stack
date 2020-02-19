import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

PERMISSION_GET = 'get:drinks-detail'
PERMISSION_CREATE = 'post:drinks'
PERMISSION_UPDATE = 'patch:drinks'
PERMISSION_DELETE = 'delete:drinks'

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

## ROUTES

def get_array_short(drinks):
    arr = []
    for one in drinks:
        arr.append(one.short())
    return arr

def get_array(drinks):
    arr = []
    for one in drinks:
        arr.append(one.long())
    return arr

def get_drink(id):
    drink = Drink.query.filter_by(id=id).one_or_none()
    if drink is None:
        abort(404, 'Check the drink id.')
    return drink

def get_validated_body():
    title = request.get_json().get('title')
    recipes = request.get_json().get('recipe')

    if title is None or recipes is None:
        abort(400, "Wrong request body.")

    for recipe in recipes:
        if 'color' not in recipe or 'name' not in recipe or 'parts' not in recipe:
            abort(400, "Request body should contain name, color, parts fields.")
    return title, recipes

@app.route('/drinks')
def get_drinks():
    return jsonify({
                    "success": True,
                    "drinks": get_array_short(Drink.query.all())
                    }), 200

@app.route('/drinks-detail')
@requires_auth(PERMISSION_GET)
def get_drinks_detail(payload):
    return jsonify({
                    "success": True,
                    "drinks": get_array(Drink.query.all())
                    }), 200

@app.route('/drinks', methods=['POST'])
@requires_auth(PERMISSION_CREATE)
def create_drink(payload):
    title, recipe = get_validated_body()
    drinks = Drink.query.filter_by(title=title).one_or_none()
    if drinks is not None:
        abort(400, "The title must be unique.")
    try:
        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()
    except Exception:
        abort(500, "Internal Error")
    return jsonify({
                    "success": True,
                    "drink": drink.long()
                    }), 200

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth(PERMISSION_UPDATE)
def update_drink(payload, id):
    title = request.get_json().get('title')
    recipes = request.get_json().get('recipe')
    drink = get_drink(id)

    if title is None and recipes is None:
        abort(400, "Wrong request body.")

    if recipes is not None:
        for recipe in recipes:
            if 'color' not in recipe or 'name' not in recipe or 'parts' not in recipe:
                abort(400, "Request body should contain name, color, parts fields.")

    try:
        if title is not None:
            drink.title = title
        if recipes is not None:
            drink.recipe = json.dumps(recipes)
        drink.update()
    except Exception:
        abort(500, "Internal Error")
    return jsonify({
                    "success": True,
                    "drink": drink.long()
                    }), 200

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth(PERMISSION_DELETE)
def delete_drink(payload, id):
    drink = get_drink(id)

    try:
        drink.delete()
    except Exception:
        abort(500, "Internal Error")
    return jsonify({
                    "success": True,
                    "delete": id
                    }), 200

## Error Handling
@app.errorhandler(400)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 400,
                    "message": str(error)
                    }), 400

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 422,
                    "message": "Unprocessable"
                    }), 422

@app.errorhandler(404)
def notfond(error):
    return jsonify({
                    "success": False,
                    "error": 404,
                    "message": 'Not Found'
                    }), 404

@app.errorhandler(500)
def internal(error):
    return jsonify({
                    "success": False,
                    "error": 500,
                    "message": str(error)
                    }), 500
