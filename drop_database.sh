#!/usr/bin/env bash
dropdb MoneyServer
rm -r game/migrations
rm -r dashboard/migrations
createdb MoneyServer --owner dasein
python manage.py makemigrations dashboard game
python manage.py migrate
# python manage.py createsuperuser