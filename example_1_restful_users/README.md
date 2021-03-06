# Simple, Public, RESTful users API

In this example we will build a simple RESTful API to manage a list of users.  This article is broken down as such:

 - [Overview](#overview)
 - [Model](#model)
 - [Query Builder](#query-builder)
 - [WSGI Entrypoint](#wsgi-entrypoint)
 - [API Usage](#api-usage)


## Overview

We want to keep track of:

 - Name
 - Email
 - Age
 - First Created
 - Last Updated

clearskies has a pre-baked handler for RESTful APIs which creates the following general behavior:

| URL                 | HTTP Verb         | Action                                     |
|---------------------|-------------------|--------------------------------------------|
| /                   | GET               | Return paginated list of records           |
| /                   | POST              | Create new record                          |
| /[id]               | GET               | Return record by id                        |
| /[id]               | PUT               | Update record by id                        |
| /[id]               | DELETE            | Delete record by id                        |
| /search             | POST              | Search records via conditions in POST body |

All endpoints speak JSON exclusively

## Model

In order to make this happen, our main requirement is just a model.  Models in clearskies extend the `clearskies.Model` class.  They mainly require two things:

 - An init method that will be used to inject the desired backend (a database cursor, in this case)
 - Column definitions!

### Model Backends

We're using a cursor backend for this example, which means that our model will manage records in a database.  Another common backend (to be explored in other examples) is an API backend, where the model manages records via an external API.  This is typically used in a microservices context, where you want to fetch and save data to a different API.  The model in this case just provides a consistent way to access the external API.

By default clearskies uses a [MariaDB connector](https://mariadb.com/resources/blog/how-to-connect-python-programs-to-mariadb/) that works for both MariaDB and MySQL.  It assumes that you have 4 environment variables configured:

| variable    | value                                |
|-------------|--------------------------------------|
| db_username | The username for your database       |
| db_password | The password for your database       |
| db_database | The database name                    |
| db_host     | The host to connect to your database |

The clearskies environment system will look for these keys in either environment variables or a file with key/value pairs.  We typically suggest using environment variables, but this example uses a [.env](users/.env) file for simplicity.

The backend is provided via dependency injection using [pinject](https://github.com/google/pinject).  pinject operates on parameter names, and clearskies provides the cursor backend via a parameter called `cursor_backend`.  Therefore, a model that uses a database for its backend will look like this:

```
import clearskies


class User(clearskies.Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)
```

The `columns` parameter will be given an object that will be responsible for creating the column objects that power everything.  For now, it's enough to know that you need to include this parameter in your model's `__init__` method and pass it along to the parent constructor.

Finally, a note on table names: clearskies assumes that table names are plural and the lowercase version of the model name.  Therefore, our above `User` model will assume a table name in your database of `users`.  You can override this name by overriding the `table_name` reader in your model:

```
class User(clearskies.model)
    @property
    def table_name(self):
        return 'some_other_table_name'
```

### Columns

The only other required part of a model is the column definitions.  Column definitions specify the name of each column, the type of each column, and any input requirements.  The available column types are not yet documented but you can view them in the [column_types](https://github.com/cmancone/clearskies/tree/master/src/clearskies/column_types) sub-module.  Available input requirements can be seen in the [input_requirements](https://github.com/cmancone/clearskies/tree/master/src/clearskies/input_requirements) sub-module.  The columns are configured for a given model by extending the `columns_configuration` method, which should return an OrderedDict.  Each column type has a helper method in the `column_types` sub module that you can use to easily build it.  This is best shown by example, so this is what our [full user model](./users/user.py) looks like:

```
from collections import OrderedDict
from clearskies import Model
from clearskies.column_types import string, email, integer, created, updated
from clearskies.input_requirements import required, maximum_length


class User(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            string('name', input_requirements=[reqired(), maximum_length(255)]),
            email('email', input_requirements=[reqired(), maximum_length(255)]),
            integer('age'),
            created('created'),
            updated('updated'),
        ])
```

It's worth pointing out that our function calls, `string`, `email`, `integer`, `created`, and `updated` all refer to column types.  The first parameter passed to each function (`name`, `email`, `age`, `created`, and `updated`) represent our column name.  It just so happens that our column name and column type match for `email`, `created`, and `updated`, hence the duplication.

We're setting maximum lengths for our `name` and `email` columns and also marking these as required fields.  Since we use the `email` column type for our `email` field, API calls that use the `email` field will automatically return input errors if an invalid email is provided.  Finally, the `created` and `updated` columns will automatically set themselves on create/update operations, but these are otherwise "read-only" fields, meaning that they cannot be set in an API call.

## Query Builder

The model class is used to create/update a single record in the backend.  Building queries to fetch models is the job of the query builder, so we must define this too.  Fortunately, [it's very simple](./users/users.py):

```
from clearskies import Models
from user import User


class Users(Models):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def model_class(self):
        return User
```

Note that it needs to receive the same backend as the model class, since this also acts as a factory for the model.

## WSGI Entrypoint

Finally, we need an application!  For this example we're using a WSGI server, so we need a python file with a standard WSGI "receiver".  A minimal WSGI application would look like this:

```
def application(env, start_response):
    return [b'Hello world!']
```

The `env` and `start_response` parameters provide the HTTP context and a callable that will be used to set information about the HTTP response.  As a result, clearskies will need these variables and will have to return an HTTP response.

When building endpoints with clearskies, it uses handlers with pre-configured behavior to generate endpoints.  They will use the information you provided in your model to automatically configure most of the endpoint behavior, and so just need a bit of direction to get started.  To bring it all together, here is our final application configuration (which you can see in [users/api.py](./users/api.py):

```
import clearskies
from users import Users
from user import User

users_app = clearskies.Application(
    clearskies.handlers.RestfulAPI,
    {
        'models_class': Users,
        'readable_columns': ['name', 'email', 'age', 'created', 'updated'],
        'writeable_columns': ['name', 'email', 'age'],
        'searchable_columns': ['name', 'email', 'age'],
        'default_sort_column': 'name',
        'authentication': clearskies.authentication.public(),
    },
)

api = clearskies.contexts.wsgi(users_app)

def application(env, start_response):
    return api(env, start_response)

```

Naturally, we import clearskies as well as our model and query builder for the model.  The model class is not used here but importing all your models at the beginning of the application will help you avoid errors from pinject related to cyclical dependencies.

Next we define our application (the `users_app` variable).  This defines exactly what we want our app to do - in this case, present a RESTful API.  The exact behavior is deteremined by the handler class (`clearskies.handlers.RestfulAPI`) as well as the handler configuration.  Each handler class has its own definition of required and optional parameters you can provide to control the application behavior.

It's also important to note that this application (the `users_app` variable) is **completely separated** from any execution context.  In other words, our application is not making any assumptions about how it is running (e.g. a WSGI server, Lambda, command line, queue listener, etc...)  Instead, the application must be attached to an execution "context".  In this case, the context we're attaching our clearskies application to is a WSGI server, and we do so like this:

```
api = clearskies.contexts.wsgi(users_app)
```

Our application is now ready to be executed by a WSGI server!  By changing this one line of code though, you could just as easily run this same application in a Lambda, a test suite, etc...

Finally, we want to call this from our standard WSGI receiving function.  It's important that the application and context are created outside of the WSGI function, as this will allow the WSGI server to cache our application, which can substantially reduce execution time.  Naturally, when we execute the application, we have to provide the `env` and `start_response` variables from the WSGI server.

## Building an Application

Above we showed how to build an application, but a quick explanation is in order.  A clearskies "application" defines the behavior of clearskies through a combination of the handler class (which defines the overall functionality) and the handler configuration (which provides the details needed for the handler to work).  You provide these two things when building the clearskies application, which looks like this:

```
app = clearskies.Application(
    HandlerClass,
    {'handler': 'config'},
)
```

As mentioned above, the list of required and optional configuration settings vary from handler class to handler class.

### Handler Class

We're providing the `clearskies.handlers.RestfulAPI` class.  Our full list of handlers are not yet documented, but this particular one will create a standard Restful API endpoint like we described at the top of this README file.  It just needs some basic configuration:

### Handler Configuration

Each handler class has its own set of configuration values, some of which are required, some of which are optional.  The above example sets all the required configuration options for our Restful API handler:

| Name                  | Value                                                                            |
|-----------------------|----------------------------------------------------------------------------------|
| `models_class`        | The query builder for our model class                                            |
| `readable_columns`    | The list of columns to return to the client in API responses                     |
| `writeable_columns`   | The list of columns that the client is allowed to set through the API            |
| `searchable_columns`  | The list of columns that the user can search with through the `/search` endpoint |
| `default_sort_column` | The default column to sort records by when listing results                       |
| `authentication`      | The authentication method to use for the endpoint                                |

## API Usage

The JSON response from clearskies is intended to always have a consistent response format.  You should always see the following "root" objects in your resposne:

| name        | value                                                                      |
|-------------|----------------------------------------------------------------------------|
| status      | `success` OR `clientError` OR `inputErrors` OR `failure`                   |
| inputErrors | An dictionary with input errors.  Used only with a status of `inputErrors` |
| error       | An error message: used only with a status of `clientError`                 |
| data        | The actual data for the response                                           |
| pagination  | Information about the maximum/current size of the response                 |

To try out this example, clone this repository, cd into the directory that contains this README.md file, and then just:

```
docker-compose up
```

It will launch the service on port 5000 locally, so:

```
curl 'http://localhost:5000'
```

But we don't have any records yet:

```
{
  "status": "success",
  "data": [],
  "pagination": {
    "numberResults": 0,
    "start": 0,
    "limit": 100
  },
  "error": "",
  "inputErrors": {}
}
```

So let's create a record:

```
curl 'http://localhost:5000' -d '{"name": "Conor Mancone", "email": "cmancone@gmail.com", "age": 100}'
```

And our response:

```
{
  "status": "success",
  "data": {
    "id": 1,
    "name": "Conor Mancone",
    "email": "cmancone@gmail.com",
    "age": 100,
    "created": "2021-03-25T16:13:59+00:00",
    "updated": "2021-03-25T16:13:59+00:00"
  },
  "pagination": {},
  "error": "",
  "inputErrors": {}
}
```

So now we can fetch our latest records:

```
curl 'http://localhost:5000'
```

and our response:

```
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Conor Mancone",
      "email": "cmancone@gmail.com",
      "age": 100,
      "created": "2021-03-25T16:13:59+00:00",
      "updated": "2021-03-25T16:13:59+00:00"
    }
  ],
  "pagination": {
    "numberResults": 1,
    "start": 0,
    "limit": 100
  },
  "error": "",
  "inputErrors": {}
}
```

This automatically applies strict input checking, which we can see with a request like this:

```
curl 'http://localhost:5000' -d '{"age":"asdf","email":"cmancone","sup":"hey"}' | jq
```

which gives this response:

```
{
  "status": "inputErrors",
  "inputErrors": {
    "sup": "Input column 'sup' is not an allowed column",
    "name": "'name' is required.",
    "email": "Invalid email address",
    "age": "age must be an integer"
  },
  "error": "",
  "data": [],
  "pagination": {}
}
```

We also have a search endpoint that allows us to make more complicated queries like so:

```
curl 'http://localhost:5000/search' \
    -d '{"where":[{"column":"name", "value":"conor"}],"sort":[{"column":"age","direction":"desc"}]}'

curl 'http://localhost:5000/search' \
    -d '{"where":[{"column":"age", "operator":"<", "value":"conor"}]}'
```
