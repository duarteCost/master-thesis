import os
import time
import bson
import mongoengine
import requests
import ssl
import logging
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
from logging.handlers import RotatingFileHandler


with open('config.json', 'r') as f:
    config = json.load(f)

AUTH_HOST_IP = config['DEFAULT']['AUTH_HOST_IP']
USER_HOST_IP = config['DEFAULT']['USER_HOST_IP']
ROLE_HOST_IP = config['DEFAULT']['ROLE_HOST_IP']
USERNAME = config['DB']['USERNAME']
PASSWORD = config['DB']['PASSWORD']
AUTHSOURCE = config['DB']['AUTHSOURCE']

role_lib = Role_Lib.role_lib

client = MongoClient('localhost',
                      username=USERNAME,
                      password=PASSWORD,
                      authSource=AUTHSOURCE,
                      authMechanism='SCRAM-SHA-1')

mongobd_role = client.Role.role

time.sleep(5)
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)



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
                        json_util.dumps({'response': 'You do not have the permissions of this role: ' + str(roles[0])}),
                        status=404,
                        mimetype='application/json')
            elif(check_password_hash(role_authorization, "tese2018") is False):
                return Response(
                    json_util.dumps({'response': 'You do not have the permissions of this roles: ' + str(roles[0])}),
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
        mongoengine.connect(db='Role', host='localhost', port=27017, username = USERNAME, password = PASSWORD,
                            authentication_source=AUTHSOURCE, authentication_mechanism='SCRAM-SHA-1')
        Role(ObjectId(), "admin", "Admin role").save()
        Role(ObjectId(), "customer", "Customer role").save()
        Role(ObjectId(), "merchant", "Merchant role").save()

@app.route('/', methods=['GET'])
def welcome_role():
    return Response(json_util.dumps({'response': 'Welcome Role Micro Service'}), status=200,
                    mimetype='application/json')

# Return all user roles
@app.route('/role/user/<user_id>', methods = ['GET'])
@Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/role_get_user_role.yml')
def get_current_user_role(user_id, **kwargs):
    user_id_auth = kwargs['payload']  # user id
    roles = role_lib.get_roles(mongobd_role)
    if 'roles' in roles:
        user_roles_name = role_lib.user_roles(roles, user_id)
        app.logger.info('/role/user/<user_id>: User '+user_id_auth+' get all user roles for user '+user_id+'!')
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
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/role_get_all.yml')
def get_all_role(**kwargs):
    user_id = kwargs['payload'];  # user id
    roles = role_lib.get_roles(mongobd_role)
    if 'roles' in roles:
        app.logger.info('/role/all: User ' + user_id + ' get all roles!')
        return Response(json_util.dumps({'roles':roles}), status=200,
                        mimetype='application/json')
    elif 'No roles found' in roles:
        return Response(json_util.dumps({'response': 'No roles found'}),
                        status=400, mimetype='application/json')
    else:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}),
                        status=404, mimetype='application/json')






@app.route('/role/<role_name>', methods=['GET'])
@Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/role_get_role.yml')
def get_role(role_name, **kwargs):
    user_id = kwargs['payload']  # user id
    print(role_name)
    try:
        roles = mongobd_role.find({'name': str(role_name)})
        if roles is None:
            return Response(json_util.dumps({'response': 'No roles found'}),
                            status=400, mimetype='application/json')
        else:
            app.logger.info('/role/<role_name>: User ' + user_id + ' get role '+role_name+'!')
            return Response(json_util.dumps(roles), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')

@app.route('/role', methods=['POST'])
@Authorization
@requires_roles('admin')
@swag_from('API_Definitions/role_post_role.yml')
def create_role(**kwargs):
    user_id = kwargs['payload']  # user id
    request_params = request.form
    print(request_params)
    if 'name' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: name'}), status=400,
                        mimetype='application/json')
    elif 'description' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: description'}), status=400,
                        mimetype='application/json')

    name = request_params['name']
    description = request_params['description']

    try:
        mongoengine.connect(db='Role', host='localhost', port=27017, username = USERNAME, password = PASSWORD,
                            authentication_source=AUTHSOURCE, authentication_mechanism='SCRAM-SHA-1')
        Role(ObjectId(), name, description).save()
        app.logger.info('/role: User ' + user_id + ' post role ' + name + '!')
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
@requires_roles('admin')
@swag_from('API_Definitions/role_post_user_permissions.yml')
def add_permissions(role_name, user_id, **kwargs):
    user_id_auth = kwargs['payload']  # user id
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
                app.logger.info('/role/<role_name>/permissions/user/<user_id>: User ' + user_id_auth + ' add role '+role_name+' to the user ' + user_id + '!')
                return Response(json_util.dumps({'response': 'Role added successfully.'}),
                                status=200, mimetype='application/json')
        except errors.ServerSelectionTimeoutError:
            return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                            mimetype='application/json')



if __name__ == '__main__':
    handler = RotatingFileHandler('role.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    context.load_cert_chain('./Certificates/ssl.crt', './Certificates/ssl.key')
    requests.packages.urllib3.disable_warnings()
    port = int(os.environ.get('PORT', 5005))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=context)