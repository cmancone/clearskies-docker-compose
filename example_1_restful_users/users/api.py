import clearskies
from users import Users
from user import User

users_app = clearskies.Application(
    clearskies.handlers.RestfulAPI,
    {
        'models_class': Users,
        'readable_columns': ['name', 'email', 'age', 'created', 'updated'],
        'writeable_columns': ['name', 'email', 'age'],
        'searchable_columns': ['name', 'email', 'age'],
        'default_sort_column': 'name',
        'authentication': clearskies.authentication.public(),
    },
)

api = clearskies.contexts.wsgi(users_app)

def application(env, start_response):
    return api(env, start_response)
