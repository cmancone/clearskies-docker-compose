from collections import OrderedDict
from clearskies import Model
from clearskies.column_types import string, email, integer, created, updated
from clearskies.input_requirements import Required, MaximumLength


class User(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            string('name', input_requirements=[Required, (MaximumLength, 255)]),
            email('email', input_requirements=[Required, (MaximumLength, 255)]),
            integer('age'),
            created('created'),
            updated('updated'),
        ])
