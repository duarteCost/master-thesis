import os
import time
import mongoengine
import requests
import ssl
from functools import wraps
from bson import ObjectId, json_util
from flask import Flask, request, Response, json
from flask_cors import CORS
from pymongo import MongoClient, errors
from AISP_Models.aisp_payment_account import Bank_account
from flasgger import swag_from
from flasgger import Swagger
import logging
from logging.handlers import RotatingFileHandler

import AISP_Lib.obp
obp = AISP_Lib.obp

# data from configuration file
with open('config.json', 'r') as f:
    config = json.load(f)

AUTH_HOST_IP = config['DEFAULT']['AUTH_HOST_IP']
USER_HOST_IP = config['DEFAULT']['USER_HOST_IP']
ROLE_HOST_IP = config['DEFAULT']['ROLE_HOST_IP']
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

mongodb_bank_account = client.Aisp_db.bank_account
mongodb_transactions = client.Aisp_db.transactions
print(mongodb_bank_account)
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


def OB_Authorization(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        token = kwargs['token']
        print(token)

        try:
            response_bytes = requests.get('https://' + USER_HOST_IP + ':5001/user/account/obp/authorization',
                                          headers={'Authorization': token},
                                          verify=False).content  # Checks in User_Service whether the user is associated with the open bank
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
        response = json.loads(response)
        if response['obp_authorization'] == "NULL":
            return Response(json_util.dumps(
                {'response': 'You have not registered your open bank account yet on our platform.'}),
                status=400, mimetype='application/json')
        else:
            # If the user has associated on open bank, your authorization is obtained from db
            raw_token = response['obp_authorization']
            dl_token = "DirectLogin token=" + raw_token
            print(dl_token)
            kwargs['user_ob_token'] = dl_token  # save direct login token in kwargs array
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



#methods
def set_baseurl_apiversion():
    obp.setBaseUrl(OB_API_HOST)
    obp.setApiVersion(API_VERSION)




app = Flask(__name__)
CORS(app)
app.config['SWAGGER'] = {
    'title': 'Nearsoft Payment Provider (AISP API)',
    'description': 'This is AISP API of Nearsoft Payment Provider',
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
    return Response(json_util.dumps({'response': 'Welcome AISP Micro Service'}), status=200,
                    mimetype='application/json')



# Post default payment account
@app.route('/aisp/payment/bank/account/default', methods=['POST'])
@Authorization
@OB_Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/aisp_post_payment_bank_account_default.yml')
def post_my_default_payment_account(**kwargs):
    payload = kwargs['payload'];  # user id
    request_params = request.form
    print(request_params)
    if 'bank_id' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: bank_id'}), status=400,
                        mimetype='application/json')
    elif 'account_id' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: account_id'}), status=400,
                        mimetype='application/json')

    bank_id = request_params['bank_id']
    account_id = request_params['account_id']

    try:
        payment_account = mongodb_bank_account.find_one({'user_id': ObjectId(payload)})
        if payment_account is None:
            mongoengine.connect(db='Aisp_db', host='localhost', port=27017, username = USERNAME, password = PASSWORD,
                            authentication_source=AUTHSOURCE, authentication_mechanism='SCRAM-SHA-1')
            Bank_account(ObjectId(), bank_id, account_id, ObjectId(payload)).save()
            app.logger.info('/aisp/payment/bank/account/default: User '+payload+' define the default payment account to'
                                                    ' BANK_ID='+bank_id+' ACCOUNT_ID='+account_id+'!');
            return Response(json_util.dumps({'response': 'Successful definition your default payment account.'}),
                            status=200, mimetype='application/json')
        else:
            mongodb_bank_account.find_one_and_update({'user_id': ObjectId(payload)},
                                                 {'$set': {'bank_id': bank_id, 'account_id' : account_id}})
            app.logger.info(
                '/aisp/payment/bank/account/default: User ' + payload + ' update the default payment account to '
                                                    'BANK_ID=' + bank_id + ' ACCOUNT_ID=' + account_id + '!');
            return Response(json_util.dumps({'response': 'Successful update of your default payment account.'}),
                            status=200, mimetype='application/json')
    except (errors.DuplicateKeyError, mongoengine.errors.NotUniqueError):
        return Response(json_util.dumps({'response': 'A user can only have one default account.'}),
                        status=400, mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')


# Get default payment account
@app.route('/aisp/payment/bank/account/default', methods=['GET'])
@Authorization
@OB_Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/aisp_get_payment_bank_account_default.yml')
def get_default_payment_account(**kwargs):
    user_id = kwargs['payload']
    try:
        payment_account = mongodb_bank_account.find_one({'user_id': ObjectId(user_id)})
        if payment_account is None:
            return Response(json_util.dumps({'response': 'No default payment account has been found'}),
                            status=400, mimetype='application/json')
        else:
            print(payment_account)
            app.logger.info('/aisp/payment/bank/account/default: User ' + user_id + ' check default payment account!')
            return Response(json_util.dumps({"response": {"bank_id" :  payment_account['bank_id'],
                            "account_id" : payment_account['account_id'] }}), status=200, mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')


@app.route('/aisp/payment/bank/account/default', methods=['DELETE'])
@Authorization
@OB_Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/aisp_delete_payment_bank_account_default.yml')
def delete_default_payment_account(**kwargs):
    user_id = kwargs['payload']

    try:
        mongodb_bank_account.remove({'user_id': ObjectId(user_id)})
        app.logger.info('/aisp/payment/bank/account/default: User ' + user_id + ' delete default payment account!')
        return Response(json_util.dumps({'response': 'Default payment account successful deleted!'}),
                            status=200, mimetype='application/json')

    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                    mimetype='application/json')


# This route gets all accounts in different banks
@app.route('/aisp/bank/accounts', methods=['GET'])
@Authorization
@OB_Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/aisp_get_bank_accounts.yml')
def get_my_bank_accounts(**kwargs):
    user_id = kwargs['payload']
    set_baseurl_apiversion()
    dl_token = kwargs['user_ob_token']  # Get the user authorization given by the open bank
    banks_accounts = obp.all_accounts(dl_token)
    available_banks_accounts = []
    for bank_account in banks_accounts:
        print(bank_account)
        our_bank = bank_account['our_bank']
        our_account = bank_account['our_account']
        account_details = obp.getAccountById(our_bank, our_account, dl_token)
        available_banks_accounts.append({'bank_id': account_details['bank_id'], 'account_id': account_details['id'],
                                         'balance' : account_details['balance']})
    app.logger.info('/aisp/bank/accounts: User ' + user_id + ' check all bank accounts!')
    return Response(json_util.dumps({'response': available_banks_accounts}), status=200,
                    mimetype='application/json')



# This route return accounts with amount enough to the transaction
@app.route('/aisp/payment/bank/accounts', methods=['GET'])
@Authorization
@OB_Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/aisp_get_payment_bank_accounts.yml')
def define_avilable_accounts(**kwargs):
    user_id = kwargs['payload']
    set_baseurl_apiversion()
    print(request.args.get('amount') )
    if 'amount' not in request.args:
        return Response(json_util.dumps({'response': 'Missing parameter: amount'}), status=404,
                        mimetype='application/json')

    dl_token = kwargs['user_ob_token']  # Get the user authorization given by the open bank
    banks_accounts = obp.all_accounts(dl_token)
    available_banks_accounts = [] # Bank accounts with the amount available
    for bank_account in banks_accounts:
        print(bank_account)
        our_bank = bank_account['our_bank']  # define default ask professor
        our_account = bank_account['our_account']  # define default ask professor
        account_details = obp.getAccountById(our_bank, our_account, dl_token)
        print(account_details['balance']['amount'])
        if float(request.args.get('amount')) <= float(account_details['balance']['amount']):
            available_banks_accounts.append({'bank_id': account_details['bank_id'], 'account_id': account_details['id'],
                                         'balance' : account_details['balance']})
    print(available_banks_accounts)
    app.logger.info('/aisp/payment/bank/accounts: User ' + user_id + 'check the accounts with balance more then '+request.args.get('amount')+'!')
    return Response(json_util.dumps({'response': available_banks_accounts }), status=200,
                    mimetype='application/json')





# This route return all transactions record
@app.route('/aisp/bank/<bank_id>/account/<account_id>/transactions', methods=['GET'])
@Authorization
@OB_Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/aisp_get_transactions.yml')
def get_transactions(bank_id, account_id, **kwargs):
    user_id = kwargs['payload']
    set_baseurl_apiversion()
    dl_token = kwargs['user_ob_token']  # Get the user authorization given by the open bank
    transactions = obp.getTransactions(bank_id, account_id, dl_token)  # See Lib
    app.logger.info('/aisp/bank/<bank_id>/account/<account_id>/transactions: User ' + user_id + 'check all transaction of BANK_ID='+bank_id+' and ACCOUNT_ID='+account_id+'!');
    return Response(json_util.dumps({'response': transactions}), status=200,
                    mimetype='application/json')



if __name__ == '__main__':
    handler = RotatingFileHandler('aisp.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    context.load_cert_chain('./Certificates/ssl.crt', './Certificates/ssl.key')
    requests.packages.urllib3.disable_warnings()
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=context)