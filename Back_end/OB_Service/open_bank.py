import os
import time
import mongoengine
import requests
import ssl
import urllib3
from functools import wraps
from bson import ObjectId, json_util
from flask import Flask, request, Response, json
from flask_cors import CORS
from pymongo import MongoClient, errors
from OB_Models.ob_account_model import Ob_account
from flasgger import swag_from
from flasgger import Swagger

import Lib.obp
obp = Lib.obp

mongodb = MongoClient('localhost', 27017).PISP_OB_UserDB.ob_account
time.sleep(5)

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)


# data from configuration file
with open('config.json', 'r') as f:
    config = json.load(f)

AUTH_HOST_IP = config['DEFAULT']['AUTH_HOST_IP']
USER_HOST_IP = config['DEFAULT']['USER_HOST_IP']
OB_API_HOST = config['OB']['OB_API_HOST']
API_VERSION = config['OB']['API_VERSION']


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
            response_bytes = requests.get('https://' + USER_HOST_IP + ':5001/user/my/account/obp/authorization',
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




app = Flask(__name__)
CORS(app)
app.config['SWAGGER'] = {
    'title': 'Nearsoft Payment Provaider (PSD2 API)',
    'description': 'This is PSD2 API of Nearsoft Payment Provaider',
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
    return Response(json_util.dumps({'response': 'Welcome Open Bank Micro Service'}), status=200,
                    mimetype='application/json')




#get current user from User_service data through do OB_Service

@app.route('/ob/my/user/account', methods=['GET'])
@Authorization
@swag_from('API_Definitions/ob_my_user_account.yml')
# Handler for HTTP GET - "/user/current-user"
def get_current_ob_user(**kwargs):
    payload = kwargs['payload'];  # user id
    token = kwargs['token'];
    try:
        #Get the open bank user from OB_Service
        user_ob_account = mongodb.find_one({'user_id': ObjectId(payload)})
        if user_ob_account is None:
            return Response(json_util.dumps({'response': 'No user found'}),
                            status=400, mimetype='application/json')
        else:
            #Get other user credentials from the User_Service
            response_bytes = requests.get('https://' + USER_HOST_IP + ':5001/user/my/account',
                                          headers={'Authorization': token}, verify=False).content
            response = json.loads(response_bytes.decode("utf-8"))
            print(response)
            return Response(json_util.dumps({"response":response}), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                        mimetype='application/json')

# This route gets all accounts in different banks
@app.route('/ob/my/bank/accounts', methods=['GET'])
@Authorization
@OB_Authorization
@swag_from('API_Definitions/ob_my_bank_accounts.yml')
def get_my_bank_accounts(**kwargs):
    set_baseurl_apiversion()
    dl_token = kwargs['user_ob_token']  # Get the user authorization given by the open bank
    banks_accounts = obp.all_accounts(dl_token)
    return Response(json_util.dumps({'response': banks_accounts}), status=200,
                    mimetype='application/json')

# ob routes, this routes correspond to the payment using PSD2
#This route return accounts with amount enough to one transaction
@app.route('/ob/payment/accounts', methods=['POST'])
@Authorization
@OB_Authorization
@swag_from('API_Definitions/ob_payment_accounts.yml')
def define_avilable_accounts(**kwargs):
    set_baseurl_apiversion()
    request_params = request.form
    print(request.form)
    if 'amount' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: amount'}), status=404,
                        mimetype='application/json')

    dl_token = kwargs['user_ob_token']  # Get the user authorization given by the open bank
    banks_accounts = obp.all_accounts(dl_token)
    print(banks_accounts)
    available_banks_accounts = [] # Bank accounts with the amount available
    for bank_account in banks_accounts:
        print(bank_account)
        our_bank = bank_account['our_bank']  # define default ask professor
        our_account = bank_account['our_account']  # define default ask professor
        account_details = obp.getAccountById(our_bank, our_account, dl_token)
        if request_params['amount'] <=  account_details['balance']['amount']:
            available_banks_accounts.append({'our_bank': account_details['id'], 'our_account': account_details['bank_id'],
                                         'balance' : account_details['balance']})
    print(available_banks_accounts)
    return Response(json_util.dumps({'response': available_banks_accounts }), status=200,
                    mimetype='application/json')






#This route gets the transaction fee
@app.route('/ob/payment/charge', methods=['GET'])
@Authorization
@OB_Authorization
@swag_from('API_Definitions/ob_charge.yml')
def get_charge(**kwargs):
    dl_token = kwargs['user_ob_token'] # Get the user authorization given by the open bank

    set_baseurl_apiversion() #Fill the API url and version with config file data
    # data = get_bank_and_account(dl_token, request_params['amount']) #Get the one of the user accounts in one bank of the user banks

    our_bank = kwargs['our_bank']
    our_account = kwargs['our_account']

    challenge_types = obp.getChallengeTypes(our_bank, our_account, dl_token) #See Lib
    charge = challenge_types[0]['charge']
    response = {'charge': charge}
    return Response(json_util.dumps({'response': response}), status=200,
                    mimetype='application/json')




#Initialize payment, as a result, the transaction may or may not be completed
@app.route('/ob/payment/initiate-transaction-request', methods=['POST'])
@Authorization
@OB_Authorization
@swag_from('API_Definitions/ob_initiate_transaction_request.yml')
def payment_initialization(**kwargs):
    set_baseurl_apiversion()
    request_params = request.form
    print(request_params)
    if 'currency' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: currency'}), status=400,
                        mimetype='application/json')
    elif 'amount' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: amount'}), status=400,
                        mimetype='application/json')

    # merchant bank details - hard coded
    cp_bank = "psd201-bank-x--uk"
    cp_account = "2018"


    OUR_CURRENCY = request_params['currency']
    OUR_VALUE = request_params['amount']
    obp.setPaymentDetails(OUR_CURRENCY, OUR_VALUE)


    dl_token = kwargs['user_ob_token'] #Get the user authorization given by the open bank
    set_baseurl_apiversion() #Fill the API url and version with config file data
    # data = get_bank_and_account(dl_token, request_params['amount']) #Get the one of the user accounts in one bank of the user banks
    our_bank = kwargs['our_bank']
    our_account = kwargs['our_account']


    challenge_types = obp.getChallengeTypes(our_bank, our_account, dl_token) #use default sandbox_tan
    challenge_type = challenge_types[0]['type']#only exists the first

    initiate_response = obp.initiateTransactionRequest(our_bank, our_account, challenge_type, cp_bank, cp_account,dl_token) #See Lib
    print(initiate_response)
    if "error" in initiate_response:
        return Response(json_util.dumps({'response': 'Got an error: ' + str(initiate_response)}), status=400,
                        mimetype='application/json')

    return Response(json_util.dumps({'response': initiate_response}), status=200,
                    mimetype='application/json')




#In case the transaction is not completed (if the amount is greater than x) it is necessary to respond to a challange
@app.route('/ob/payment/answer-challenge', methods=['POST'])
@Authorization
@OB_Authorization
@swag_from('API_Definitions/ob_answer_challenge.yml')
def payment_answer_challenge(**kwargs):
    set_baseurl_apiversion()
    request_params = request.form
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
    # data = get_bank_and_account(dl_token, request_params['amount']) #Get the one of the user accounts in one bank of the user banks
    our_bank = kwargs['our_bank']
    our_account = kwargs['our_account']


    challenge_response = obp.answerChallenge(our_bank, our_account, transaction_req_id, challenge_query, dl_token)#See Lib
    if "error" in challenge_response:
        return Response(json_util.dumps({'response': 'Got an error: ' + str(challenge_response)}), status=400,
                        mimetype='application/json')


    print("Transaction status: {0}".format(challenge_response))
    return Response(json_util.dumps({'response': challenge_response}), status=200,
                    mimetype='application/json')

# end of payment routs



if __name__ == '__main__':
    context.load_cert_chain('./Certificates/ssl.crt', './Certificates/ssl.key')
    requests.packages.urllib3.disable_warnings()
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=context)