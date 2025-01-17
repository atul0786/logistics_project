#!/usr/bin/env bash

# Stop script execution if a command fails
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Apply migrations with conflict resolution
python manage.py migrate --fake-initial

# Collect static files
python manage.py collectstatic --noinput
