from django.db import models

# Create your models here.

class Booking(models.Model):
    pnr = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    ff_number = models.CharField("Frequent Flyer Number", max_length=20, blank=True)
    meal_selection = models.CharField(max_length=50, blank=True)
    seat = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PNR: {self.pnr}"
