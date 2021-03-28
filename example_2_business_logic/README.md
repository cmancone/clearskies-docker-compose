# Adding in Business Logic

Of course, an API that just dumps data into a database is not the most useful one.  You'll almost always need to implement some custom behavior (aka business logic) based on your user input.  This example will show how to define your own custom column type class that will implement some additional user input checks and modify the data before persisting it to the database

 - [Column Types](#column-types)
 - [Input Checking](#input-checking)
 - [Pre Save](#pre-save)
 - [Post Save](#post-save)
 - [Tests](#tests)

# Column Types

The logic of validating column types and making adjustments to the data before and after saving to the backend are controlled by the column type class.  clearskies has a number of hooks that you can extend to inject behavior into all the stages of the save process.  This is true  for both the column type classes (which are meant to enable column-specific behavior) as well as for the model, where you might control behavior that uses data from the full model rather than just an individual column.

Most of the time you wouldn't build your own column type from scratch, but rather extend and modify one of the existing column type classes.  In the following example, we're going to extend the `clearskies.column_types.Email` class to add some functionality related to the user's email.

# Input Checking
