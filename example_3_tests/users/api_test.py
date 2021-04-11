import unittest
from unittest.mock import MagicMock
from types import SimpleNamespace
from clearskies.mocks import InputOutput
from clearskies.binding_specs import WSGI
from clearskies.backends import MemoryBackend
from models import User
from api import application


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.environment = {}
        self.start_response = MagicMock()
        self.memory_backend = MemoryBackend()
        self.memory_backend.create_table(User)
        self.memory_backend.create_record_with_class(User, {
            'name': 'Conor',
            'email': 'cmancone@example.com',
            'age': 120,
        })
        self.input_output = InputOutput()

        WSGI.bind({
            'cursor_backend': self.memory_backend,
            'input_output': self.input_output,
        })

    def test_list_all(self):
        app = application(self.environment, self.start_response)
