import os
import time
import mongoengine

from bson import ObjectId, json_util
from flask import Flask, request, Response
from flask_cors import CORS
from pymongo import MongoClient, errors
from User_Models.user_model import User
from werkzeug.security import check_password_hash

mongodb = MongoClient('localhost', 27017).PISP_UserDB.user
time.sleep(5)

app = Flask(__name__)
CORS(app)

@app.route('/user', methods=['GET'])
def welcome_user():
    return Response(json_util.dumps({'response': 'Welcome User Micro Service'}), status=200,
                    mimetype='application/json')


@app.route('/user/register', methods=['POST'])
# Handler for HTTP Post - "/user/register"
def create_user():
    request_params = request.form
    print(request_params)
    if 'name' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: name'}), status=404,
                        mimetype='application/json')
    elif 'surname' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: surname'}), status=404,
                        mimetype='application/json')
    elif 'email' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: email'}), status=404,
                        mimetype='application/json')
    elif 'password' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: password'}), status=404,
                        mimetype='application/json')
    elif 'confirm-password' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: confirm password'}), status=404,
                        mimetype='application/json')

    name = request_params['name']
    surname = request_params['surname']
    password = request_params['password']
    email = request_params['email']

    try:
        mongoengine.connect(db='PISP_UserDB', host='localhost', port=27017)
        User(ObjectId(), email, password, name, surname).save()
        return Response(json_util.dumps({'response': 'Successful operation'}),
                        status=200, mimetype='application/json')
    except (errors.DuplicateKeyError, mongoengine.errors.NotUniqueError):
        return Response(json_util.dumps({'response': 'User already exists'}),
                        status=404, mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=500,
                        mimetype='application/json')


@app.route('/user/all', methods=['GET'])
# Handler for HTTP GET - "/user/all"
def get_user():
    try:
        users = mongodb.find({})
        if users is None:
            return Response(json_util.dumps({'response': 'No users found'}),
                            status=500, mimetype='application/json')
        else:
            return Response(json_util.dumps(users), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=500,
                        mimetype='application/json')


@app.route('/user/login', methods=['POST'])
# Handler for HTTP POST - "/user/login"
def login_user():
    request_params = request.form
    print(request_params)
    if 'email' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: email'}), status=404, mimetype='application'
                                                                                                        '/json')
    elif 'password' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: password'}), status=404,
                        mimetype='application/json')

    password = request_params['password']
    email = request_params['email']

    existing_user = mongodb.find_one({'email': email})
    if existing_user is None and check_password_hash(existing_user['password'], password):
        return Response(json_util.dumps({'response': 'Invalid username/password supplied'}), status=404,
                        mimetype='application/json')
    # RPC communication to generate token when user does the login

    return Response(json_util.dumps({'response': 'Successful operation', 'token': 'to implement'}), status=200,
                    mimetype='application/json')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
