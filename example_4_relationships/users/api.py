import clearskies
import apps

api = clearskies.contexts.wsgi(apps.users_api)

def application(env, start_response):
    return api(env, start_response)
