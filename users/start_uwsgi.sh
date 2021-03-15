#!/usr/bin/env bash
wait-for-it db:3306
mygrate.py apply
uwsgi --http :5000 --wsgi-file api.py --master --processes 2 --threads 1
