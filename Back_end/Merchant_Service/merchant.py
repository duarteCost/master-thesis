import os
import time

import binascii
import requests
import ssl
import mongoengine
from functools import wraps
from bson import json_util, ObjectId
from flask import Flask, request, Response, json
from flask_cors import CORS
from pymongo import MongoClient, errors
from flasgger import swag_from
from flasgger import Swagger
import logging
from logging.handlers import RotatingFileHandler
from Merchant_Models.merchant_account import ReceiverAccount
from Merchant_Models.merchant_account import Merchant

# data from configuration file
with open('config.json', 'r') as f:
    config = json.load(f)

AUTH_HOST_IP = config['DEFAULT']['AUTH_HOST_IP']
USER_HOST_IP = config['DEFAULT']['USER_HOST_IP']
ROLE_HOST_IP = config['DEFAULT']['ROLE_HOST_IP']
TRANSACTION_RECORD_HOST_IP = config['DEFAULT']['TRANSACTION_RECORD_HOST_IP']
OB_API_HOST = config['OB']['OB_API_HOST']
API_VERSION = config['OB']['API_VERSION']
USERNAME = config['DB']['USERNAME']
PASSWORD = config['DB']['PASSWORD']
AUTHSOURCE = config['DB']['AUTHSOURCE']

client = MongoClient('localhost',
                      username=USERNAME,
                      password=PASSWORD,
                      authSource=AUTHSOURCE,
                      authMechanism='SCRAM-SHA-1')

mongodb = client.Merchant.merchant
time.sleep(5)

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)



# decorator's
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

def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_id = kwargs['payload']
            token = request.headers.get('Authorization')
            error = True

            try:
                response_user_roles_bytes = requests.get('https://' + ROLE_HOST_IP + ':5005/role/user/'+user_id,
                                              headers={'Authorization': token},
                                              verify=False).content  # Get user Roles in Role server

                user_roles = json.loads(response_user_roles_bytes.decode('utf-8'))
                if 'roles' in user_roles:  # Exist roles for that user
                    print(roles)
                    print(user_roles)
                    user_roles = user_roles['roles']
                    for user_role in user_roles:  # Verify if user have a specific role
                        print(user_role)
                        if user_role in roles:
                            error = False
                            break
                elif 'No roles found' in user_roles:
                    print('No roles found for that user!')
                else:
                    print('Mongodb is not running')
                print(roles)

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

            if (error == True):
                return Response(
                    json_util.dumps({'response': 'You do not have the permissions of this role: ' + str(roles[0])}),
                    status=404,
                    mimetype='application/json')

            return f(*args, **kwargs)
        return wrapped
    return wrapper

def get_receiver_account_method():
    try:
        payment_account = mongodb.find_one({})
        if payment_account is None:
            return  'No one destination payment bank account has been found'
        else:
            return {'account_data':payment_account}
    except errors.ServerSelectionTimeoutError:
        return 'Mongodb is not running'


