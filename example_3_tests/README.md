# Tests

Of course, any good application needs some tests!  Now it's time to look at testing our application.

 - [Unit Tests](#unit-tests)
 - [Integration Tests](#integration-tests)

# Unit Tests

You can really use any testing suite you want to test your application.  This is where dependency injection comes in handy, as it means that test environments are easy to setup and patching is rarely necessary.  Columns are especially easy to test as they don't natively have any dependencies or side-effects.  Our Column class from the last example has only one dependency (the `requests` module) and doesn't persist anything anywhere.

As a result, I'm just going to work with the standard, built in, unittest module.  Obviously though you can use whatever testing suite you want.  First, we'll check our function which checks input for errors in our custom Column class.  For context, the relevant code looks like this:

```
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
```

We want to check the `input_error_for_value` method.  Our Column class does require the requests module to be injected in the contstructor, but it doesn't get used at all in this method we're checking at the moment.  Therefore, we don't have to worry about it and can provide a placeholder.  Our check for this method looks like this:

```
import unittest
from .business_email import BusinessEmail


class BusinessEmailTest(unittest.TestCase):
    def test_check_search_value(self):
        email = BusinessEmail('requests')
        email.configure('email', {}, BusinessEmailTest)
        self.assertEquals('', email.check_search_value('cmancone@example2.com'))
        self.assertEquals('Invalid email domain', email.check_search_value('cmancone@example.com'))
        self.assertEquals('Invalid email address', email.check_search_value('cmancone'))
        self.assertEquals('Value must be a string for email', email.check_search_value(5))

```

We create an instance of our class and then call its `configure` method, passing in the column name, configuration, and then the model class (which isn't needed in our example, so I provided a filler).  Then we just call our `check_search` method with whatever we want and check the result.  An empty string means the value is allowed, and otherwise we should hae an error message.

Of course you need a runner, and so an example runner for the project is given in the [users/test.py](./users/test.py) file.  It's as easy as this:

```
$ ./test.py
.
----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
```

Next we want to check our `pre_save` method.  For context, it looks like this:

```
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
```

it exits early if the column is not in the data.  If there is no email then it will return extra empty parameters in the returned data.  Otherwise it will make an HTTP request with the email, parse the results, and include part of the results in the retruned data.  We're going to use the `MagicMock` method in the standard `unittest` library to make a fake `requests.get` method, as well as the `json` method of the result object it returns.  There are lots of ways to do this in "vanilla" python, but I like to use the `SimpleNamespace` class to make the equivalent of anonymous objects.  This can team up with the `MagicMock` method to confirm calling parameters, or just with a simple `lambda` if you don't care about checking the call.  So for instance we can build the response from the `requests` library like this:

```
from types import SimpleNamespace

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
```

In otherwords, we have a response object, it has a `json` property, and when that method is called it returns a dictionary of results.  We just need to return this object when the `get` method is called on the requests library.  To do that, we use another `SimpleNamespace` and a `MagicMock` (so we can test how our `get` method was called later).  That looks something like this:

```
from unittest import MagicMock

response = [FROM_ABOVE]
requests = SimpleNamespace(get=MagicMock(return_value=response))
```

And that's it!  We now have our requests object which we can inject into our Column class.  After we run the `pre_save` method we can check the details of the HTTP reqest that the class tried to make by using the `assert_called_with` method of the `MagicMock` class.  Putting it all together we get this:

```
import unittest
from unittest.mock import MagicMock
from .business_email import BusinessEmail
from types import SimpleNamespace


class BusinessEmailTest(unittest.TestCase):
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
```

See the actual [users/models/business_email_test.py](./users/models/business_email_test.py) file for a few more tests on the code branches.

# Integration Tests

Of course, the line between integration tests and unit tests can be... blurry.  In the following examples we're still going to mock out a few dependencies to simplify testing, but we'll still get as close to a production test as is practical/helpful.  As part of this, we're going to mock out 4 things:

 1. [Swap the CursorBackend for a MemoryBackend.](#memorybackend)
 2. [Mock the HTTP request/response object since we don't have an actual WSGI server running things.](#request-and-response)
 3. [Mock out the requests library so we don't actually have to use a 3rd party service.](#request-library)
 4. [Set the current time to simplify testing.](#current-time)

We can do all these things without making any changes to our production code.  The key is our binding spec.  In case you missed it, [the binding spec is a special class in the pinject library](https://github.com/google/pinject#binding-specs) that allows you to configure the dependency injection process.  The base clearskies binding spec gives options to easily override all the dependencies at run-time, both at the class level and object level.  When running an integration test on the full application, we want to override dependencies at the class level so that the actual application will pick up these changes itself.

To do this at the class level, you use the `bind` class method of the clearskies binding class.  This accepts a dictionary with the objects to use instead of the default dependencies.

## MemoryBackend

To replace the cursor backend with a memory backend, we'll build an instance of the [MemoryBackend](https://github.com/cmancone/clearskies/blob/master/src/clearskies/backends/memory_backend.py) class.  This class has no depdencies itself, but needs some configuration.  First you must create the "tables" in the database, which you do by simply calling the `create_table` method and passing in a model class that you intend to use with the memory backend.  This creates a list of expected table/column names, so that an error can be thrown if you use incorrect values.  You can then create some initial records in the memory backend if desired.  The process looks something like this:

```
import unittest
from clearskies.binding_specs import WSGI
from clearskies.backends import MemoryBackend
from models import User, Users


class ApiTest(unittest.TestCase):
    def setUp(self):
        # create the memory backend
        self.memory_backend = MemoryBackend()

        # create a "table" for our User class (the class, not a model instance!)
        self.memory_backend.create_table(User)

        # add a record to the table.  Note that the model class is required so that it knows what table
        # to stick the record in.
        self.memory_backend.create_record_with_class(User, {
            'name': 'Conor',
            'email': 'cmancone@example.com',
            'age': 120,
            'created': self.now,
            'updated': self.now,
        })

        # now override the cursor_backend and tell clearskies to inject our memory backend instead
        WSGI.bind({
            'cursor_backend': self.memory_backend
        })
```

## Request and Response

Since we're not hooked up to an actual server, we need to mock out our HTTP request and response object.  In "typical" clearskies usage you don't have to deal directly with the HTTP request and response, since both are used by the handlers, and the WSGI binding spec automatically provides the necessary object and configuration.  So, as a quick intro, both the request and response are managed by an object descended from the [InputOutput](https://github.com/cmancone/clearskies/blob/master/src/clearskies/input_outputs/input_output.py) class. Yes, this is a clear violation of the Single Responsibility Principle.  Yes, there is a reason for this violation.  No, I don't regret this choice ☺.

To help with testing, there is a [mock InputOuput](https://github.com/cmancone/clearskies/blob/master/src/clearskies/mocks/input_output.py) class which you can use to specify an arbitrary HTTP request and see the details of the response sent back by the clearskies application.

## Mock requests library

Our [BusinessEmail](https://github.com/cmancone/clearskies-docker-compose/blob/master/example_3_tests/users/models/business_email.py) class made an HTTP call with the [requests](https://pypi.org/project/requests/) library.  If we don't mock out the requests library, then our tests will actually make an HTTP request.  This likely isn't what you want, since it means that your integration tests will also be testing a 3rd party service, which isn't usually the point.  Therefore we'll mock out the requests library just like we did in the unit tests, and then just specify our requests mock as an override in the dependency injection configuration:

```
import unittest
from unittest.mock import MagicMock
from types import SimpleNamespace


class ApiTest(unittest.TestCase):
    def setUp(self):
        # The SimpleNamespace is a convenient way to make an "anonymous" model to attach mock method calls to.
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

        WSGI.bind({
            'requests': self.requests,
        })
```
