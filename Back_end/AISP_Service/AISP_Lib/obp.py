import requests
from bson import json_util
from flask import json, Response


def setPaymentDetails(currency ,value):
    global OUR_CURRENCY, OUR_VALUE

    OUR_CURRENCY = currency
    OUR_VALUE =value


def setBaseUrl(u):
    global BASE_URL
    BASE_URL = u

def setApiVersion(v):
    global API_VERSION
    API_VERSION = v

def getCurrentUser(DL_TOKEN):
    # Prepare headers
    response = requests.get(u"{0}/obp/{1}/users/current".format(BASE_URL, API_VERSION), headers={'Authorization' : DL_TOKEN , 'content-type'  : 'application/json'})
    return response.json()

def getBanks(DL_TOKEN):
    # Prepare headers
    response = requests.get(u"{0}/obp/{1}/banks".format(BASE_URL, API_VERSION), headers={'Authorization' : DL_TOKEN , 'content-type'  : 'application/json'})
    return response.json()['banks']

# Get all user's private accounts
def getPrivateAccounts(bank, DL_TOKEN):
    # Prepare headers
    response = requests.get(u"{0}/obp/{1}/banks/{2}/accounts/private".format(BASE_URL, API_VERSION, bank), headers={'Authorization' : DL_TOKEN , 'content-type'  : 'application/json'})
    return response.json()['accounts']


# Get Account by Id
def getAccountById(bank, account,  DL_TOKEN):
    # Prepare headers
    response = requests.get(u"{0}/obp/{1}//my/banks/{2}/accounts/{3}/account".format(BASE_URL, API_VERSION, bank, account), headers={'Authorization' : DL_TOKEN , 'content-type'  : 'application/json'})
    return response.json()

def all_accounts(DL_TOKEN):
    # Prepare headers
    try:
        response = requests.get(u"{0}/obp/{1}/my/accounts".format(BASE_URL, API_VERSION),
                                headers={'Authorization': DL_TOKEN, 'content-type': 'application/json'}).content
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

    accounts = json.loads(response.decode("utf-8"))
    print(accounts);
    res = []
    for account in accounts['accounts']:
        res.append({'our_bank': account['bank_id'], 'our_account': account['id']})
    return res

    return response.json()['accounts']

# Get challenge types
def getChallengeTypes(bank, account, DL_TOKEN):
    response_bytes = requests.get(u"{0}/obp/{1}/banks/{2}/accounts/{3}/owner/transaction-request-types".format(BASE_URL, API_VERSION, bank, account), headers={'Authorization' : DL_TOKEN , 'content-type'  : 'application/json'}).content
    response = json.loads(response_bytes.decode("utf-8"))
    types = response['transaction_request_types']
    print(response)
    res = []
    for type in types:
      res.append({'type': type['value'], 'charge': type['charge']['value']['amount']})
    print(res)
    return res

# Answer the challenge
def answerChallenge(bank, account, transation_req_id, challenge_query, DL_TOKEN):
    body = '{"id": "' + challenge_query + '","answer": "123456"}'    #any number works in sandbox mode
    response = requests.post(u"{0}/obp/v1.4.0/banks/{1}/accounts/{2}/owner/transaction-request-types/sandbox/transaction-requests/{3}/challenge".format(
         BASE_URL, bank, account, transation_req_id), data=body, headers={'Authorization' : DL_TOKEN , 'content-type'  : 'application/json'}
    )
    return response.json()

def getTransactionRequest(bank, account, DL_TOKEN):
    response = requests.get(u"{0}/obp/{1}/banks/{2}/accounts/{3}/owner/transactions".format(BASE_URL, API_VERSION, bank, account), headers={'Authorization' : DL_TOKEN , 'content-type'  : 'application/json'})
    return response.json()

def initiateTransactionRequest(bank, account, challenge_type, cp_bank, cp_account, DL_TOKEN):
    send_to = {"bank": cp_bank, "account": cp_account}
    payload = '{"to": {"account_id": "' + send_to['account'] +'", "bank_id": "' + send_to['bank'] + \
    '"}, "value": {"currency": "' + OUR_CURRENCY + '", "amount": "' + OUR_VALUE + '"}, "description": "Description abc", "challenge_type" : "' + \
    challenge_type + '"}'
    response = requests.post(u"{0}/obp/v1.4.0/banks/{1}/accounts/{2}/owner/transaction-request-types/{3}/transaction-requests".format(BASE_URL, bank, account, challenge_type), data=payload, headers={'Authorization' : DL_TOKEN , 'content-type'  : 'application/json'})
    return response.json()


# Get owner's transactions
    # Possible custom headers for pagination:
    # sort_direction=ASC/DESC ==> default value: DESC. The sort field is the completed date.
    # limit=NUMBER ==> default value: 50
    # offset=NUMBER ==> default value: 0
    # from_date=DATE => default value: Thu Jan 01 01:00:00 CET 1970 (format below)
    # to_date=DATE => default value: 3049-01-01
def getTransactions(bank, account, DL_TOKEN):
    response = requests.get(u"{0}/obp/{1}/banks/{2}/accounts/{3}/owner/transactions".format(BASE_URL, API_VERSION, bank, account), headers={'Authorization' : DL_TOKEN , 'content-type'  : 'application/json'})
    return response.json()['transactions']
