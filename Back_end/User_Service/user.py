import os
import time
import mongoengine
import requests
import sys
import ssl
from functools import wraps
from bson import ObjectId, json_util
from flask import Flask, request, Response, json
from flask_cors import CORS
from pymongo import MongoClient, errors
from User_Models.user_model import User
from werkzeug.security import check_password_hash

mongodb = MongoClient('localhost', 27017).PISP_UserDB.user
time.sleep(5)

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

with open('config.json', 'r') as f:
    config = json.load(f)

AUTH_HOST_IP = config['DEFAULT']['AUTH_HOST_IP']


#decorator
def Authorization(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        response_bytes = requests.get('https://'+AUTH_HOST_IP+':5000/authorization', headers={'Authorization': token}, verify=False).content #Verifies in Auth_Service if the token is valid and returns the payload(user_id)
        response = response_bytes.decode("utf-8")
        error_message = 'Invalid token.'
        if response != error_message:
            kwargs['payload'] = response #save the payload(user_id) in kwargs array
        else:
            return Response(json_util.dumps({'response': 'Invalid token! Please refresh log in.'}), status=404,
                            mimetype='application/json')
        return f(*args, **kwargs)
    return wrapper

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
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
    elif request_params['password'] !=  request_params['confirm-password']:
        return Response(json_util.dumps({'response': 'Passwords does not match'}), status=404,
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
    if existing_user is None:
        return Response(json_util.dumps({'response': 'Invalid email.'}), status=404,
                        mimetype='application/json')
    elif check_password_hash(existing_user['password'], password) is False:
        return Response(json_util.dumps({'response': 'Invalid password.'}), status=404,
                        mimetype='application/json')



    # http communication to generate token when user does the login
    try:
        response = requests.get('https://'+AUTH_HOST_IP+':5000/authentication', headers={'user_id': str(existing_user['_id'])}, verify=False).content
    except requests.exceptions.Timeout:
    # Maybe set up for a retry, or continue in a retry loop
        return Response(json_util.dumps({'response': 'Server timeout.'}), status=404,
                    mimetype='application/json')
    except requests.exceptions.TooManyRedirects:
    # Tell the user their URL was bad and try a different one
        return Response(json_util.dumps({'response': 'Impossible to find url.'}), status=404,
                    mimetype='application/json')
    except requests.exceptions.RequestException as err:
        # catastrophic error. bail.
        return Response(json_util.dumps({'response': str(err)}), status=404,
                        mimetype='application/json')
        sys.exit(1)
    token = response.decode("utf-8")
    return Response(json_util.dumps({'response': 'Successful operation', 'token': token}), status=200,
                    mimetype='application/json')


@app.route('/user/all', methods=['GET'])
@Authorization
# Handler for HTTP GET - "/user/all"
def get_user(**kwargs):
    print(kwargs['payload'])
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





#find corrent user
@app.route('/user/<string:user_id>', methods=['GET'])
@Authorization
# Handler for HTTP GET - "/user/all"
def get_current_user(user_id, **kwargs):
    print(kwargs['payload'])
    try:
        users = mongodb.find_one({'_id': ObjectId(user_id)})
        if users is None:
            return Response(json_util.dumps({'response': 'No user found'}),
                            status=500, mimetype='application/json')
        else:
            return Response(json_util.dumps(users), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=500,
                        mimetype='application/json')





if __name__ == '__main__':
    context.load_cert_chain('./Certificates/ssl.crt', './Certificates/ssl.key')
    requests.packages.urllib3.disable_warnings()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=context)
