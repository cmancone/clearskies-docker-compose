import clearskies
from models import Users
from .applications import users_api

api = clearskies.contexts.wsgi(users_api)

def application(env, start_response):
    return api(env, start_response)
