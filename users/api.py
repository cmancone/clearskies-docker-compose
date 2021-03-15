from binding_spec import BindingSpec
import clearskies
from users import Users
from user import User


def application(env, start_response):
    object_graph = BindingSpec.get_object_graph(env, start_response)
    api = object_graph.provide(clearskies.handlers.CRUDByMethod)
    api.configure({
        'models_class': Users,
        'readable_columns': ['name', 'email', 'age', 'created', 'updated'],
        'writeable_columns': ['name', 'email', 'age'],
        'searchable_columns': ['name', 'email', 'age'],
        'default_sort_column': 'name',
    })
    return api()
