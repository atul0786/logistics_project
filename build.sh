#!/usr/bin/env bash

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Faking initial migrations to avoid table conflicts..."
python manage.py migrate --fake-initial
