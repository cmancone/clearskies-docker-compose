from clearskies.column_types import Email, build_column_config


def business_email(name, **kwargs):
    return build_column_config(name, BusinessEmail, **kwargs)

class BusinessEmail(Email):
    _requests = None

    def __init__(self, requests):
        self._requests = requests

    def input_error_for_value(self, value):
        error = super().input_error_for_value(value)
        if error:
            return error
        if value[-12:] == '@example.com':
            return 'Invalid email domain'
        return ''

    def pre_save(self, data, model):
        if not self.name in data:
            return data
        email = data[self.name].strip()
        if not email:
            user_data = {
                'city': '',
                'state': '',
                'country': '',
                'age': '',
            }
        else:
            response_data = self._requests.get(
                'https://randomuser.me/api/',
                params={'seed': email}
            ).json()['results'][0]
            user_data = {
                'city': response_data['location']['city'],
                'state': response_data['location']['state'],
                'country': response_data['location']['country'],
                'age': response_data['dob']['age'],
            }

        return {
            **data,
            **user_data,
        }
