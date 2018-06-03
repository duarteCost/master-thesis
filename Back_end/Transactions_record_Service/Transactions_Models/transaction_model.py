import datetime

from mongoengine import *


class Transaction(Document):

    bank_id = StringField(max_length=500, required=True)
    account_id = StringField(max_length=500, required=True)
    amount= FloatField(max_length=500, required=True)
    currency= StringField(max_length=500, required=True)
    description= StringField(max_length=500, required=True)
    status= StringField(max_length=500, required=True)
    user_id = ObjectIdField(max_length=200, required=True)
    merchant = StringField(max_length=200, required=True)
    modifiedAt = DateTimeField(default=datetime.datetime.now())

    def __init__(self, transaction_id, bank_id, account_id, amount, currency, description, status, user_id, merchant, *args, **values):
        super().__init__(*args, **values)
        self.id = transaction_id
        self.bank_id = bank_id
        self.account_id = account_id
        self.amount = amount
        self.currency = currency
        self.description = description
        self.status = status
        self.user_id = user_id
        self.merchant = merchant
        self.modifiedAt = datetime.datetime.now()