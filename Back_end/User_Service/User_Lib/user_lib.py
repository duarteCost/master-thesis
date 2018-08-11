import mongoengine
import requests
from bson import ObjectId
from flask import json
from pymongo import MongoClient, errors
from werkzeug.security import generate_password_hash

with open('config.json', 'r') as f:
    config = json.load(f)
USERNAME = config['DB']['USERNAME']
PASSWORD = config['DB']['PASSWORD']
AUTHSOURCE = config['DB']['AUTHSOURCE']
DB_HOST_IP = config['DB']['HOST_IP']

#methods
def authentication_function(user_id, AUTH_HOST_IP):
    try:
        # http communication to generate token when user does the login
        response = requests.get('https://'+AUTH_HOST_IP+':5000/authentication', headers={'user_id': user_id }, verify=False).content
    except requests.exceptions.Timeout:
    # Maybe set up for a retry, or continue in a retry loop
        return 'Server timeout.'
    except requests.exceptions.TooManyRedirects:
    # Tell the user their URL was bad and try a different one
        return 'Impossible to find url.'
    except requests.exceptions.RequestException as err:
        # catastrophic error. bail.
        return str(err)
    token = response.decode("utf-8")
    token_response = {'token':token}
    return token_response


def create_user_m(object_id, email, password, name, surname, obp_authorization):
    try:
        print(USERNAME)
        mongoengine.connect(db='User_db', host=DB_HOST_IP, port=27017, username = USERNAME, password = PASSWORD,
                            authentication_source=AUTHSOURCE, authentication_mechanism='SCRAM-SHA-1')
        from Back_end.User_Service.User_Models.user_model import User
        User(object_id, email, password, name, surname, None).save()
        return 'Success'
    except (errors.DuplicateKeyError, mongoengine.errors.NotUniqueError):
        return 'User already exists'
    except errors.ServerSelectionTimeoutError:
        return 'Mongodb is not running'

def associate_role(token, role, user_id, ROLE_HOST_IP):
    role_authorization = "tese2018"
    role_authorization = generate_password_hash(
        role_authorization)  # Generation of authorization to create clients and first administrator. This is required because the role server needs to be closed
    try:
        # http communication to generate token when user does the login
        response = requests.post('https://' + ROLE_HOST_IP + ':5005/role/'+role+'/user/' + str(user_id),
                      headers={'Authorization': token, 'Role_authorization': role_authorization}, verify=False).content
        response_json = json.loads(response.decode("utf-8"))
        if response_json['response'] == "Role added successfully.":
            return 'Success'
        else:
            return ('Some error occurred in user role association!')
    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        return 'Server timeout.'
    except requests.exceptions.TooManyRedirects:
        # Tell the user their URL was bad and try a different one
        return 'Impossible to find url.'
    except requests.exceptions.RequestException as err:
        # catastrophic error. bail.
        return str(err)

