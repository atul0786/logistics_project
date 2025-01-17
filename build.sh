#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Make and run migrations, handling conflicts
python manage.py makemigrations
python manage.py migrate --fake-initial