app = Flask(__name__)
CORS(app)
app.config['SWAGGER'] = {
    'title': 'Nearsoft Payment Provider (Merchant API)',
    'description': 'This is Merchant API of Nearsoft Payment Provider',
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



@app.route('/', methods=['GET'])
def welcome_ob():
    return Response(json_util.dumps({'response': 'Welcome Merchant Service'}), status=200,
                    mimetype='application/json')


@app.route('/merchant/<merchant_id>/account', methods=['POST'])
@Authorization
@requires_roles('admin')
@swag_from('API_Definitions/merchant_post_account.yml')
def post_merchant_account(merchant_id, **kwargs):
    request_params = request.form
    if 'brand' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: brand'}), status=400,
                        mimetype='application/json')
    elif 'email' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: email'}), status=400,
                        mimetype='application/json')
    elif 'phone' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: phone'}), status=400,
                        mimetype='application/json')
    elif 'account_id' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: account_id'}), status=400,
                        mimetype='application/json')
    elif 'bank_id' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: bank_id'}), status=400,
                        mimetype='application/json')

    brand = request_params['brand']
    email = request_params['email']
    phone = request_params['phone']
    account_id = request_params['account_id']
    bank_id = request_params['bank_id']
    key = binascii.hexlify(os.urandom(32)).decode("utf-8")

    try:
        mongoengine.connect(db='Merchant', host='localhost', port=27017, username = USERNAME, password = PASSWORD,
                        authentication_source=AUTHSOURCE, authentication_mechanism='SCRAM-SHA-1')
        receiver_account = ReceiverAccount(bank_id = bank_id, account_id = account_id)
        Merchant(ObjectId(), brand, email, phone, str(key), ObjectId(merchant_id), receiver_account).save()
        app.logger.info('/merchant/account: Merchant ' + brand + ' was created!')
        return Response(json_util.dumps({'response': 'Merchant successfully created.'}),
                        status=200, mimetype='application/json')
    except (errors.DuplicateKeyError, mongoengine.errors.NotUniqueError):
        return Response(json_util.dumps({'response': 'A user can only have one receiver bank account.'}),
                        status=400, mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')


@app.route('/merchant/receiver/account', methods=['POST'])
@Authorization
@requires_roles('merchant')
@swag_from('API_Definitions/merchant_update_receiver_account.yml')
def update_merchant_account(**kwargs):
    request_params = request.form
    user_id = kwargs['payload']  # user id
    if 'account_id' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: account_id'}), status=400,
                        mimetype='application/json')
    elif 'bank_id' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: bank_id'}), status=400,
                        mimetype='application/json')

    account_id = request_params['account_id']
    bank_id = request_params['bank_id']

    try:
        merchant = mongodb.find_one_and_update({'user_id': ObjectId(user_id)}, {'$set': {'receiver_account':
        {'bank_id': bank_id, 'account_id': account_id}}})
        if merchant is None:
            print(merchant)
            return Response(json_util.dumps({'response': 'You dont have merchant account defined'}),
                            status=400, mimetype='application/json')
        else:
            app.logger.info('/merchant/<merchant_id>/account: User ' + user_id + ' update the merchant receiver account.!')
            return Response(json_util.dumps({"response": "Receiver account updated successfully."}), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')


@app.route('/merchant/account', methods=['GET'])
@Authorization
@requires_roles('merchant')
@swag_from('API_Definitions/merchant_get_account.yml')
def get_merchant_account(**kwargs):
    user_id = kwargs['payload']  # user id
    print(user_id)
    try:
        merchant = mongodb.find({'user_id': ObjectId(user_id)})
        if merchant is None:
            return Response(json_util.dumps({'response': 'You dont have merchant account defined'}),
                            status=400, mimetype='application/json')
        else:
            app.logger.info('/merchant/<merchant_id>/account: User ' + user_id + ' check the merchant account.!')
            return Response(json_util.dumps({"response": merchant}), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')


@app.route('/merchant/account/<key>', methods=['GET'])
@Authorization
@requires_roles('customer')
@swag_from('API_Definitions/merchant_get_account_by_key.yml')
def get_merchant_by_key(key, **kwargs):
    user_id = kwargs['payload']  # user id
    try:
        merchant = mongodb.find({'key': key})
        if merchant is None:
            return Response(json_util.dumps({'response': 'You dont have merchant account defined'}),
                            status=400, mimetype='application/json')
        else:
            app.logger.info('/merchant/<merchant_id>/account: User ' + user_id + ' get receiver payment account.!')
            return Response(json_util.dumps({"response":merchant}), status=200, mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')

if __name__ == '__main__':
    handler = RotatingFileHandler('merchant.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    context.load_cert_chain('./Certificates/ssl.crt', './Certificates/ssl.key')
    requests.packages.urllib3.disable_warnings()
    port = int(os.environ.get('PORT', 5006))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=context)