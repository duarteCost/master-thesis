import datetime

from mongoengine import *


class Role(Document):

    name = StringField(unique=True, max_length=500, required=True)
    description = StringField(max_length=500, required=True)
    modifiedAt = DateTimeField(default=datetime.datetime.now())
    users = ListField(ObjectIdField(), default=[])

    def __init__(self, id, name, description, *args, **values):
        super().__init__(*args, **values)
        self.id = id
        self.name = name
        self.description = description
