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
    CHANNEL_CHOICES = [
        # Direct channels
        ('website', 'Website'),
        ('mobile', 'Mobile'),
        ('ato', 'ATO'),
        ('cto', 'CTO'),
        ('cec', 'Contact Center (CEC)'),
        ('kq_gsa', 'KQ GSA'),
        # Indirect channels
        ('travel_agents', 'Travel Agents'),
        ('ndc', 'NDC'),
        ('msafiri_connect', 'Msafiri Connect'),
    ]
    
    DIRECT_CHANNELS = ['website', 'mobile', 'ato', 'cto', 'cec', 'kq_gsa']
    INDIRECT_CHANNELS = ['travel_agents', 'ndc', 'msafiri_connect']
    
    # Channel groupings for filtering
    CHANNEL_GROUPINGS = {
        'direct': {
            'label': 'Direct Channels',
            'channels': DIRECT_CHANNELS
        },
        'indirect': {
            'label': 'Indirect Channels', 
            'channels': INDIRECT_CHANNELS
        }
    }
    
    # Office requirements by channel
    OFFICE_CHANNELS = ['website', 'mobile']  # Channels that require office_id
    STAFF_CHANNELS = ['ato', 'cto', 'cec', 'kq_gsa', 'travel_agents', 'ndc', 'msafiri_connect']  # Channels that require staff_id
    
    pnr = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    ff_number = models.CharField("Frequent Flyer Number", max_length=20, blank=True)
    meal_selection = models.CharField(max_length=50, blank=True)
    seat = models.CharField(max_length=10, blank=True)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='website')
    departure_date = models.DateField(null=True, blank=True)
    
    # Channel-specific relationships
    kq_office = models.ForeignKey(KQOffice, on_delete=models.SET_NULL, null=True, blank=True)
    kq_staff = models.ForeignKey(KQStaff, on_delete=models.SET_NULL, null=True, blank=True)
    travel_agency = models.ForeignKey(TravelAgency, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return escape(f"PNR: {self.pnr}")
    
    class Meta:
        ordering = ['-created_at']
    
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
    def channel_type(self):
        """Return channel type (direct/indirect)"""
        return 'direct' if self.channel in self.DIRECT_CHANNELS else 'indirect'
    
    @property
    def office_id(self):
        """Return office ID based on channel"""
        if self.kq_office:
            return self.kq_office.office_id
        return None
    
    @property
    def staff_id(self):
        """Return staff ID"""
        if self.kq_staff:
            return self.kq_staff.staff_id
        return None
    
    @property
    def booking_agent(self):
        """Return the booking agent based on channel"""
        if self.kq_staff:
            return self.kq_staff.name
        elif self.travel_agency:
            return self.travel_agency.name
        elif self.kq_office:
            return self.kq_office.name
        return dict(self.CHANNEL_CHOICES).get(self.channel, 'Unknown')
    
    @classmethod
    def get_offices_for_channel(cls, channel):
        """Get available offices for a specific channel"""
        if channel in cls.OFFICE_CHANNELS:
            return KQOffice.objects.all()
        elif channel in cls.STAFF_CHANNELS:
            return KQOffice.objects.filter(staff__isnull=False).distinct()
        return KQOffice.objects.none()
    
    def clean(self):
        """Validate channel-specific data"""
        from django.core.exceptions import ValidationError
        
        if self.channel in self.OFFICE_CHANNELS:
            if not self.kq_office:
                raise ValidationError(f"{self.get_channel_display()} bookings must have an office")
        elif self.channel in self.STAFF_CHANNELS:
            if not self.kq_staff:
                raise ValidationError(f"{self.get_channel_display()} bookings must have a staff member")
            if self.channel == 'travel_agents' and not self.travel_agency:
                raise ValidationError("Travel agent bookings must have an associated agency")