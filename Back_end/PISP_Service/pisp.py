import os
import time
import requests
import ssl
from functools import wraps
from bson import json_util
from flask import Flask, request, Response, json
from flask_cors import CORS
from pymongo import MongoClient
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
    'title': 'Nearsoft Payment Provaider (PISP API)',
    'description': 'This is PISP API of Nearsoft Payment Provaider',
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

#This route gets the transaction fee
@app.route('/pisp/bank/<bank_id>/acount/<account_id>/charge', methods=['GET'])
@Authorization
@OB_Authorization
@swag_from('API_Definitions/pisp_charge.yml')
def get_charge(bank_id, account_id,**kwargs):
    dl_token = kwargs['user_ob_token'] # Get the user authorization given by the open bank

    set_baseurl_apiversion() #Fill the API url and version with config file data
    challenge_types = obp.getChallengeTypes(bank_id, account_id, dl_token) #See Lib
    charge = challenge_types[0]['charge']
    response = {'charge': charge}
    return Response(json_util.dumps({'response': response}), status=200,
                    mimetype='application/json')




#Initialize payment, as a result, the transaction may or may not be completed
@app.route('/pisp/bank/<bank_id>/acount/<account_id>/initiate-transaction-request', methods=['POST'])
@Authorization
@OB_Authorization
@swag_from('API_Definitions/pisp_initiate_transaction_request.yml')
def payment_initialization(bank_id, account_id,**kwargs):
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


    challenge_types = obp.getChallengeTypes(bank_id, account_id, dl_token) #use default sandbox_tan
    challenge_type = challenge_types[0]['type']#only exists the first

    initiate_response = obp.initiateTransactionRequest(bank_id, account_id, challenge_type, cp_bank, cp_account,dl_token) #See Lib
    print(initiate_response)
    if "error" in initiate_response:
        return Response(json_util.dumps({'response': 'Got an error: ' + str(initiate_response)}), status=400,
                        mimetype='application/json')

    return Response(json_util.dumps({'response': initiate_response}), status=200,
                    mimetype='application/json')




#In case the transaction is not completed (if the amount is greater than x) it is necessary to respond to a challange
@app.route('/pisp/bank/<bank_id>/acount/<account_id>/answer-challenge', methods=['POST'])
@Authorization
@OB_Authorization
@swag_from('API_Definitions/pisp_answer_challenge.yml')
def payment_answer_challenge(bank_id, account_id,**kwargs):
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


    challenge_response = obp.answerChallenge(bank_id, account_id, transaction_req_id, challenge_query, dl_token)#See Lib
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