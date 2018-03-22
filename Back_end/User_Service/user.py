import os
import time
import mongoengine
import requests
import sys
import ssl
import User_Lib.user_lib
from functools import wraps
from bson import ObjectId, json_util
from flask import Flask, request, Response, json
from flask_cors import CORS
from pymongo import MongoClient, errors
from flasgger import swag_from
from werkzeug.security import check_password_hash, generate_password_hash
from flasgger import Swagger

user_lib = User_Lib.user_lib
mongobd_user = MongoClient('localhost', 27017).User_db.user
time.sleep(5)

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)


# Variables from config.json
with open('config.json', 'r') as f:
    config = json.load(f)
AUTH_HOST_IP = config['DEFAULT']['AUTH_HOST_IP']
ROLE_HOST_IP = config['DEFAULT']['ROLE_HOST_IP']
USER_HOST_IP = config['DEFAULT']['USER_HOST_IP']
OB_API_HOST = config['OB']['OB_API_HOST']
CONSUMER_KEY = config['OB']['CONSUMER_KEY']


#decorator
def Authorization(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        print("autho")
        token = request.headers.get('Authorization')

        try:
            response_bytes = requests.get('https://' + AUTH_HOST_IP + ':5000/authorization',
                                          headers={'Authorization': token},
                                          verify=False).content  # Verifies in Auth_Service if the token is valid and returns the payload(user_id)
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

        response = response_bytes.decode("utf-8")
        error_message = 'Invalid token.'
        if response != error_message:
            kwargs['payload'] = response # save the payload(user_id) in kwargs array
            kwargs['token'] = token
        else:
            return Response(json_util.dumps({'response': 'Invalid or inexistent token! Please log in.'}), status=400,
                            mimetype='application/json')
        return f(*args, **kwargs)
    return wrapper



app = Flask(__name__)
CORS(app)
app.config['SWAGGER'] = {
    'title': 'Nearsoft Payment Provider (User API)',
    'description': 'This is User API of Nearsoft Payment Provider',
    'uiversion': 2,
    'email': "duarteafonsocosta@hotmail.com"
}
swagger = Swagger(app, template={
    "info": {
        "contact": {
            "email":"duarteafonsocosta@hotmail.com",
        },
    },
    "schemes": [
        "http",
        "https",
    ],
    "securityDefinitions":{
        "JWT":{
            "description":"JWT autorization",
            "type":"apiKey",
            "name":"Authorization",
            "in":"header",
        },
    },
},)


@app.before_first_request
def verify_first_admin():  # Create first admin if db is empty
    try:
        user = mongobd_user.find({'email': "admin@admin.com"})
        if user.count() == 0:
            object_id = ObjectId()
            email = 'admin@admin.com'
            password = '123456'
            name = 'admin'
            username = 'admin'
            create_user_status = user_lib.create_user_m(object_id, email, password, name, username, None) #Create user through Lib method
            if create_user_status == 'Success':
                authentication = user_lib.authentication_function(str(object_id),AUTH_HOST_IP) # Get login token through Lib method
                if "token" in authentication:
                    print(user_lib.associate_role(authentication['token'], "merchant", object_id, ROLE_HOST_IP)) # Save user role in Role micro server through Lib method
                else:
                    print(authentication)
            else:
                print(create_user_status)

    except errors.ServerSelectionTimeoutError:
        print('Mongodb is not running')


@app.route('/user/', methods=['GET'])
def welcome_user():
    return Response(json_util.dumps({'response': 'Welcome User Micro Service'}), status=200,
                    mimetype='application/json')



@app.route('/user/register', methods=['POST'])
@swag_from('API_Definitions/user_post_register.yml')
# Handler for HTTP Post - "/user/register"
def create_user():
    request_params = request.form
    print(request_params)
    if 'name' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: name'}), status=400,
                        mimetype='application/json')
    elif 'surname' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: surname'}), status=400,
                        mimetype='application/json')
    elif 'email' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: email'}), status=400,
                        mimetype='application/json')
    elif 'password' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: password'}), status=400,
                        mimetype='application/json')
    elif 'confirm-password' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: confirm password'}), status=400,
                        mimetype='application/json')
    elif request_params['password'] !=  request_params['confirm-password']:
        return Response(json_util.dumps({'response': 'Passwords does not match'}), status=400,
                        mimetype='application/json')

    name = request_params['name']
    surname = request_params['surname']
    password = request_params['password']
    email = request_params['email']
    try:
        object_id = ObjectId()
        create_user_status = user_lib.create_user_m(object_id, email, password, name, surname, None) # Create user through Lib method
        if create_user_status == "Success":
            authentication = user_lib.authentication_function(str(object_id), AUTH_HOST_IP) # Get login token through Lib method
            if "token" in authentication:
                status = user_lib.associate_role(authentication['token'], "customer", object_id, ROLE_HOST_IP)  # Save user role in Role micro server through Lib method
                if (status == "Success"):
                    return Response(json_util.dumps({'response': 'Successful operation'}),
                                    status=200, mimetype='application/json')
                else:
                    return Response(json_util.dumps({'response': status}),
                                    status=404, mimetype='application/json')
            else:
                return Response(json_util.dumps({'response': authentication}),
                         status=404, mimetype='application/json')
        return Response(json_util.dumps({'response': create_user_status}),
                        status=404, mimetype='application/json')

    except (errors.DuplicateKeyError, mongoengine.errors.NotUniqueError):
        return Response(json_util.dumps({'response': 'User already exists'}),
                        status=400, mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')


@app.route('/user/login', methods=['POST'])
@swag_from('API_Definitions/user_post_login.yml')
# Handler for HTTP POST - "/user/login"
def login_user():
    request_params = request.form
    print(request_params)
    password = request_params['password']
    email = request_params['email']
    if 'email' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: email'}), status=400, mimetype='application'
                                                                                                        '/json')
    elif 'password' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: password'}), status=400,
                        mimetype='application/json')

    try:
        existing_user = mongobd_user.find_one({'email': email})
        if existing_user is None:
            return Response(json_util.dumps({'response': 'Invalid email.'}), status=400,
                            mimetype='application/json')
        elif check_password_hash(existing_user['password'], password) is False:
            return Response(json_util.dumps({'response': 'Invalid password.'}), status=400,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                    mimetype='application/json')
    user_id = str(existing_user['_id'])
    authentication = user_lib.authentication_function(user_id,
                                                      AUTH_HOST_IP)  # Get login token through Lib method
    if "token" in authentication:
        return Response(json_util.dumps(authentication), status=200,
                     mimetype='application/json')
    else:
        return Response(json_util.dumps({'response':authentication}), status=400,
                        mimetype='application/json')





