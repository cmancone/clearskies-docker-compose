from clearskies import Models
from .user import User


class Users(Models):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def model_class(self):
        return User
