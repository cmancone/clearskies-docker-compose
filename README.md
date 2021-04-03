# Clearskies via uwsgi and docker compose

This repository shows various uses-cases for clearskies.  It uses [uwsgi](https://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html) to serve the clearskies application and [docker-compose](https://docs.docker.com/compose/) to launch it locally and coordinate necessary databases and microservices.  This is divided into examples that each highlight one step in building a more complicated application. Each example is in its own directory and contains a fully functional docker-compose setup along with a README.md file walking through the additions.

## Examples

 1. [Building a simple, public, restful, users API](./example_1_restful_users)
 2. [Adding in business logic](./example_2_business_logic)
 3. [Tests!](./example_3_tests)
