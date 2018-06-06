import os
import time
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
import PISP_Lib.obp
obp = PISP_Lib.obp

# data from configuration file
with open('config.json', 'r') as f:
    config = json.load(f)

AUTH_HOST_IP = config['DEFAULT']['AUTH_HOST_IP']
USER_HOST_IP = config['DEFAULT']['USER_HOST_IP']
ROLE_HOST_IP = config['DEFAULT']['ROLE_HOST_IP']
TRANSACTION_RECORD_HOST_IP = config['DEFAULT']['TRANSACTION_RECORD_HOST_IP']
MERCHANT_HOST_IP = config['DEFAULT']['MERCHANT_HOST_IP']
OB_API_HOST = config['OB']['OB_API_HOST']
API_VERSION = config['OB']['API_VERSION']
USERNAME = config['DB']['USERNAME']
PASSWORD = config['DB']['PASSWORD']
AUTHSOURCE = config['DB']['AUTHSOURCE']

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
                        if user_role in roles:
                            error = False
                            break
                elif 'No roles found' in user_roles:
                    print('No roles found for that user!')
                else:
                    print('Mongodb is not running')

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
            sys.exit(1)

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


def set_baseurl_apiversion():
    obp.setBaseUrl(OB_API_HOST)
    obp.setApiVersion(API_VERSION)


def get_merchant(key, token):
    try:
        merchant_bytes = requests.get('https://' + MERCHANT_HOST_IP + ':5006/merchant/account/'+ key ,
                                      headers={'Authorization': token},
                                      verify=False).content
    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        return Response(json_util.dumps({'response': 'Merchant micro service timeout.'}), status=404,
                        mimetype='application/json')
    except requests.exceptions.TooManyRedirects:
        # Tell the user their URL was bad and try a different one
        return Response(json_util.dumps({'response': 'Impossible to find url of Merchant micro service.'}), status=404,
                        mimetype='application/json')
    except requests.exceptions.RequestException as err:
        # catastrophic error. bail.
        return Response(json_util.dumps({'response': str(err)}), status=404,
                        mimetype='application/json')

    return merchant_bytes.decode("utf-8")


def save_transaction_record(bank_id, account_id, OUR_VALUE, OUR_CURRENCY, description, status, token, merchant):
    # save transaction record on Transaction record micro service
    try:
        transaction_data = {'amount': OUR_VALUE, 'currency': OUR_CURRENCY, 'description': description,
                            'status': status, 'merchant':merchant};
        requests.post(
            'https://' + TRANSACTION_RECORD_HOST_IP + ':5004/transactions_record/bank/' + bank_id + '/account/' + account_id + '/transactions',
            headers={'Authorization': token}, data=transaction_data,
            verify=False)  # Verifies in Auth_Service if the token is valid and returns the payload(user_id)
    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        return Response(json_util.dumps({'response': 'Transactions record microservice timeout.'}), status=404,
                        mimetype='application/json')
    except requests.exceptions.TooManyRedirects:
        # Tell the user their URL was bad and try a different one
        return Response(json_util.dumps({'response': 'Impossible to find url of transactions record microservice.'}),
                        status=404,
                        mimetype='application/json')
    except requests.exceptions.RequestException as err:
        # catastrophic error. bail.
        return Response(json_util.dumps({'response': str(err)}), status=404,
                        mimetype='application/json')
        # end of save transaction record

