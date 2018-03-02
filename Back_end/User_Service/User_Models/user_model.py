import datetime

from mongoengine import *
from werkzeug.security import generate_password_hash


class User(Document):
    id = ObjectIdField(required=True, primary_key=True)
    email = EmailField(unique=True, max_length=200, required=True)
    password = StringField(max_length=200, required=True)
    name = StringField(max_length=200, required=True)
    surname = StringField(max_length=200, required=True)
    obp_authorization =  StringField(max_length=200, required=False)
    modifiedAt = DateTimeField(default=datetime.datetime.now())

    def __init__(self, user_id, email, password, name, surname, obp_authorization, *args, **values):
        super().__init__(*args, **values)
        self.id = user_id
        self.email = email
        self.password = generate_password_hash(password)
        self.name = name
        self.surname = surname
        self.obp_authorization = obp_authorization

