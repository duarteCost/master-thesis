import os
import time

import dateutil
import mongoengine
import pymongo
import requests
import ssl
from functools import wraps
from bson import ObjectId, json_util
from flask import Flask, request, Response, json
from flask_cors import CORS
from pymongo import MongoClient, errors
from Transactions_Models.transaction_model import Transaction
from flasgger import swag_from
from flasgger import Swagger


# data from configuration file
with open('config.json', 'r') as f:
    config = json.load(f)

AUTH_HOST_IP = config['DEFAULT']['AUTH_HOST_IP']
USER_HOST_IP = config['DEFAULT']['USER_HOST_IP']
ROLE_HOST_IP = config['DEFAULT']['ROLE_HOST_IP']
USERNAME = config['DB']['USERNAME']
PASSWORD = config['DB']['PASSWORD']
AUTHSOURCE = config['DB']['AUTHSOURCE']

client = MongoClient('localhost',
                      username=USERNAME,
                      password=PASSWORD,
                      authSource=AUTHSOURCE,
                      authMechanism='SCRAM-SHA-1')

mongodb_transactions = client.Transactions_db.transaction
time.sleep(5)

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)



# decorator's
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
            sys.exit(1)

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




app = Flask(__name__)
CORS(app)
app.config['SWAGGER'] = {
    'title': 'Nearsoft Payment Provider (Transactions Record API)',
    'description': 'This is Transactions Record of Nearsoft Payment Provider',
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
    return Response(json_util.dumps({'response': 'Welcome Transactions Record Micro Service'}), status=200,
                    mimetype='application/json')


# Post transaction
@app.route('/transactions_record/bank/<bank_id>/account/<account_id>/transactions', methods=['POST'])
@Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/transaction-record_post_transaction.yml')
def post_transaction(bank_id, account_id, **kwargs):
    payload = kwargs['payload'];  # user id
    request_params = request.form
    print(request_params)
    if 'amount' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: amount'}), status=400,
                        mimetype='application/json')
    elif 'currency' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: currency'}), status=400,
                        mimetype='application/json')
    elif 'description' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: description'}), status=400,
                        mimetype='application/json')
    elif 'status' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: status'}), status=400,
                        mimetype='application/json')
    elif 'merchant' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: merchant'}), status=400,
                        mimetype='application/json')

    amount = request_params['amount']
    currency = request_params['currency']
    description = request_params['description']
    status = request_params['status']
    merchant = request_params['merchant']

    try:
        mongoengine.connect(db='Transactions_db', host='localhost', port=27017, username = USERNAME, password = PASSWORD,
                        authentication_source=AUTHSOURCE, authentication_mechanism='SCRAM-SHA-1')
        Transaction(ObjectId(), bank_id, account_id, float(amount), currency, description, status, ObjectId(payload), merchant).save()

        return Response(json_util.dumps({'response': 'Transaction record added successfully.'}),
                        status=200, mimetype='application/json')
    except (errors.DuplicateKeyError, mongoengine.errors.NotUniqueError):
        return Response(json_util.dumps({'response': 'Transaction duplicated.'}),
                        status=400, mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')


# Get bank account transaction
@app.route('/transactions_record/bank/<bank_id>/account/<account_id>/transactions', methods=['GET'])
@Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/transaction-record_get_user_transaction_by_bank_account.yml')
def get_user_transactions(bank_id, account_id, **kwargs):
    user_id = kwargs['payload']
    try:
        user_transactions = mongodb_transactions.find({'user_id': ObjectId(user_id), 'bank_id':bank_id, 'account_id':account_id}).sort("modifiedAt", -1)
        if user_transactions is None:
            return Response(json_util.dumps({'response': 'No transactions has been found for that user'}),
                            status=400, mimetype='application/json')
        else:
            return Response(json_util.dumps({"response": user_transactions}), status=200, mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')

# Get bank account transaction
@app.route('/transactions_record/search', methods=['POST'])
@Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/transaction-record_get_user_transaction_by_search.yml')
def get_user_transactions_by_account(**kwargs):
    user_id = kwargs['payload']
    query = {'user_id': ObjectId(user_id)};
    td = {}

    request_params = request.form
    if 'account_id' in request_params and request_params['account_id']!='':
        query['account_id'] = request_params['account_id']

    if 'begin_date' in request_params and request_params['begin_date']!='':
        transaction_begin_date = dateutil.parser.parse(request_params['begin_date'])
        td["$gte"] = transaction_begin_date

    if 'end_date' in request_params and request_params['end_date']!='':
        transaction_end_date = dateutil.parser.parse(request_params['end_date'])
        td["$lt"] = transaction_end_date

    if "$gte" in td or "$lt" in td:
        query['modifiedAt'] = td

    print(query)

    try:
        user_transactions = mongodb_transactions.find(query).sort("modifiedAt", -1)
        if user_transactions is None:
            return Response(json_util.dumps({'response': 'No transactions has been found for that user'}),
                            status=400, mimetype='application/json')
        else:
            return Response(json_util.dumps({"response": user_transactions}), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')

# Get user account transaction by admin
@app.route('/transactions_record/user/<user_id>/transactions', methods=['GET'])
@Authorization
@requires_roles('admin')
@swag_from('API_Definitions/transaction-record_get_user_transaction_by_admin.yml')
def get_user_transaction_by_admin(user_id, **kwargs):
    try:
        user_transactions = mongodb_transactions.find(
            {'user_id': ObjectId(user_id)}).sort("modifiedAt", -1)
        if user_transactions is None:
            return Response(json_util.dumps({'response': 'No transactions has been found for that user'}),
                            status=400, mimetype='application/json')
        else:
            return Response(json_util.dumps({"response": user_transactions}), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')

@app.route('/transactions_record/transactions', methods=['GET'])
@Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/transaction-record_get_user_transaction_by_user.yml')
def get_user_transactions_by_user(**kwargs):
    user_id = kwargs['payload']
    try:
        user_transactions = mongodb_transactions.find(
            {'user_id': ObjectId(user_id)}).sort("modifiedAt", -1)
        if user_transactions is None:
            return Response(json_util.dumps({'response': 'No transactions has been found for that user'}),
                            status=400, mimetype='application/json')
        else:
            return Response(json_util.dumps({"response": user_transactions}), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')


@app.route('/transactions_record/transactions', methods=['DELETE'])
@Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/transaction-record_delete_user_transaction_by_user.yml')
def delete_user_transactions_by_user(**kwargs):
    user_id = kwargs['payload']
    try:
        mongodb_transactions.remove({'user_id': ObjectId(user_id)})
        return Response(json_util.dumps({'response': 'Transactions successfully deleted.'}),
                            status=200, mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')


if __name__ == '__main__':
    context.load_cert_chain('./Certificates/ssl.crt', './Certificates/ssl.key')
    requests.packages.urllib3.disable_warnings()
    port = int(os.environ.get('PORT', 5004))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=context)