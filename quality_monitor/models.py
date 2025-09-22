from django.db import models
from django.db.models import Q
import re

class PNR(models.Model):
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
        ]
    

    
    @property
    def has_valid_contacts(self):
        """Check if PNR has at least one valid contact"""
        for contact in self.contacts.all():
            if contact.is_valid_email or contact.is_valid_phone:
                return True
        return False
    
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
              contact_detail__regex=r'^[a-zA-Z0-9._%+-]+(@|//)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') |
            Q(contact_type__in=Contact.PHONE_VALID_TYPES, 
              contact_detail__regex=r'^\+?[0-9\s-]{7,20}$')
        ).exists()
    
    @property
    def has_wrongly_placed_contacts(self):
        """Check if PNR has contacts in wrong contact types - optimized"""
        return self.contacts.filter(
            Q(contact_detail__contains='@') & ~Q(contact_type__in=Contact.EMAIL_VALID_TYPES) |
            Q(contact_detail__regex=r'\d{7,}') & ~Q(contact_type__in=Contact.PHONE_VALID_TYPES)
        ).exists()
    
    # Removed redundant is_reachable property - use has_valid_contacts directly
    
    @property
    def quality_score(self):
        """Calculate quality score - use annotation for better performance"""
        from .utils import get_quality_score_annotation
        # For individual instances, calculate directly
        score = 0
        if self.has_valid_contacts:
            score += 40
        if self.passengers.filter(ff_number__gt='').exists():
            score += 20
        if self.passengers.filter(meal__gt='').exists():
            score += 20
        if self.passengers.filter(seat_row_number__gt='', seat_column__gt='').exists():
            score += 20
        return score

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

class Contact(models.Model):
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
        if not self.is_email:
            return False
        
        # Check if contact type is valid for email
        if self.contact_type not in self.EMAIL_VALID_TYPES:
            return False
        
        # Basic email format validation with // support
        email = self.contact_detail.replace('//', '@')
        # Remove any prefixes like "KQ/E+" or "KQ/M+"
        email = Contact.PREFIX_PATTERN.sub('', email)
        # Remove any suffixes like "/EN"
        email = Contact.SUFFIX_PATTERN.sub('', email)
        
        return bool(re.match(Contact.EMAIL_PATTERN, email))
    
    @property
    def is_valid_phone(self):
        """Check if phone is valid and in correct contact type"""
        if not self.is_phone:
            return False
        
        # Check if contact type is valid for phone
        if self.contact_type not in self.PHONE_VALID_TYPES:
            return False
        
        # Clean phone number - remove prefixes and suffixes
        phone = self.contact_detail
        phone = Contact.PREFIX_PATTERN.sub('', phone)  # Remove "KQ/M+" etc
        phone = Contact.SUFFIX_PATTERN.sub('', phone)  # Remove "/EN" etc
        phone = re.sub(r'-[A-Z]$', '', phone)  # Remove "-M", "-S" etc
        
        # Use consistent phone validation pattern
        return bool(re.match(r'^\+?[0-9\s-]{7,20}$', phone.strip()))
    
    @property
    def is_wrongly_placed(self):
        """Check if contact is in wrong contact type"""
        if self.is_email and self.contact_type not in self.EMAIL_VALID_TYPES:
            return True
        if self.is_phone and self.contact_type not in self.PHONE_VALID_TYPES:
            return True
        return False

    @classmethod
    def get_valid_contact_q(cls):
        """
        Returns a Q object for filtering valid contacts (email or phone).
        """
        valid_email_q = Q(contact_type__in=cls.EMAIL_VALID_TYPES, contact_detail__regex=r'^[a-zA-Z0-9._%+-]+(@|//)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        valid_phone_q = Q(contact_type__in=cls.PHONE_VALID_TYPES, contact_detail__regex=r'^\+?[0-9\s-]{7,20}$')
        return valid_email_q | valid_phone_q

    
    def __str__(self):
        return f"{self.contact_type}: {self.contact_detail}"
    
    class Meta:
        indexes = [
            models.Index(fields=['contact_type', 'contact_detail']),
        ]