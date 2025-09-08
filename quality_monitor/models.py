from django.db import models
from django.utils.html import escape

class TravelAgency(models.Model):
    iata_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.iata_code})"
    
    class Meta:
        verbose_name_plural = "Travel Agencies"

class KQOffice(models.Model):
    office_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    manager = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.office_id})"

class KQStaff(models.Model):
    staff_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    office = models.ForeignKey(KQOffice, on_delete=models.CASCADE, related_name='staff')
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.staff_id})"

class Booking(models.Model):
    CHANNEL_TYPE_CHOICES = [
        ('direct', 'Direct'),
        ('indirect', 'Indirect'),
    ]
    
    DIRECT_OFFICE_CHOICES = [
        ('website', 'Website'),
        ('mobile', 'Mobile'),
        ('ato', 'ATO'),
        ('cto', 'CTO'),
        ('cec', 'Contact Center (CEC)'),
        ('kq_gsa', 'KQ GSA'),
    ]
    
    INDIRECT_OFFICE_CHOICES = [
        ('agents', 'Agents'),
        ('ndc', 'NDC'),
        ('msafiri_connect', 'Msafiri-Connect'),
    ]
    
    pnr = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    ff_number = models.CharField("Frequent Flyer Number", max_length=20, blank=True)
    meal_selection = models.CharField(max_length=50, blank=True)
    seat = models.CharField(max_length=10, blank=True)
    channel_type = models.CharField(max_length=10, choices=CHANNEL_TYPE_CHOICES, default='direct')
    office_type = models.CharField(max_length=20, blank=True)
    departure_date = models.DateField(null=True, blank=True)
    
    # Channel-specific relationships
    kq_office = models.ForeignKey(KQOffice, on_delete=models.SET_NULL, null=True, blank=True)
    kq_staff = models.ForeignKey(KQStaff, on_delete=models.SET_NULL, null=True, blank=True)
    travel_agency = models.ForeignKey(TravelAgency, on_delete=models.SET_NULL, null=True, blank=True)
    
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
    
    @property
    def booking_agent(self):
        """Return the booking agent based on channel"""
        if self.channel_type == 'direct' and self.kq_staff:
            return self.kq_staff.name
        elif self.channel_type == 'indirect' and self.travel_agency:
            return self.travel_agency.name
        return self.office_type or 'Direct Booking'
    
    def clean(self):
        """Validate channel-specific data"""
        from django.core.exceptions import ValidationError
        
        if self.channel_type == 'direct':
            if self.office_type not in [choice[0] for choice in self.DIRECT_OFFICE_CHOICES]:
                raise ValidationError("Direct channels must have a valid direct office type")
            # Clear indirect data
            self.travel_agency = None
        elif self.channel_type == 'indirect':
            if self.office_type not in [choice[0] for choice in self.INDIRECT_OFFICE_CHOICES]:
                raise ValidationError("Indirect channels must have a valid indirect office type")
            # Clear direct staff for indirect bookings
            if self.office_type != 'agents':
                self.kq_staff = None
                self.kq_office = None