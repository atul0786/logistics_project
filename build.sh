#!/usr/bin/env bash

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running migrations with --fake-initial to avoid conflicts..."
python manage.py migrate --fake-initial

echo "Collecting static files..."
python manage.py collectstatic --noinput
