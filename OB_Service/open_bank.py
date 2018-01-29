import os
from functools import wraps
import requests
from bson import ObjectId, json_util
from flask import Flask, request, Response, json
from flask_cors import CORS

with open('config.json', 'r') as f:
    config = json.load(f)

AUTH_HOST_IP = config['DEFAULT']['AUTH_HOST_IP']
USER_HOST_IP = config['DEFAULT']['USER_HOST_IP']
OB_API_HOST = config['OB']['OB_API_HOST']


#decorator
def Authorization(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        response_bytes = requests.get('http://'+AUTH_HOST_IP+':5000/authorization', headers={'Authorization': token}).content
        response = response_bytes.decode("utf-8")
        error_message = 'Invalid token.'
        if response != error_message:
            kwargs['payload'] = response
            kwargs['token'] = token
        else:
            return Response(json_util.dumps({'response': 'Invalid token! Please refresh log in.'}), status=404,
                            mimetype='application/json')
        return f(*args, **kwargs)
    return wrapper


app = Flask(__name__)
CORS(app)

@app.route('/ob/get_auth', methods=['POST'])
@Authorization
def get_ob_auth(**kwargs):
    payload = kwargs['payload'];
    try:
        response = requests.get('http://'+USER_HOST_IP+':5001/user/'+payload, headers={'Authorization': kwargs['token']}).content
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
    user =  response.decode('utf-8');
    user_json =json.loads(user)

    #http call the open bank server to get the token
    response = requests.post('https://apisandbox.openbankproject.com/my/logins/direct',
                            headers={'Authorization': 'DirectLogin username=joao_s, password=aB-1234567, consumer_key=1j2z3vl4ok5ozkdtqld2n2w4tcivnacalqemldm1', 'Content-Type':'application/json'}).content
    return response.decode('utf-8')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)