import os
import time

import bson
import mongoengine
import requests
import ssl
import Role_Lib.role_lib
from functools import wraps
from bson import ObjectId, json_util
from flask import Flask, request, Response, json
from flask_cors import CORS
from pymongo import MongoClient, errors
from Role_Models.role_model import Role
from flasgger import Swagger
from flasgger import swag_from
from werkzeug.security import check_password_hash

role_lib = Role_Lib.role_lib
mongobd_role = MongoClient('localhost', 27017).Role.role
time.sleep(5)
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

with open('config.json', 'r') as f:
    config = json.load(f)

AUTH_HOST_IP = config['DEFAULT']['AUTH_HOST_IP']
USER_HOST_IP = config['DEFAULT']['USER_HOST_IP']
ROLE_HOST_IP = config['DEFAULT']['ROLE_HOST_IP']


#decorator
def Authorization(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
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

def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            print(request.headers.get('Role_authorization'))
            role_authorization = request.headers.get('Role_authorization')
            if role_authorization is None:
                user_id = kwargs['payload']
                error = True
                roles_all = role_lib.get_roles(mongobd_role)  # Get all roles
                if 'roles' in roles_all:
                    user_roles_name = role_lib.user_roles(roles_all, user_id)  # Get the name of all user roles
                elif 'No roles found' in roles_all:
                    print('No roles found')
                else:
                    print('Mongodb is not running')
                print(roles)
                for user_role in user_roles_name:  # Verify if user have a specific role
                    if user_role in roles:
                        error = False
                        break

                if (error == True):
                    return Response(
                        json_util.dumps({'response': 'You do not have the permissions of this role: ' + str(roles)}),
                        status=404,
                        mimetype='application/json')
            elif(check_password_hash(role_authorization, "tese2018") is False):
                return Response(
                    json_util.dumps({'response': 'You do not have the permissions of this roles: ' + str(roles)}),
                    status=404,
                    mimetype='application/json')

            return f(*args, **kwargs)
        return wrapped
    return wrapper



app = Flask(__name__)
CORS(app)
app.config['SWAGGER'] = {
    'title': 'Nearsoft Payment Provider (Role API)',
    'description': 'This is Role API of Nearsoft Payment Provider',
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
def verify_db():
    roles = mongobd_role.find({})
    if roles.count() == 0:
        mongoengine.connect(db='Role', host='localhost', port=27017)
        Role(ObjectId(), "merchant", "Merchant role").save()
        Role(ObjectId(), "customer", "Costumer role").save()

@app.route('/', methods=['GET'])
def welcome_role():
    return Response(json_util.dumps({'response': 'Welcome Role Micro Service'}), status=200,
                    mimetype='application/json')

# Return all user roles
@app.route('/role/user/<user_id>', methods = ['GET'])
@Authorization
@swag_from('API_Definitions/role_get_user_role.yml')
def get_current_user_role(user_id, **kwargs):
    roles = role_lib.get_roles(mongobd_role)
    if 'roles' in roles:
        user_roles_name = role_lib.user_roles(roles, user_id)
        return Response(json_util.dumps({'roles': user_roles_name}), status=200,
                        mimetype='application/json')
    elif 'No roles found' in roles:
        return Response(json_util.dumps({'response': 'No roles found'}),
                        status=400, mimetype='application/json')
    else:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}),
                        status=404, mimetype='application/json')



@app.route('/role/all', methods=['GET'])
@Authorization
@swag_from('API_Definitions/role_get_all.yml')
def get_all_role(**kwargs):
    roles = role_lib.get_roles(mongobd_role)
    if 'roles' in roles:
        return Response(json_util.dumps(roles), status=200,
                        mimetype='application/json')
    elif 'No roles found' in roles:
        return Response(json_util.dumps({'response': 'No roles found'}),
                        status=400, mimetype='application/json')
    else:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}),
                        status=404, mimetype='application/json')






@app.route('/role/<role_name>', methods=['GET'])
@Authorization
@swag_from('API_Definitions/role_get_role.yml')
def get_role(role_name, **kwargs):
    print(role_name)
    try:
        roles = mongobd_role.find({'name': str(role_name)})
        if roles is None:
            return Response(json_util.dumps({'response': 'No roles found'}),
                            status=400, mimetype='application/json')
        else:
            return Response(json_util.dumps(roles), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')

@app.route('/role', methods=['POST'])
@Authorization
@swag_from('API_Definitions/role_post_role.yml')
def create_role(**kwargs):
    request_params = request.form
    print(request_params)
    if 'name' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: name'}), status=400,
                        mimetype='application/json')
    elif 'description' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: surname'}), status=400,
                        mimetype='application/json')

    name = request_params['name']
    description = request_params['description']

    try:
        mongoengine.connect(db='Role', host='localhost', port=27017)
        Role(ObjectId(), name, description).save()
        return Response(json_util.dumps({'response': 'Successful operation'}),
                        status=200, mimetype='application/json')
    except (errors.DuplicateKeyError, mongoengine.errors.NotUniqueError):
        return Response(json_util.dumps({'response': 'Role already exists'}),
                        status=400, mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')


@app.route('/role/<role_name>/permissions/user/<user_id>', methods=['POST'])
@Authorization
@requires_roles('merchant')
@swag_from('API_Definitions/role_post_user_permissions.yml')
def add_permissions(role_name, user_id, **kwargs):
    first_authorization = request.headers.get('First_authorization')
    print(first_authorization)
    if bson.objectid.ObjectId.is_valid(user_id) == False:
        return Response(json_util.dumps({'response': 'The user_id is not have correct format.'}),
                        status=200, mimetype='application/json')
    else:
        try:
            # future work, implementation of email confirmation mecanisme
            role = mongobd_role.find_one_and_update({'name': role_name},
                                             {'$push' : {'users': ObjectId(user_id)}})
            print(role)
            if role is None:
                return Response(json_util.dumps({'response': 'The role does not exist or is incorrect.'}),
                                status=200, mimetype='application/json')
            else:
                return Response(json_util.dumps({'response': 'Role added successfully.'}),
                                status=200, mimetype='application/json')
        except errors.ServerSelectionTimeoutError:
            return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                            mimetype='application/json')



if __name__ == '__main__':
    context.load_cert_chain('./Certificates/ssl.crt', './Certificates/ssl.key')
    requests.packages.urllib3.disable_warnings()
    port = int(os.environ.get('PORT', 5005))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=context)