import clearskies
from models import Users


def application(env, start_response):
    api = clearskies.binding_specs.WSGI.init_application(
        clearskies.handlers.RestfulAPI,
        {
            'models_class': Users,
            'readable_columns': ['name', 'email', 'city', 'state', 'country', 'age', 'created', 'updated'],
            'writeable_columns': ['name', 'email'],
            'searchable_columns': ['name', 'email'],
            'default_sort_column': 'name',
            'authentication': clearskies.authentication.public(),
        },
        env,
        start_response,
    )
    return api()
