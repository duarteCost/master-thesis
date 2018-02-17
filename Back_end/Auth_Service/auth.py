import datetime
import jwt
import os
import ssl
from flask import Flask, request
from flask_cors import CORS

JWT_SECRET = 'secret'
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 120

app = Flask(__name__)
CORS(app)
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

# Receives the user id when a login is made and generates a authentication token based on user_id and expiration.
@app.route('/authentication', methods=['GET'])
def create_auth_token():
    user_id = request.headers.get('user_id')
    payload = {
        'user_id': str(user_id),
        'expiration': str(datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS))
    }
    auth_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    print(str(auth_token))
    return auth_token.decode('utf-8')

# Receives the authentication token. If token is valid or is not expired, the user_id is returned.
@app.route('/authorization', methods=['GET'])
def read_auth_token():
    auth_token = request.headers.get('Authorization')
    try:
        payload = jwt.decode(auth_token, JWT_SECRET, algorithm=JWT_ALGORITHM)
        print(str(payload['user_id']))
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return 'Invalid token.'
    except jwt.InvalidTokenError:
        return 'Invalid token.'

if __name__ == '__main__':
    context.load_cert_chain('./Certificates/ssl.crt', './Certificates/ssl.key')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, ssl_context=context)