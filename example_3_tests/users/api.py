import clearskies
from users import Users
from user import User


def application(env, start_response):
    api = clearskies.binding_specs.WSGI.init_application(
        clearskies.handlers.RestfulAPI,
        {
            'models_class': Users,
            'readable_columns': ['name', 'email', 'city', 'state', 'country', 'age', 'created', 'updated'],
            'writeable_columns': ['name', 'email'],
            'searchable_columns': ['name', 'email'],
            'default_sort_column': 'name',
        },
        env,
        start_response,
        authentication=clearskies.authentication.public()
    )
    return api()