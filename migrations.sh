#!/usr/bin/env bash
python manage.py flush
python manage.py makemigrations dashboard game
python manage.py migrate
