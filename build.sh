#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Make migrations (if needed)
python manage.py makemigrations

# Skip the problematic migration
python manage.py migrate --fake transporter_app 0006_ddmsummary_alter_partymaster_display_name_and_more

# Apply remaining migrations
python manage.py migrate
