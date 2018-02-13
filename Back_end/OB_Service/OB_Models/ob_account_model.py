import datetime

from mongoengine import *
from werkzeug.security import generate_password_hash


class Ob_account(Document):

    ob_token = StringField(unique=True,max_length=500, required=True)
    user_id = ObjectIdField(max_length=200, required=True)
    modifiedAt = DateTimeField(default=datetime.datetime.now())

    def __init__(self, ob_account_id, ob_token, user_id, *args, **values):
        super().__init__(*args, **values)
        self.id = ob_account_id
        self.ob_token = ob_token
        self.user_id = user_id

