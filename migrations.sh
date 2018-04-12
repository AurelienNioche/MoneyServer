#!/usr/bin/env bash
python manage.py test game
python manage.py makemigrations dashboard game
python manage.py migrate