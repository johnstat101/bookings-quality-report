from django.db import models
from django.db.models import Q, Count, Avg
from django.core.exceptions import ValidationError
import re

class PNRManager(models.Manager):
    def with_quality_score(self):
        """Annotate PNRs with quality score for efficient querying"""
        from .utils import get_quality_score_annotation
        return self.annotate(quality_score=get_quality_score_annotation())
    
    def with_valid_contacts(self):
        """Filter PNRs that have valid contacts"""
        return self.filter(contacts__in=Contact.objects.valid_contacts()).distinct()
    
    def by_delivery_system(self, systems):
        """Filter by delivery systems with validation"""
        if not systems:
            return self.all()
        clean_systems = [s.strip() for s in systems if s.strip()]
        return self.filter(delivery_system_company__in=clean_systems) if clean_systems else self.all()
    
    def by_offices(self, offices):
        """Filter by offices with validation"""
        if not offices:
            return self.all()
        clean_offices = [o.strip() for o in offices if o.strip()]
        return self.filter(office_id__in=clean_offices) if clean_offices else self.all()
    
    def get_or_create_pnr(self, control_number, defaults=None):
        """Get or create PNR with proper handling of control number uniqueness"""
        try:
            return self.get(control_number=control_number), False
        except self.model.DoesNotExist:
            if defaults:
                return self.create(control_number=control_number, **defaults), True
            return None, False

class ContactManager(models.Manager):
    def valid_contacts(self):
        """Return only valid contacts (email or phone)"""
        return self.filter(Contact.get_valid_contact_q())
    
    def invalid_format(self):
        """Return contacts with invalid format"""
        return self.exclude(Contact.get_valid_contact_q()).exclude(contact_detail__exact='')

