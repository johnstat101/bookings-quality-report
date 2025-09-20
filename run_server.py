#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line
from django.conf import settings

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookings_quality.settings')
    execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])