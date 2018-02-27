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
CONSUMER_KEY = config['OB']['CONSUMER_KEY']
API_VERSION = config['OB']['API_VERSION']


# decorator's
def Authorization(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        response_bytes = requests.get('https://'+AUTH_HOST_IP+':5000/authorization', headers={'Authorization': token},verify=False).content #Verifies in Auth_Service if the token is valid and returns the payload(user_id)
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


# def DirectLogin(f):
#     @wraps(f)
#     def wrapper(*args, **kwargs):
#         payload = kwargs['payload'];
#         try:
#             user_ob_account = mongodb.find_one({'user_id': ObjectId(payload)})
#             print(user_ob_account)
#             if user_ob_account is None:
#                 return Response(json_util.dumps(
#                     {'response': 'You have not registered your open bank account yet on our platform.'}),
#                                 status=500, mimetype='application/json')
#             else:
#                 # http call the open bank server to get the token
#                 response = requests.post(OB_API_HOST + '/my/logins/direct',
#                                          headers={
#                                              'Authorization': 'DirectLogin username=' + user_ob_account[
#                                                  'username'] + ', password=' + user_ob_account[
#                                                                   'password'] + ', consumer_key=' + CONSUMER_KEY,
#                                              'Content-Type': 'application/json'}).content
#
#                 token = json.loads(response.decode('utf-8'))
#                 dl_token = token['token']
#                 dl_token = "DirectLogin token=" + dl_token
#                 kwargs['user_ob_token'] = dl_token
#         except errors.ServerSelectionTimeoutError:
#             return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=500,
#                             mimetype='application/json')
#         return f(*args, **kwargs)
#     return wrapper


def OB_Authorization(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        payload = kwargs['payload']; # The payload represents the user id, getted from authentication header of the user
        try:
            user_ob_account = mongodb.find_one({'user_id': ObjectId(payload)})
            if user_ob_account is None:
                return Response(json_util.dumps(
                    {'response': 'You have not registered your open bank account yet on our platform.'}),
                                status=400, mimetype='application/json')
            else:
                # If the user has associated on open bank, your authorization is obtained from db
                raw_token = user_ob_account['ob_token']
                dl_token = "DirectLogin token=" + raw_token
                print(dl_token)
                kwargs['user_ob_token'] = dl_token #save direct login token in kwargs array
        except errors.ServerSelectionTimeoutError:
            return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=404,
                            mimetype='application/json')
        return f(*args, **kwargs)
    return wrapper

def set_baseurl_apiversion():
    obp.setBaseUrl(OB_API_HOST)
    obp.setApiVersion(API_VERSION)


def get_bank_and_account(dl_token):
    user = obp.getCurrentUser(dl_token)
    print(user)

    # --------------------------- 2º fase --------------------------------------------------------------------
    data = obp.all_accounts(dl_token)
    print(data)
    our_bank = data[0]['our_bank']
    print(our_bank)
    our_account = data[0]['our_account']
    print(our_account)
    # --------------------------------------------------------------------------------------------------------
    data = {'our_bank':our_bank, 'our_account': our_account}
    return data


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
    "host": "https://localhost:5002",
    "basePath": "Nearsoft/PSP/PSD2",  # base bash for blueprint registration
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



@app.route('/ob/associate', methods=['POST'])
@Authorization
@swag_from('API_Definitions/ob_associate.yml')
# Handler for HTTP Post - "/ob/register"
def create_user(**kwargs):
    payload = kwargs['payload'];   #user id
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
    elif request_params['password'] !=  request_params['confirm-password']:
        return Response(json_util.dumps({'response': 'Passwords does not match'}), status=400,
                        mimetype='application/json')

    username = request_params['username']
    password = request_params['password']

    try:
        #Obtain authorization to use the psd2 routes for that user
        response = requests.post(OB_API_HOST + '/my/logins/direct',
                                 headers={
                                     'Authorization': 'DirectLogin username='+username+', password='+password+', consumer_key='+CONSUMER_KEY,
                                     'Content-Type': 'application/json'}).content

    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        return Response(json_util.dumps({'response': 'Server timeout, impossible to test credentials. Try signing up later.'}), status=404,
                        mimetype='application/json')
    except requests.exceptions.TooManyRedirects:
        # Tell the user their URL was bad and try a different one
        return Response(json_util.dumps({'response': 'Impossible to find url, impossible to test credentials. Try signing up later.'}), status=400,
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
            mongoengine.connect(db='PISP_OB_UserDB', host='localhost', port=27017)
            #future work, implementation of email confirmation mecanisme

            Ob_account(ObjectId(), ob_token, ObjectId(payload)).save() # Save authorization for that user
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


#get current user from User_service data through do OB_Service

@app.route('/ob/my/account', methods=['GET'])
@Authorization
@swag_from('API_Definitions/ob_get_user.yml')
# Handler for HTTP GET - "/user/current-user"
def get_current_ob_user(**kwargs):
    payload = kwargs['payload'];  # user id
    token = kwargs['token'];
    try:
        #Get the open bank user from OB_Service
        user_ob_account = mongodb.find_one({'user_id': ObjectId(payload)})
        if user_ob_account is None:
            return Response(json_util.dumps({'response': 'No user found'}),
                            status=404, mimetype='application/json')
        else:
            #Get other user credentials from the User_Service
            response_bytes = requests.get('https://' + USER_HOST_IP + ':5001/user/my/account',
                                          headers={'Authorization': token}, verify=False).content
            response = json.loads(response_bytes.decode("utf-8"))
            print(response)
            return Response(json_util.dumps({"response":response}), status=200,
                            mimetype='application/json')
    except errors.ServerSelectionTimeoutError:
        return Response(json_util.dumps({'response': 'Mongodb is not running'}), status=500,
                        mimetype='application/json')





# ob routes, this routes correspond to the payment using PSD2

#This route gets the transaction fee
@app.route('/ob/payment/charge', methods=['GET'])
@Authorization
@OB_Authorization
@swag_from('API_Definitions/ob_payment_charge.yml')
def get_charge(**kwargs):

    dl_token = kwargs['user_ob_token'] # Get the user authorization given by the open bank

    set_baseurl_apiversion() #Fill the API url and version with config file data
    data = get_bank_and_account(dl_token) #Get the one of the user accounts in one bank of the user banks
    our_bank = data['our_bank']
    our_account = data['our_account']

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
    request_params = request.form
    print(request_params)
    if 'currency' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: currency'}), status=404,
                        mimetype='application/json')
    elif 'amount' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: amount'}), status=404,
                        mimetype='application/json')

    # merchant bank details - hard coded
    cp_bank = "psd201-bank-x--uk"
    cp_account = "2018"


    OUR_CURRENCY = request_params['currency']
    OUR_VALUE_LARGE = request_params['amount']
    obp.setPaymentDetails(OUR_CURRENCY, OUR_VALUE_LARGE)


    dl_token = kwargs['user_ob_token'] #Get the user authorization given by the open bank
    set_baseurl_apiversion() #Fill the API url and version with config file data
    data = get_bank_and_account(dl_token)#Get the one of the user accounts in one bank of the user banks
    our_bank = data['our_bank']
    our_account = data['our_account']


    challenge_types = obp.getChallengeTypes(our_bank, our_account, dl_token) #use default sandbox_tan
    challenge_type = challenge_types[0]['type']#only exists the first

    initiate_response = obp.initiateTransactionRequest(our_bank, our_account, challenge_type, cp_bank, cp_account,dl_token) #See Lib
    print(initiate_response)
    if "error" in initiate_response:
        return Response(json_util.dumps({'response': 'Got an error: ' + str(initiate_response)}), status=404,
                        mimetype='application/json')

    return Response(json_util.dumps({'response': initiate_response}), status=200,
                    mimetype='application/json')




