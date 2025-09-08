#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookings_quality.settings')
django.setup()

from quality_monitor.models import Booking, KQOffice, KQStaff, TravelAgency

# Delete all data
print("Deleting all existing data...")
Booking.objects.all().delete()
KQStaff.objects.all().delete()
KQOffice.objects.all().delete()
TravelAgency.objects.all().delete()

print("All data cleared successfully!")