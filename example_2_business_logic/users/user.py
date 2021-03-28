from collections import OrderedDict
from clearskies import Model
from clearskies.column_types import string, integer, created, updated
from clearskies.input_requirements import Required, MaximumLength
from business_email import business_email


class User(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            string('name', input_requirements=[Required, (MaximumLength, 255)]),
            business_email('email', input_requirements=[Required, (MaximumLength, 255)]),
            string('city', is_writeable=False, input_requirements=[(MaximumLength, 255)]),
            string('state', is_writeable=False, input_requirements=[(MaximumLength, 255)]),
            string('country', is_writeable=False, input_requirements=[(MaximumLength, 255)]),
            integer('age', is_writeable=False),
            created('created'),
            updated('updated'),
        ])
