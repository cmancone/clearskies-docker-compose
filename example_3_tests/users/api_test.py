import unittest
from unittest.mock import MagicMock
from types import SimpleNamespace
from clearskies.mocks import InputOutput
from clearskies.binding_specs import WSGI
from clearskies.backends import MemoryBackend
from models import User, Users
from api import application
from datetime import datetime, timezone
from collections import OrderedDict


class ApiTest(unittest.TestCase):
    def setUp(self):
        # a standard "now" will make life easier in case the second changes mid-testing
        self.now = datetime.now().replace(tzinfo=timezone.utc, microsecond=0)

        # we're also going to switch our cursor backend for an in-memory backend, create a table, and add a record
        self.memory_backend = MemoryBackend()
        self.memory_backend.create_table(User)
        self.memory_backend.create_record_with_class(User, {
            'name': 'Conor',
            'email': 'cmancone@example.com',
            'age': 120,
            'created': self.now,
            'updated': self.now,
        })

        # we need our own Input/Output object since there is no web server
        self.input_output = InputOutput()

        # Finally, we'll mock out a requests object for the API call made by our email column.
        # This isn't strictly required, but if we don't do it then our integration test will actually make calls
        # to 3rd party services, which means they will fail if those services are down - that isn't usually helpful.
        response = SimpleNamespace(json=lambda: {'results':[{
            'location': {
                'city': 'cool city',
                'state': 'awesome state',
                'country': 'my country',
            },
            'dob': {
                'age': 20,
            }
        }]})
        get = MagicMock(return_value=response)
        self.requests = SimpleNamespace(get=get)

        # This is where we update our binding spec class to use the couple things we had to mock.
        WSGI.bind({
            'cursor_backend': self.memory_backend,
            'input_output': self.input_output,
            'requests': self.requests,
            'now': self.now,
        })

    def test_list_all(self):
        # we want to call the same application method that the WSGI server would.  However, we don't need
        # either the 'environment' variable or the start_response call back.  We don't need an environment because
        # instead everything will just come through the self.input_output object which we injected in and will
        # configuire.  We don't need a start_response object becauise our mock InputOutput object won't use it
        # anyway - it will just return the response as a tuple with (response, status_code).
        # Therefore, we can just call the application function and get back the result from the API endpoint.
        result = application('environment', 'start_response')
        status_code = result[1]
        response = result[0]
        self.assertEquals(200, status_code)
        self.assertEquals(1, len(response['data']))

        # Because nothing was converted to JSON, we'll get back an OrderedDict, which is how clearskies builds its
        # response so it can control the order of the elements in the final JSON response.  In general, the order
        # will match the order of the columns in your model, with 'id' first.
        self.assertEquals(OrderedDict([
            ('id', 1),
            ('name', 'Conor'),
            ('email', 'cmancone@example.com'),
            ('city', None),
            ('state', None),
            ('country', None),
            ('age', 120),
            ('created', self.now.isoformat()),
            ('updated', self.now.isoformat()),
        ]), response['data'][0])
        self.assertEquals({'numberResults': 1, 'start': 0, 'limit': 100}, response['pagination'])
        self.assertEquals('success', response['status'])

    def test_create(self):
        # To test out a create, we'll switch our request to a POST and provide a body.
        self.input_output.set_request_method('POST')
        self.input_output.set_body({
            'name': 'Alice',
            'email': 'alice@example2.com',
        })
        result = application('environment', 'start_response')
        status_code = result[1]
        response = result[0]
        self.assertEquals(200, status_code)
        self.assertEquals(OrderedDict([
            ('id', 2),
            ('name', 'Alice'),
            ('email', 'alice@example2.com'),
            ('city', 'cool city'),
            ('state', 'awesome state'),
            ('country', 'my country'),
            ('age', 20),
            ('created', self.now.isoformat()),
            ('updated', self.now.isoformat()),
        ]), response['data'])
        self.assertEquals('success', response['status'])

    def test_update(self):
        self.input_output.set_request_method('PUT')
        self.input_output.set_request_url('/1')
        self.input_output.set_body({
            'name': 'CMan',
            'email': 'cman@example2.com',
        })
        result = application('environment', 'start_response')
        status_code = result[1]
        response = result[0]
        self.assertEquals(200, status_code)
        self.assertEquals(OrderedDict([
            ('id', 1),
            ('name', 'CMan'),
            ('email', 'cman@example2.com'),
            ('city', 'cool city'),
            ('state', 'awesome state'),
            ('country', 'my country'),
            ('age', 20),
            ('created', self.now.isoformat()),
            ('updated', self.now.isoformat()),
        ]), response['data'])
        self.assertEquals('success', response['status'])
