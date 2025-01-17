#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run database migrations safely
python manage.py migrate --fake-initial

# Run migrations to apply pending changes
python manage.py migrate

# Collect static files without user input
python manage.py collectstatic --noinput
