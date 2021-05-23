# Adding in Business Logic

Of course, an API that just dumps data into a database is not very useful.  You'll almost always need to implement some custom behavior (aka business logic) to your API.  In clearskies, this business logic pretty much always lives in either the model or a `Column` class.  This example will show how to define your own custom `Column` class that will implement some additional user input checks and modify the data before persisting it to the backend.

 - [Columns](#columns)
 - [Input Checking](#input-checking)
 - [Pre-Save vs Post-Save](#pre-save-vs-post-save)
 - [Fetching Additional Data](#fetching-additional-data)
 - [Update Model and API Configuration](#update-model-and-api-configuration)
 - [API Changes](#api-changes)

# Columns

We've already used a few different column types.  Our model included [String](https://github.com/cmancone/clearskies/blob/master/src/clearskies/column_types/string.py), [Email](https://github.com/cmancone/clearskies/blob/master/src/clearskies/column_types/email.py), [Integer](https://github.com/cmancone/clearskies/blob/master/src/clearskies/column_types/integer.py), [Created](https://github.com/cmancone/clearskies/blob/master/src/clearskies/column_types/created.py), and [Updated](https://github.com/cmancone/clearskies/blob/master/src/clearskies/column_types/string.py) columns.  Each column class comes with pre-defined behavior related to input checking, data injection, transformations to/from the backend, and JSON conversion.

If your business logic is related to a particular "column" in your backend/API, then you'll likely want to implement it by defining your own Column class to keep all the related business logic together.  clearskies has a number of hooks that you can extend when defining your Column class which you can use to inject behavior into all the stages of the save process.  This is also true for the model classes, although we will explore that functionality in a later example.

Most of the time you wouldn't build your own Column from scratch, but rather extend and modify one of the existing Column classes.  In the following example, we're going to extend the `clearskies.column_types.Email` class to add some functionality related to the user's email.  Specifically, we're going to add two changes:

 1. We want to block emails from a specific domain
 2. We will send the email to an external API to fetch related data which we will store with the model

For the latter, we'll need the `requests` module.  Since this is a commonly needed, clearskies automatically configures and provides it for dependency injection (see the `provide_requests` method in the base [BindingSpec class](https://github.com/cmancone/clearskies/blob/master/src/clearskies/binding_specs/binding_spec.py)).  Therefore, to inject it, we just need to add the `requests` positional parameter to the constructor of our new Column. Therefore, we start with this:

```
from clearskies.column_types import Email, build_column_config


def business_email(name, **kwargs):
    return build_column_config(name, BusinessEmail, **kwargs)

class BusinessEmail(Email):
    _requests = None

    def __init__(self, requests):
        self._requests = requests
```

By extending the `Email` column we automatically gain the basic functionality related to validating and handling email addresses.  Our constructor includes the `requests` parameter, and so clearskies will automatically inject the requests library.  Finally, note the `business_email` function.  This is not required but will allow us to add a `BusinessEmail` column to our model the same way we add in other Columns.

# Input Checking

For input checking, we want to blacklist a specific domain.  Every Column class has a method called `input_error_for_value`.  During saving and searching clearskies will invoke this method with the user input for the column, and it should return a user-friendly error message if the value is not acceptable.  For valid values it should return an empty string.  Note that this is invoked during API calls: **not** if you issue a `model.save()` call directly yourself.  When we extend this we want to call the parent method first and return early if the parent returns an error message, as this will check for a valid email address for us.  Therefore we end up with this:

```
    def input_error_for_value(self, value):
        error = super().input_error_for_value(value)
        if error:
            return error
        if value[-12:] == '@example.com':
            return 'Invalid email domain'
        return ''
```

# Pre-Save vs Post-Save

clearskies has two primary hooks during the save process: `pre_save` and `post_save`.  `pre_save` is called before persisting any data to the backend, and `post_save` is (naturally!) called afterwards.  This results in two primary differences between these methods, which will determine which you want to use in a given situation:

 - During `pre_save`, you may make changes to the data being saved and these changes will be persisted to the backend in a single operation.
 - The model id is only consistently available during `post_save`, since during a create operation the record is only created after the `pre_save` call

Therefore, use `pre_save` if the model id is not required and you don't want to issue a second call to your backend.  Use `post_save` if you require the model id for your business logic, but remember that you have to issue a separate save operation to persist any data.  In our case, we are going to use the email address present in the save data to fetch additional information to save.  Therefore, the model id is not required and we can put our logic in `pre_save` to save an extra trip to our backend.

# Fetching Additional Data

We're going to define the `pre_save` hook in our `BusinessEmail` column.  This is what the default `pre_save` method does:

```
    def pre_save(self, data, model):
        # returning the data dictionary is required!
        return data
```

`data` is a dictionary containing the data being saved.  Therefore, we want to fetch the email from there.  Moreover, we'll return a new `data` dictionary with our additional information.  Note that we should always check that the column we are interested in is actually avaialable in our data dictionary to avoid errors.  Even if, for instance, the API requires the `email` column to be present, there are still cases where it may not be in this dictionary.  In particular, this happens if you issue a `save` operation to the model directly, rather than invoking it through the API.  In short, the input requirements you provide in the model are only processed during API calls: never by any direct save calls you make to your models yourself.

The `model` parameter passed into this function will of course be the model that data is being saved to.  Use this if you need to know whether or not the model already exists and what the current data in the model is.  Finally, you'll likely want to reference `self.name` in your logic: this is the name of your column.  In our current example this will always be `email`, but it's usually best not to hard-code this in your logic in case you decide to change the column name later or re-use your new column with a different name.

Here is our finished example, where we fetch some data from an external API endpoint and save the results to our model:

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

To emphasize again: we don't need to persist anything ourselves.  We just need to return additional information in the data dictionary.  The clearskies model will make sure to persist all this data to the backend later on in the save process.

# Update Model and API Configuration

Finally, we need to make some changes to our model and API configuration.  We now have this new `BusinessEmail` column to use instead of the standard `Email` column type.  Moreover, we have a couple additional columns (`city`, `state`, and `country`).  Finally, four of our columns will be set automatically by the above `pre_save` in our `BusinessEmail` column, and so do not need to be set explicitly.  The columns configuration in our [User model](./users/user.py) class just needs some minor adjustments to reflect this:

```
    def columns_configuration(self):
        return OrderedDict([
            string('name', input_requirements=[required(), maximum_length(255)]),
            business_email('email', input_requirements=[required(), maximum_length(255)]),
            string('city', is_writeable=False),
            string('state', is_writeable=False),
            string('country', is_writeable=False),
            integer('age', is_writeable=False),
            created('created'),
            updated('updated'),
        ])
```

Note that we've changed out the column type for the `email` field and we've also marked four fields with the `is_writeable=False` flag.  We've removed the `input_requirements` from our age column because it is no longer set from user input, so has no requirements!

Similarly, we just need some minor changes to our columns configuration in our [API config](./users/api.py).  In short, we have additional columns we want to return to the user (i.e. the `readable_columns`) and we no longer need to accept input for the `age` column, so it comes out of the `writeable_columns` list:

```
def application(env, start_response):
    api = clearskies.binding_specs.WSGI.init_application(
        clearskies.handlers.RestfulAPI,
        {
            'models_class': Users,
            'readable_columns': ['name', 'email', 'city', 'state', 'country', 'age', 'created', 'updated'],
            'writeable_columns': ['name', 'email'],
            'searchable_columns': ['name', 'email'],
            'default_sort_column': 'name',
            'authentication': clearskies.authentication.public(),
        },
        env,
        start_response,
    )
    return api()
```

# API Changes

We can launch our new application via `docker-compose up` and see the results of our changes.

Our input check works as expected.  Trying to set an email with the `example.com` domain:

```
curl 'http://localhost:5000' -d '{"name":"Conor","email":"cmancone@example.com"}'
```

Results in this response:

```
{
    "status": "inputErrors",
    "inputErrors": {"email": "Invalid email domain"},
    "error": "",
    "data": [],
    "pagination": {}
}
```

And we can no longer set the `age` column:

```
curl 'http://localhost:5000' -d '{"name":"Conor","email":"cmancone2@example2.com", "age": 5}'
```

which gives us:

```
{
    "status": "inputErrors",
    "inputErrors": {"age": "Input column 'age' is not an allowed column"},
    "error": "",
    "data": [],
    "pagination": {}
}
```

If we make a valid request then we'll see a slight delay as our external API is hit, and our additional data will be provided to us:

```
curl 'http://localhost:5000' -d '{"name":"Conor","email":"cmancone@example2.com"}'
```

And our response:

```
{
    "status": "success",
    "data": {
        "id": 1,
        "name": "Conor",
        "email": "cmancone@example2.com",
        "city": "Sinop",
        "state": "Ayd\u0131n",
        "country": "Turkey",
        "age": 55,
        "created": "2021-03-28T18:28:39+00:00",
        "updated": "2021-03-28T18:28:39+00:00"
    },
    "pagination": {},
    "error": "",
    "inputErrors": {}
}
```
