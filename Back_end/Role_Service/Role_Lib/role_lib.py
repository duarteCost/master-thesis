from bson import ObjectId
from pymongo import errors


# methods
def get_roles(mongobd_role):
    try:
        roles = mongobd_role.find({})
        if roles.count() == 0:
            return 'No roles found'
        else:
            return {'roles': roles}
    except errors.ServerSelectionTimeoutError:
        return 'Mongodb is not running'

def user_roles(roles, user_id):
    user_roles_name = []
    roles = roles['roles']
    for role in roles:
        if "users" in role:
            if ObjectId(user_id) in role['users']:
                user_roles_name.append(role['name'])
    return user_roles_name