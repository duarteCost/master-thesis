import datetime

from mongoengine import *
from werkzeug.security import generate_password_hash


class Payment_account(Document):

    bank_id = StringField(unique=True,max_length=500, required=True)
    account_id = StringField(unique=True,max_length=500, required=True)
    user_id = ObjectIdField(max_length=200, required=True)
    modifiedAt = DateTimeField(default=datetime.datetime.now())

    def __init__(self, payment_account_id, bank_id, account_id, user_id, *args, **values):
        super().__init__(*args, **values)
        self.id = payment_account_id
        self.bank_id = bank_id
        self.account_id = account_id
        self.user_id = user_id

