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
from AISP_Models.aisp_payment_account import Payment_account
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
    'title': 'Nearsoft Payment Provaider (AISP API)',
    'description': 'This is AISP API of Nearsoft Payment Provaider',
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





# This route gets all accounts in different banks
@app.route('/aisp/my/bank/accounts', methods=['GET'])
@Authorization
@OB_Authorization
@swag_from('API_Definitions/aisp_my_bank_accounts.yml')
def get_my_bank_accounts(**kwargs):
    set_baseurl_apiversion()
    dl_token = kwargs['user_ob_token']  # Get the user authorization given by the open bank
    banks_accounts = obp.all_accounts(dl_token)
    return Response(json_util.dumps({'response': banks_accounts}), status=200,
                    mimetype='application/json')

# ob routes, this routes correspond to the payment using PSD2
#This route return accounts with amount enough to one transaction
@app.route('/aisp/payment/accounts', methods=['GET'])
@Authorization
@OB_Authorization
@swag_from('API_Definitions/aisp_payment_accounts.yml')
def define_avilable_accounts(**kwargs):
    set_baseurl_apiversion()
    print(request.args.get('amount') )
    if 'amount' not in request.args:
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
        if request.args['amount'] <=  account_details['balance']['amount']:
            available_banks_accounts.append({'our_bank': account_details['id'], 'our_account': account_details['bank_id'],
                                         'balance' : account_details['balance']})
    print(available_banks_accounts)
    return Response(json_util.dumps({'response': available_banks_accounts }), status=200,
                    mimetype='application/json')



if __name__ == '__main__':
    context.load_cert_chain('./Certificates/ssl.crt', './Certificates/ssl.key')
    requests.packages.urllib3.disable_warnings()
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=context)