class PNR(models.Model):
    objects = PNRManager()
    """
    Passenger Name Record (PNR) - Main booking record.
    
    Represents a single booking with associated passengers and contacts.
    Quality score is calculated based on completeness of contact details,
    frequent flyer numbers, meal selections, and seat assignments.
    """
    control_number = models.CharField(max_length=20, unique=True, db_index=True)
    office_id = models.CharField(max_length=20, blank=True, db_index=True)
    agent = models.CharField(max_length=20, blank=True)
    creation_date = models.DateField(null=True, blank=True, db_index=True) # Changed to DateField
    creator_iata_code = models.CharField(max_length=20, blank=True)
    delivery_system_company = models.CharField(max_length=10, blank=True, db_index=True)
    delivery_system_location = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"PNR: {self.control_number}"
    
    class Meta:
        indexes = [
            models.Index(fields=['creation_date', 'office_id']),
            models.Index(fields=['delivery_system_company', 'creation_date']),
            models.Index(fields=['office_id', 'delivery_system_company']),  # For dynamic filtering
        ]
    

    
    @property
    def has_valid_contacts(self):
        """Check if PNR has at least one valid contact - optimized"""
        return self.contacts.filter(Contact.get_valid_contact_q()).exists()
    
    @property
    def has_missing_contacts(self):
        return not self.contacts.exists()
    
    @property
    def has_wrong_format_contacts(self):
        """Check if PNR has contacts with wrong format - supports // operator for emails"""
        return self.contacts.filter(
            contact_detail__isnull=False
        ).exclude(
            Q(contact_type__in=Contact.EMAIL_VALID_TYPES, 
              contact_detail__regex=r'^[a-zA-Z0-9._%+\-/]+(@|//)[a-zA-Z0-9.\-/]+\.[a-zA-Z]{2,}$') |
            Q(contact_type__in=Contact.PHONE_VALID_TYPES, 
              contact_detail__regex=r'^\+?[0-9\s-]{7,20}$')
        ).exists()
    
    @property
    def has_wrongly_placed_contacts(self):
        """Check if PNR has contacts in wrong contact types - only CTCE/CTCM misplacement"""
        return self.contacts.filter(
            # Email in phone-only field (CTCM)
            Q(contact_type__exact='CTCM', contact_detail__contains='@') |
            Q(contact_type__exact='CTCM', contact_detail__contains='//') |
            # Phone in email-only field (CTCE) - check for phone patterns but exclude emails
            (Q(contact_type__exact='CTCE', contact_detail__regex=r'^(?:[A-Z]{2,3}/[A-Z]\+)?\+?[0-9][0-9\s\-\(\)]{6,}$') & ~Q(contact_detail__contains='@') & ~Q(contact_detail__contains='//'))
        ).exists()
    
    # Removed redundant is_reachable property - use has_valid_contacts directly
    
    @property
    def quality_score(self):
        """Calculate quality score - use annotation for better performance"""
        # For individual instances, calculate directly with bounds checking
        score = 0
        if self.has_valid_contacts:
            score += 40
        if self.passengers.filter(ff_number__gt='').exists():
            score += 20
        if self.passengers.filter(meal__gt='').exists():
            score += 20
        if self.passengers.filter(seat_row_number__gt='', seat_column__gt='').exists():
            score += 20
        # Ensure score is within valid range [0, 100]
        return min(100, max(0, score))
    
    def clean(self):
        """Validate PNR data before saving"""
        super().clean()
        if not self.control_number or not self.control_number.strip():
            raise ValidationError('Control number cannot be empty')
        self.control_number = self.control_number.strip()
    
    def save(self, *args, **kwargs):
        """Override save to ensure data validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def update_passenger_details(self, passenger_data_list):
        """Update multiple passengers for this PNR"""
        for passenger_data in passenger_data_list:
            passenger, created = self.passengers.get_or_create(
                surname=passenger_data.get('surname', ''),
                first_name=passenger_data.get('first_name', ''),
                defaults={
                    'ff_number': passenger_data.get('ff_number', ''),
                    'meal': passenger_data.get('meal', ''),
                    'seat_row_number': passenger_data.get('seat_row_number', ''),
                    'seat_column': passenger_data.get('seat_column', ''),
                }
            )
            if not created:
                for field, value in passenger_data.items():
                    if hasattr(passenger, field):
                        setattr(passenger, field, value)
                passenger.save()
    
    def update_contact_information(self, contact_data_list):
        """Update contact information for this PNR"""
        for contact_data in contact_data_list:
            self.contacts.get_or_create(
                contact_type=contact_data.get('contact_type', ''),
                contact_detail=contact_data.get('contact_detail', ''),
            )
    
    @classmethod
    def get_reachable_pnrs(cls):
        """Get PNRs that have at least one valid contact"""
        return cls.objects.filter(Contact.get_valid_contact_q('contacts__')).distinct()
    
    @classmethod
    def get_unreachable_pnrs(cls):
        """Get PNRs without valid contacts"""
        return cls.objects.exclude(Contact.get_valid_contact_q('contacts__')).distinct()
    
    @classmethod
    def get_pnrs_with_invalid_contacts(cls):
        """Get all PNR-contact combinations with invalid formats (allows duplicates)"""
        return cls.objects.filter(
            contacts__contact_detail__isnull=False
        ).exclude(
            Contact.get_valid_contact_q('contacts__')
        ).select_related().prefetch_related('contacts')
    
    @classmethod
    def get_analytics_summary(cls):
        """Get comprehensive analytics summary considering multiple passengers per PNR"""
        total_pnrs = cls.objects.count()
        reachable_pnrs = cls.get_reachable_pnrs().count()
        total_passengers = Passenger.objects.count()
        
        passengers_with_meals = Passenger.objects.exclude(meal='').count()
        passengers_with_ff = Passenger.objects.exclude(ff_number='').count()
        passengers_with_seats = Passenger.objects.exclude(
            Q(seat_row_number='') | Q(seat_column='')
        ).count()
        
        return {
            'total_pnrs': total_pnrs,
            'total_passengers': total_passengers,
            'reachable_pnrs': reachable_pnrs,
            'unreachable_pnrs': total_pnrs - reachable_pnrs,
            'reachability_percentage': min(100, max(0, (reachable_pnrs / total_pnrs * 100))) if total_pnrs > 0 else 0,
            'passengers_with_meals': passengers_with_meals,
            'passengers_with_ff': passengers_with_ff,
            'passengers_with_seats': passengers_with_seats,
            'meal_completion_rate': min(100, max(0, (passengers_with_meals / total_passengers * 100))) if total_passengers > 0 else 0,
        }

class Passenger(models.Model):
    """
    Passenger information associated with a PNR.
    
    Contains personal details, frequent flyer information,
    travel preferences (meal, seat), and journey details.
    """
    pnr = models.ForeignKey(PNR, on_delete=models.CASCADE, related_name='passengers')
    surname = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    ff_number = models.CharField(max_length=20, blank=True)
    ff_tier = models.CharField(max_length=20, blank=True)
    board_point = models.CharField(max_length=10, blank=True)
    off_point = models.CharField(max_length=10, blank=True)
    seat_row_number = models.CharField(max_length=10, blank=True)
    seat_column = models.CharField(max_length=10, blank=True)
    meal = models.CharField(max_length=20, blank=True)
    
    @property
    def seat(self):
        """Combine seat row and column"""
        if self.seat_row_number and self.seat_column:
            return f"{self.seat_row_number}{self.seat_column}"
        return ''
    
    def __str__(self):
        return f"{self.surname}, {self.first_name}"
    
    class Meta:
        unique_together = ['pnr', 'surname', 'first_name']
        indexes = [
            models.Index(fields=['pnr', 'surname', 'first_name']),
        ]
    
    def update_meal_selection(self, meal_code):
        """Update meal selection for this passenger"""
        self.meal = meal_code
        self.save(update_fields=['meal'])
    
    def has_complete_details(self):
        """Check if passenger has all required details"""
        return all([
            self.surname,
            self.first_name,
            self.ff_number,
            self.meal,
            self.seat_row_number,
            self.seat_column
        ])

class Contact(models.Model):
    objects = ContactManager()
    """
    Contact information for PNR communication.
    
    Supports various contact types (AP, APE, APM, CTCE, CTCM) with
    validation for proper email and phone number formats.
    Handles both @ and // operators for email addresses.
    """
    CONTACT_TYPE_CHOICES = [
        ('AP', 'AP'),
        ('APE', 'APE'), # Email
        ('APM', 'APM'), # Phone
        ('CTCE', 'CTCE'),
        ('CTCEM', 'CTCEM'),
        ('CTCM', 'CTCM'),
    ]
    
    # Valid contact types for each contact method
    EMAIL_VALID_TYPES = ['AP', 'APE', 'CTCE']  # AP=generic, APE=email, CTCE=email
    PHONE_VALID_TYPES = ['AP', 'APM', 'CTCM']  # AP=generic, APM=phone, CTCM=phone
    
    # Pre-compiled regex patterns for performance optimization
    PREFIX_PATTERN = re.compile(r'^[A-Z]+/[A-Z]\+')  # Matches "KQ/M+", "KQ/E+" prefixes
    SUFFIX_PATTERN = re.compile(r'/[A-Z]+$')         # Matches "/EN", "/FR" suffixes
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$')

    pnr = models.ForeignKey(PNR, on_delete=models.CASCADE, related_name='contacts')
    contact_type = models.CharField(max_length=10, choices=CONTACT_TYPE_CHOICES, db_index=True)
    contact_detail = models.CharField(max_length=200, db_index=True)
    
    @property
    def is_email(self):
        """Check if contact appears to be an email with better validation"""
        detail = self.contact_detail.lower()
        # More robust email detection
        return ('@' in detail and '.' in detail) or ('//' in detail and '.' in detail)
    
    @property
    def is_phone(self):
        """Check if contact appears to be a phone number"""
        # Check for phone indicators or if it contains mostly digits
        detail = self.contact_detail.lower()
        
        # Check for phone prefixes or suffixes
        if any(indicator in detail for indicator in ['-m', '-s', 'tel', 'phone', 'mobile']):
            return True
            
        # Remove common phone separators and check if mostly digits
        cleaned = re.sub(r'[\s\-\+\(\)\.\,]', '', self.contact_detail)
        # Remove prefixes like "KQ/M+" or "KQ/E+"
        cleaned = Contact.PREFIX_PATTERN.sub('', cleaned)
        # Remove suffixes like "/EN"
        cleaned = Contact.SUFFIX_PATTERN.sub('', cleaned)
        
        # Count digits
        digit_count = sum(c.isdigit() for c in cleaned)
        return len(cleaned) > 0 and digit_count / len(cleaned) > 0.7 and digit_count >= 7
    
    @property
    def is_valid_email(self):
        """Check if email is valid and in correct contact type"""
        if not self.is_email or self.contact_type not in self.EMAIL_VALID_TYPES:
            return False
        
        # Clean email - handle // operator and remove prefixes/suffixes
        email = self.contact_detail.replace('//', '@')
        email = Contact.PREFIX_PATTERN.sub('', email)
        email = Contact.SUFFIX_PATTERN.sub('', email)
        email = re.sub(r'-[A-Z]$', '', email)  # Remove trailing -M, -S etc
        
        return bool(re.match(Contact.EMAIL_PATTERN, email.strip()))
    
    @property
    def is_valid_phone(self):
        """Check if phone is valid and in correct contact type"""
        if not self.is_phone or self.contact_type not in self.PHONE_VALID_TYPES:
            return False
        
        # Clean phone number - remove all prefixes and suffixes
        phone = self.contact_detail
        phone = Contact.PREFIX_PATTERN.sub('', phone)
        phone = Contact.SUFFIX_PATTERN.sub('', phone)
        phone = re.sub(r'-[A-Z]$', '', phone)
        
        # Enhanced phone validation pattern
        return bool(re.match(r'^\+?[0-9\s\-\(\)]{7,25}$', phone.strip()))
    
    @property
    def is_wrongly_placed(self):
        """Check if contact is in wrong contact type"""
        if self.is_email and self.contact_type not in self.EMAIL_VALID_TYPES:
            return True
        if self.is_phone and self.contact_type not in self.PHONE_VALID_TYPES:
            return True
        return False

    @classmethod
    def get_valid_contact_q(cls, prefix=''):
        """
        Returns a Q object for filtering valid contacts with improved patterns.
        Args:
            prefix: Field prefix for cross-model queries (e.g., 'contacts__')
        """
        # Enhanced email pattern supporting prefixes/suffixes, // operator, and ./ replacement for - in both username and domain
        email_pattern = r'^(?:[A-Z]{2,3}/[A-Z]\+)?[a-zA-Z0-9._%+\-/]+(@|//)[a-zA-Z0-9.\-/]+\.[a-zA-Z]{2,}(?:/[A-Z]{2})?(?:-[A-Z])?$'
        # Enhanced phone pattern supporting prefixes/suffixes
        phone_pattern = r'^(?:[A-Z]{2,3}/[A-Z]\+)?\+?[0-9\s\-\(\)]{7,25}(?:-[A-Z])?(?:/[A-Z]{2})?$'
        
        contact_type_field = f'{prefix}contact_type__in'
        contact_detail_field = f'{prefix}contact_detail__regex'
        
        valid_email_q = Q(**{contact_type_field: cls.EMAIL_VALID_TYPES, contact_detail_field: email_pattern})
        valid_phone_q = Q(**{contact_type_field: cls.PHONE_VALID_TYPES, contact_detail_field: phone_pattern})
        return valid_email_q | valid_phone_q

    
    def __str__(self):
        return f"{self.contact_type}: {self.contact_detail}"
    
    class Meta:
        indexes = [
            models.Index(fields=['contact_type', 'contact_detail']),
        ]
    
    @classmethod
    def get_analytics_by_delivery_system(cls):
        """Get analytics grouped by delivery system considering multiple passengers"""
        from .utils import get_quality_score_annotation
        return PNR.objects.values('delivery_system_company').annotate(
            total_pnrs=Count('id', distinct=True),
            total_passengers=Count('passengers', distinct=True),
            reachable_pnrs=Count('pk', filter=cls.get_valid_contact_q('contacts__'), distinct=True),
            avg_quality=Avg(get_quality_score_annotation())
        ).order_by('-total_pnrs')
    
    @classmethod
    def get_analytics_by_office(cls):
        """Get analytics grouped by office considering multiple passengers"""
        from .utils import get_quality_score_annotation
        return PNR.objects.values('office_id').annotate(
            total_pnrs=Count('id', distinct=True),
            total_passengers=Count('passengers', distinct=True),
            reachable_pnrs=Count('pk', filter=cls.get_valid_contact_q('contacts__'), distinct=True),
            avg_quality=Avg(get_quality_score_annotation())
        ).order_by('-total_pnrs')
    
    @classmethod
    def get_invalid_contact_details(cls):
        """Get all invalid contacts with PNR details (allows multiple rows per PNR)"""
        return cls.objects.filter(
            contacts__contact_detail__isnull=False
        ).exclude(
            cls.get_valid_contact_q('contacts__')
        ).values(
            'control_number',
            'office_id', 
            'delivery_system_company',
            'contacts__contact_type',
            'contacts__contact_detail'
        )


# Utility functions for PNR management and analytics
def get_filtered_pnrs_for_download(filter_type, queryset=None):
    """Get filtered PNRs for download based on filter type"""
    if queryset is None:
        queryset = PNR.objects.prefetch_related('passengers', 'contacts')
    
    from .utils import get_quality_score_annotation
    
    FILTER_MAPPING = {
        'reachable': lambda qs: qs.filter(Contact.get_valid_contact_q('contacts__')).distinct(),
        'unreachable': lambda qs: qs.exclude(Contact.get_valid_contact_q('contacts__')).distinct(),
        'invalid_contacts': lambda qs: qs.filter(
            Q(contacts__contact_detail__isnull=False) & ~Contact.get_valid_contact_q('contacts__')
        ),  # Remove distinct() to show all invalid contact rows
        'high_quality': lambda qs: qs.annotate(
            quality=get_quality_score_annotation()
        ).filter(quality__gte=80),
        'low_quality': lambda qs: qs.annotate(
            quality=get_quality_score_annotation()
        ).filter(quality__lt=60),
        'multiple_passengers': lambda qs: qs.annotate(
            passenger_count=Count('passengers')
        ).filter(passenger_count__gt=1),
    }
    
    filter_func = FILTER_MAPPING.get(filter_type)
    return filter_func(queryset) if filter_func else queryset


def bulk_update_passenger_meals(pnr_passenger_meals):
    """Bulk update meal selections for multiple passengers"""
    passengers_to_update = []
    for pnr_id, passenger_meals in pnr_passenger_meals.items():
        for passenger_id, meal_code in passenger_meals.items():
            try:
                passenger = Passenger.objects.get(id=passenger_id, pnr_id=pnr_id)
                passenger.meal = meal_code
                passengers_to_update.append(passenger)
            except Passenger.DoesNotExist:
                continue
    
    if passengers_to_update:
        Passenger.objects.bulk_update(passengers_to_update, ['meal'], batch_size=100)
    
    return len(passengers_to_update)


def get_pnr_analytics_data():
    """Get comprehensive analytics data for dashboard considering multiple passengers"""
    from .utils import get_quality_score_annotation
    from .cache_utils import get_cache_key, get_cached_analytics, cache_analytics_data
    
    cache_key = get_cache_key('analytics_data')
    cached_data = get_cached_analytics(cache_key)
    if cached_data:
        return cached_data
    
    total_pnrs = PNR.objects.count()
    total_passengers = Passenger.objects.count()
    reachable_pnrs = PNR.get_reachable_pnrs().count()
    
    # Quality distribution
    quality_ranges = PNR.objects.annotate(
        quality=get_quality_score_annotation()
    ).aggregate(
        range1=Count('pk', filter=Q(quality__lte=20)),
        range2=Count('pk', filter=Q(quality__gt=20, quality__lte=40)),
        range3=Count('pk', filter=Q(quality__gt=40, quality__lte=60)),
        range4=Count('pk', filter=Q(quality__gt=60, quality__lte=80)),
        range5=Count('pk', filter=Q(quality__gt=80)),
    )
    
    # Passenger-level analytics
    passenger_stats = {
        'total_passengers': total_passengers,
        'passengers_with_meals': Passenger.objects.exclude(meal='').count(),
        'passengers_with_ff': Passenger.objects.exclude(ff_number='').count(),
        'passengers_with_seats': Passenger.objects.exclude(
            Q(seat_row_number='') | Q(seat_column='')
        ).count(),
    }
    
    return {
        'total_pnrs': total_pnrs,
        'reachable_pnrs': reachable_pnrs,
        'unreachable_pnrs': total_pnrs - reachable_pnrs,
        'reachability_rate': min(100, max(0, (reachable_pnrs / total_pnrs * 100))) if total_pnrs > 0 else 0,
        'quality_distribution': quality_ranges,
        'passenger_stats': passenger_stats,
        'delivery_system_stats': Contact.get_analytics_by_delivery_system(),
        'office_stats': Contact.get_analytics_by_office(),
        'avg_passengers_per_pnr': round(total_passengers / total_pnrs, 2) if total_pnrs > 0 else 0,
    }