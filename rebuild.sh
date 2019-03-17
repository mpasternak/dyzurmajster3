#!/bin/bash

dropdb dyzurmajster3

createdb dyzurmajster3

rm src/piony/migrations/*py
touch src/piony/migrations/__init__.py

rm src/profil/migrations/*py
touch src/profil/migrations/__init__.py

python src/manage.py makemigrations
python src/manage.py migrate

python src/manage.py jbozy_initial_data
