import datetime

from mongoengine import *


class Bank_account(Document):

    bank_id = StringField(max_length=500, required=True)
    account_id = StringField(max_length=500, required=True)
    modifiedAt = DateTimeField(default=datetime.datetime.now())

    def __init__(self, payment_account_id, bank_id, account_id, *args, **values):
        super().__init__(*args, **values)
        self.id = payment_account_id
        self.bank_id = bank_id
        self.account_id = account_id