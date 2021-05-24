import unittest
from clearskies.contexts import test
from unittest.mock import MagicMock
from types import SimpleNamespace
from models import User, Users
from .users_api import users_api
from collections import OrderedDict


class UsersApiTest(unittest.TestCase):
    def setUp(self):
        self.api = test(users_api)

        # we're also going to switch our cursor backend for an in-memory backend, create a table, and add a record
        self.memory_backend = self.api.memory_backend
        self.memory_backend.create_table(User)
        self.memory_backend.create_record_with_class(User, {
            'name': 'Conor',
            'email': 'cmancone@example.com',
            'age': 120,
            'created': self.api.now,
            'updated': self.api.now,
        })

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

        # and we need to mock out the "usual" requests library
        self.api.bind('requests', self.requests)

    def test_list_all(self):
        # fetch all records, which doesn't need anything special in the request: empty post body, default route,
        # GET method.  Therefore, we can just invoke our app in the test context without any effort
        result = self.api()
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
            ('created', self.api.now.isoformat()),
            ('updated', self.api.now.isoformat()),
        ]), response['data'][0])
        self.assertEquals({'numberResults': 1, 'start': 0, 'limit': 100}, response['pagination'])
        self.assertEquals('success', response['status'])

    def test_create(self):
        # To test out a create, we'll switch our request to a POST and provide a body.
        result = self.api(
            method='POST',
            body={
                'name': 'Alice',
                'email': 'alice@example2.com',
            }
        )
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
            ('created', self.api.now.isoformat()),
            ('updated', self.api.now.isoformat()),
        ]), response['data'])
        self.assertEquals('success', response['status'])

    def test_update(self):
        result = self.api(
            method='PUT',
            url='/1',
            body={
                'name': 'CMan',
                'email': 'cman@example2.com',
            }
        )
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
            ('created', self.api.now.isoformat()),
            ('updated', self.api.now.isoformat()),
        ]), response['data'])
        self.assertEquals('success', response['status'])
