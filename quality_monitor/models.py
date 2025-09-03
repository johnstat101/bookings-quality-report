from django.db import models
from django.utils.html import escape

class Booking(models.Model):
    CHANNEL_CHOICES = [
        ('web', 'Web'),
        ('mobile', 'Mobile App'),
        ('office', 'Own Office'),
        ('agency', 'Travel Agency'),
        ('ndc', 'NDC'),
    ]
    
    pnr = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    ff_number = models.CharField("Frequent Flyer Number", max_length=20, blank=True)
    meal_selection = models.CharField(max_length=50, blank=True)
    seat = models.CharField(max_length=10, blank=True)
    booking_channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='web')
    office_id = models.CharField(max_length=10, blank=True)
    agency_iata = models.CharField(max_length=10, blank=True)
    agency_name = models.CharField(max_length=100, blank=True)
    staff_id = models.CharField(max_length=10, blank=True)
    staff_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return escape(f"PNR: {self.pnr}")
    
    @property
    def quality_score(self):
        score = 0
        if self.phone: score += 20
        if self.email: score += 20
        if self.ff_number: score += 20
        if self.meal_selection: score += 20
        if self.seat: score += 20
        return score
    
    @property
    def has_contacts(self):
        return bool(self.phone or self.email)
