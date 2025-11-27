#!/bin/bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn procure_to_pay.wsgi:application --bind 0.0.0.0:8000
