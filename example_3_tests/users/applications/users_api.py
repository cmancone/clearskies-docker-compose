import clearskies
import .models

users_api = clearskies.Application(
    clearskies.handlers.RestfulAPI,
    {
        'models_class': models.Users,
        'readable_columns': ['name', 'email', 'city', 'state', 'country', 'age', 'created', 'updated'],
        'writeable_columns': ['name', 'email'],
        'searchable_columns': ['name', 'email'],
        'default_sort_column': 'name',
        'authentication': clearskies.authentication.public(),
    },
)
