from django.contrib.auth.hashers import make_password
from mongosh import users_collection


class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = make_password(password)

    def save(self):
        users_collection.insert_one({
            'username': self.username,
            'email': self.email,
            'password': self.password
        })

    @staticmethod
    def find_by_email(email):
        return users_collection.find_one({"email": email})