from mongoengine import *


class ReceiverAccount(EmbeddedDocument):
    bank_id = StringField(max_length=500, required=True)
    account_id = StringField(max_length=500, required=True)


class Merchant(Document):
    id = ObjectIdField(required=True, primary_key=True)
    brand = StringField(max_length=500, required=True)
    email = StringField(unique=True, max_length=500, required=True)
    phone = StringField(max_length=500, required=True)
    key = StringField(max_length=500, required=True)
    user_id = ObjectIdField(unique=True, required=True)
    receiver_account = EmbeddedDocumentField(ReceiverAccount)

    def __init__(self, id, brand, email, phone, key, user_id, receiver_account, *args, **values):
        super().__init__(*args, **values)
        self.id = id
        self.brand = brand
        self.email = email
        self.phone = phone
        self.key = key
        self.user_id = user_id
        self.receiver_account = receiver_account