@app.route('/user/all', methods=['GET'])
@swag_from('API_Definitions/user_get_all.yml')
# Handler for HTTP GET - "/user/all"
def get_user():
    try:
        users = mongobd_user.find({})
        if users is None:
            return Response(json_util.dumps({'response': 'No users found'}),
                            status=400, mimetype='application/json')
        else:
            return Response(json_util.dumps(users), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')





#find corrent user
@app.route('/user/my/account', methods=['GET'])
@Authorization
@swag_from('API_Definitions/user_get_account.yml')
def get_current_user(**kwargs):
    user_id = kwargs['payload']
    try:
        users = mongobd_user.find_one({'_id': ObjectId(user_id)})
        if users is None:
            return Response(json_util.dumps({'response': 'No user found'}),
                            status=400, mimetype='application/json')
        else:
            return Response(json_util.dumps(users), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')


@app.route('/user/obp/associate', methods=['POST'])
@Authorization
@swag_from('API_Definitions/user_post_obp_associate.yml')
def obp_associate_user(**kwargs):
    payload = kwargs['payload'];  # user id
    request_params = request.form
    print(request_params)
    if 'username' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: username'}), status=400,
                        mimetype='application/json')
    elif 'password' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: password'}), status=400,
                        mimetype='application/json')
    elif 'confirm-password' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: confirm password'}), status=400,
                        mimetype='application/json')
    elif request_params['password'] != request_params['confirm-password']:
        return Response(json_util.dumps({'response': 'Passwords does not match'}), status=400,
                        mimetype='application/json')

    username = request_params['username']
    password = request_params['password']

    try:
        # Obtain authorization to use the psd2 routes for that user
        response = requests.post(OB_API_HOST + '/my/logins/direct',
                                 headers={
                                     'Authorization': 'DirectLogin username=' + username + ', password=' + password + ', consumer_key=' + CONSUMER_KEY,
                                     'Content-Type': 'application/json'}).content

    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        return Response(
            json_util.dumps({'response': 'Server timeout, impossible to test credentials. Try signing up later.'}),
            status=404,
            mimetype='application/json')
    except requests.exceptions.TooManyRedirects:
        # Tell the user their URL was bad and try a different one
        return Response(json_util.dumps(
            {'response': 'Impossible to find url, impossible to test credentials. Try signing up later.'}),
                        status=400,
                        mimetype='application/json')
    except requests.exceptions.RequestException as err:
        # catastrophic error. bail.
        return Response(json_util.dumps({'response': str(err)}), status=400,
                        mimetype='application/json')
    print(response)
    response = json.loads(response.decode('utf-8'))
    if 'error' in response:
        return Response(json_util.dumps({'response': response['error']}), status=400, mimetype='application/json')

    elif 'token' in response:
        ob_token = response['token']
        print(ob_token)
        try:
            # future work, implementation of email confirmation mecanisme
            mongobd_user.find_one_and_update({'_id': ObjectId(payload)},
                                             {'$set': {'obp_authorization': ob_token}})
            return Response(json_util.dumps({'response': 'Successful registration with your open bank account.'}),
                            status=200, mimetype='application/json')
        except (errors.DuplicateKeyError, mongoengine.errors.NotUniqueError):
            return Response(json_util.dumps({'response': 'This open bank account already exists.'}),
                            status=400, mimetype='application/json')
        except errors.ServerSelectionTimeoutError:
            return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                            mimetype='application/json')

    return Response(json_util.dumps({'response': 'Same error occurred!'}), status=400,
                mimetype='application/json')



# Check if user is associated on open bank project
@app.route('/user/account/obp/authorization', methods=['GET'])
@Authorization
@swag_from('API_Definitions/user_get_obp_authorization.yml')
def get_obp_authorization(**kwargs):
    user_id = kwargs['payload']
    try:
        user = mongobd_user.find_one({'_id': ObjectId(user_id)})
        if user is None:
            return Response(json_util.dumps({'response': 'No user found'}),
                            status=400, mimetype='application/json')
        else:
            if 'obp_authorization' not in user:
                return Response(json_util.dumps({"obp_authorization" : "NULL"}), status=400,
                                mimetype='application/json')
            else:
                return Response(json_util.dumps({"obp_authorization" : user['obp_authorization']}), status=200,
                                mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')





if __name__ == '__main__':
    context.load_cert_chain('./Certificates/ssl.crt', './Certificates/ssl.key')
    requests.packages.urllib3.disable_warnings()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=context)