app = Flask(__name__)
CORS(app)
app.config['SWAGGER'] = {
    'title': 'Nearsoft Payment Provider (PISP API)',
    'description': 'This is PISP API of Nearsoft Payment Provider',
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
    return Response(json_util.dumps({'response': 'Welcome PISP Service'}), status=200,
                    mimetype='application/json')

# ob routes, this routes correspond to the payment using PSD2
# This route gets the transaction fee
@app.route('/pisp/bank/<bank_id>/account/<account_id>/charge', methods=['GET'])
@Authorization
@OB_Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/pisp_get_charge.yml')
def get_charge(bank_id, account_id,**kwargs):
    user_id = kwargs['payload'];  # user id
    dl_token = kwargs['user_ob_token'] # Get the user authorization given by the open bank
    set_baseurl_apiversion() #Fill the API url and version with config file data
    challenge_types = obp.getChallengeTypes(bank_id, account_id, dl_token) #See Lib
    charge = challenge_types[0]['charge']
    response = {'charge': charge}
    app.logger.info('/pisp/bank/<bank_id>/account/<account_id>/charge: User ' + user_id + ' get the charge for BANK_ID='+bank_id+' and ACCOUNT_ID '+account_id+'!');
    return Response(json_util.dumps({'response': response}), status=200,
                    mimetype='application/json')


# Initialize payment, as a result, the transaction may or may not be completed
@app.route('/pisp/bank/<bank_id>/account/<account_id>/initiate-transaction-request', methods=['POST'])
@Authorization
@OB_Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/pisp_post_initiate_transaction_request.yml')
def payment_initialization(bank_id, account_id,**kwargs):
    user_id = kwargs['payload'];  # user id
    token = kwargs['token']
    set_baseurl_apiversion()
    merchant_key = request.args.get('merchantKey')

    request_params = request.form
    if 'currency' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: currency'}), status=400,
                        mimetype='application/json')
    elif 'amount' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: amount'}), status=400,
                        mimetype='application/json')


    if 'description' not in request_params:
        description = "Default description!"
    else:
        description = request_params['description']

    merchant = get_merchant(merchant_key, token)
    merchant_json = json.loads(merchant)
    print(merchant_json)
    merchant_json = merchant_json['response'][0]
    print(merchant_json);
    if 'receiver_account' not in merchant_json:
        return Response(json_util.dumps({'response': 'No one receiver payment bank account has been found'}),
                        status=400, mimetype='application/json')

    cp_bank = merchant_json['receiver_account']['bank_id']
    cp_account = merchant_json['receiver_account']['account_id']

    OUR_CURRENCY = request_params['currency']
    OUR_VALUE = request_params['amount']
    obp.setPaymentDetails(OUR_CURRENCY, OUR_VALUE)

    dl_token = kwargs['user_ob_token'] #Get the user authorization given by the open bank
    set_baseurl_apiversion() #Fill the API url and version with config file data

    challenge_types = obp.getChallengeTypes(bank_id, account_id, dl_token) #use default sandbox_tan
    challenge_type = challenge_types[0]['type']#only exists the first

    initiate_transaction_response = obp.initiateTransactionRequest(bank_id, account_id, challenge_type, cp_bank, cp_account,dl_token, description) #See Lib
    print(initiate_transaction_response)
    if "error" in initiate_transaction_response:
        return Response(json_util.dumps({'response': 'Got an error: ' + str(initiate_transaction_response)}), status=400,
                        mimetype='application/json')
    else:
        merchant_brand = merchant_json['brand'];
        save_transaction_record(bank_id, account_id, OUR_VALUE, OUR_CURRENCY, description, initiate_transaction_response['status'], token, merchant_brand)
        app.logger.info('/pisp/bank/<bank_id>/account/<account_id>/initiate-transaction-request: User ' + user_id + ' '
         'initiate a transaction request on BANK_ID=' + bank_id + ' and ACCOUNT_ID=' + account_id + '! '
                    'Transaction od is '+initiate_transaction_response['id']['value']+'!')
        return Response(json_util.dumps({'response': initiate_transaction_response}), status=200,
                    mimetype='application/json')


# In case the transaction is not completed (if the amount is greater than x) it is necessary to respond to a challenge
@app.route('/pisp/bank/<bank_id>/account/<account_id>/answer-challenge', methods=['POST'])
@Authorization
@OB_Authorization
@requires_roles('customer', 'admin')
@swag_from('API_Definitions/pisp_post_answer_challenge.yml')
def payment_answer_challenge(bank_id, account_id,**kwargs):
    user_id = kwargs['payload'];  # user id
    token = kwargs['token']
    set_baseurl_apiversion()
    request_params = request.form
    merchant_key = request.args.get('merchantKey')
    print(merchant_key)
    print(request_params) #body of route
    if 'transaction_req_id' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: transaction_req_id'}), status=400,
                        mimetype='application/json')
    elif 'challenge_query' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: challenge_query'}), status=400,
                        mimetype='application/json')

    transaction_req_id = request_params['transaction_req_id']
    challenge_query = request_params['challenge_query']

    dl_token = kwargs['user_ob_token'] #Get the user authorization given by the open bank
    set_baseurl_apiversion() #Fill the API url and version with config file data


    challenge_response = obp.answerChallenge(bank_id, account_id, transaction_req_id, challenge_query, dl_token)#See Lib
    if "error" in challenge_response:
        return Response(json_util.dumps({'response': 'Got an error: ' + str(challenge_response)}), status=400,
                        mimetype='application/json')

    OUR_VALUE = challenge_response['details']['value']['amount']
    OUR_CURRENCY = challenge_response['details']['value']['currency']
    description = challenge_response['details']['description']
    status = challenge_response['status']

    merchant = get_merchant(merchant_key, token)
    merchant_json = json.loads(merchant);
    merchantJson = merchant_json['response'][0]
    merchant_brand = merchantJson['brand'];
    save_transaction_record(bank_id, account_id, OUR_VALUE, OUR_CURRENCY, description,
                            status, token, merchant_brand)
    app.logger.info('/pisp/bank/<bank_id>/account/<account_id>/answer-challenge: User ' + user_id + ' '
                                'answer challenge of transaction '+transaction_req_id+'!')
    return Response(json_util.dumps({'response': challenge_response}), status=200,
                    mimetype='application/json')
# end of payment routes


if __name__ == '__main__':
    handler = RotatingFileHandler('pisp.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    context.load_cert_chain('./Certificates/ssl.crt', './Certificates/ssl.key')
    requests.packages.urllib3.disable_warnings()
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=context)