import unittest
from unittest.mock import MagicMock
from .business_email import BusinessEmail
from types import SimpleNamespace


class BusinessEmailTest(unittest.TestCase):
    def test_check_search_value(self):
        # Our class needs a requests object, but since we're not going to use it in the function
        # we're passing in here, we can be lazy and pass in anything we want
        email = BusinessEmail('requests')
        email.configure('email', {}, BusinessEmailTest)
        self.assertEquals('', email.check_search_value('cmancone@example2.com'))
        self.assertEquals('Invalid email domain', email.check_search_value('cmancone@example.com'))
        self.assertEquals('Invalid email address', email.check_search_value('cmancone'))
        self.assertEquals('Value must be a string for email', email.check_search_value(5))

    def test_pre_save(self):
        # Mock out our requests object, including the response
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
        requests = SimpleNamespace(get=get)

        # now build our email object and pass in the mock
        email = BusinessEmail(requests)
        email.configure('email', {}, BusinessEmailTest)

        # and test out the pre_save!  Again, the second parameter (model) passed to pre_save won't
        # be used, so we can pass anything in there
        final_data = email.pre_save(
            {
                'name': 'Conor',
                'email': 'cmancone@example.com',
            },
            'model'
        )

        # we should have taken the API results we wanted and added them to the final data
        self.assertEquals({
            'name': 'Conor',
            'email': 'cmancone@example.com',
            'city': 'cool city',
            'state': 'awesome state',
            'country': 'my country',
            'age': 20,
        }, final_data)

        # and of course we should have made the correct API call to our service provider
        get.assert_called_with(
            'https://randomuser.me/api/',
            params={'seed': 'cmancone@example.com'}
        )

    def test_pre_save_no_email(self):
        email = BusinessEmail('requests')
        email.configure('email', {}, BusinessEmailTest)

        final_data = email.pre_save(
            {
                'name': 'Conor',
            },
            'model'
        )

        # we should have taken the API results we wanted and added them to the final data
        self.assertEquals({
            'name': 'Conor',
        }, final_data)

    def test_pre_save_blank_email(self):
        email = BusinessEmail('requests')
        email.configure('email', {}, BusinessEmailTest)

        final_data = email.pre_save(
            {
                'name': 'Conor',
                'email': '',
                'city': 'Will',
                'state': 'Be',
                'country': 'Clobbered',
                'age': 20,
            },
            'model'
        )

        # we should have taken the API results we wanted and added them to the final data
        self.assertEquals({
            'name': 'Conor',
            'email': '',
            'city': '',
            'state': '',
            'country': '',
            'age': 0,
        }, final_data)
