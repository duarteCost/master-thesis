import datetime

from mongoengine import *
from werkzeug.security import generate_password_hash


class Ob_account(Document):

    email = EmailField(unique=True, max_length=200, required=True)
    password = StringField(max_length=200, required=True)
    username = StringField(max_length=200, required=True)
    user_id = ObjectIdField(max_length=200, required=True)
    modifiedAt = DateTimeField(default=datetime.datetime.now())

    def __init__(self, ob_account_id, email, password, username, user_id, *args, **values):
        super().__init__(*args, **values)
        self.id = ob_account_id
        self.email = email
        self.password = password #add hash in future
        self.username = username
        self.user_id = user_id
