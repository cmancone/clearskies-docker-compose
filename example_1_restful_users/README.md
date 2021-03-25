# Simple, Public, RESTful users API

In this example we will build a simple RESTful API to manage a list of users.  We want to keep track of:

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
| /                   | GET               | Return record by id                        |
| /[id]               | PUT               | Update record by id                        |
| /[id]               | DELETE            | Delete record by id                        |
| /search             | POST              | Search records via conditions in POST body |

All endpoints speak JSON exclusively

## Model

In order to make this happen, our main requirement is just a model.  Models in clearskies extend the `clearskies.Model` class.  They mainly require two things:

 - An init method that will be used to inject the desired backend (a database cursor, in this case)
 - Column definitions!

### Model Backends

We're using a cursor backend for this example, which means that our model will manage records in a database.  Another common backend (to be explored in other examples) is an API backend, where the model manages records via an external API.  This is typically used in a microservices context, where you want to fetch and save data to a different API.  The model in this case just provides a consistent way to access the external API.  Naturally, clearskies comes with an backend for making calls to a clearskies API.  This means that if you are making calls to another clearskies API, you don't have to program any details about the API calls - the clearskies API backend will handle this for you automatically.

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
```

It's worth pointing out that our function calls, `string`, `email`, `integer`, `created`, and `updated` all refer to column types.  The first parameter passed to each function (`name`, `email`, `age`, `created`, and `updated`) represent our column name.  It just so happens that our column name and column type match for `email`, `created`, and `updated`, hence the duplication.

We're setting maximum lengths for our `name` and `email` columns and also marking these as required fields.  Since we use the `email` column type for our `email` field, API calls that use the `email` field will automatically return input errors if an invalid email is provided.  Finally, the `created` and `updated` columns will automatically set themselves on create/update operations, but these are otherwise "read-only" fields, meaning that they cannot be set in an API call.

## Query Builder

The model class is used to create/update a single record in the backend.  Building queries to fetch models is the job of the query builder, so we must define this too.  Fortunately, [it's very simple](./users/users.py):

from clearskies import Models
from user import User


class Users(Models):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def model_class(self):
        return User


## WSGI Entrypoint
