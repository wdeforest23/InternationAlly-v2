from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, email, name):
        self.id = id
        self.email = email
        self.name = name

    @staticmethod
    def get(user_id):
        # In a real app, this would check a database
        # For now, we'll use a simple in-memory store
        return User.users.get(user_id)

    # Simple in-memory user store
    users = {}