#In case the transaction is not completed (if the amount is greater than x) it is necessary to respond to a challange
@app.route('/ob/payment/answer-challenge', methods=['POST'])
@Authorization
@OB_Authorization
@swag_from('API_Definitions/ob_answer_challenge.yml')
def payment_answer_challenge(**kwargs):
    request_params = request.form
    print(request_params) #body of route
    if 'transaction_req_id' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: transaction_req_id'}), status=404,
                        mimetype='application/json')
    elif 'challenge_query' not in request_params:
        return Response(json_util.dumps({'response': 'Missing parameter: challenge_query'}), status=404,
                        mimetype='application/json')

    transaction_req_id = request_params['transaction_req_id']
    challenge_query = request_params['challenge_query']

    dl_token = kwargs['user_ob_token'] #Get the user authorization given by the open bank
    set_baseurl_apiversion() #Fill the API url and version with config file data
    data = get_bank_and_account(dl_token)#Get the one of the user accounts in one bank of the user banks
    our_bank = data['our_bank']
    our_account = data['our_account']

    challenge_response = obp.answerChallenge(our_bank, our_account, transaction_req_id, challenge_query, dl_token)#See Lib
    if "error" in challenge_response:
        return Response(json_util.dumps({'response': 'Got an error: ' + str(challenge_response)}), status=404,
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