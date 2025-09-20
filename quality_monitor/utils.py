from django.db.models import Count, Case, When, IntegerField, Q
from .models import Contact

def get_quality_score_annotation():
    """
    Reusable quality score annotation for consistent calculation across views.
    
    Quality Score Breakdown:
    - Contact Details (40%): Valid phone or email in correct field types
    - Frequent Flyer Number (20%): Non-empty FF number
    - Meal Selection (20%): Non-empty meal code
    - Seat Assignment (20%): Both seat row and column present
    
    Returns Django annotation expression for use in querysets.
    """
    return (
        # Contact validation (40 points): Email with @ or // operator, or valid phone
        Case(
            When(
                Q(contacts__contact_type__in=Contact.EMAIL_VALID_TYPES, 
                  contacts__contact_detail__regex=r'^[a-zA-Z0-9._%+-]+(@|//)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') |
                Q(contacts__contact_type__in=Contact.PHONE_VALID_TYPES, 
                  contacts__contact_detail__regex=r'^\+?[0-9\s-]{7,20}$'),
                then=40
            ),
            default=0,
            output_field=IntegerField()
        ) +
        # Frequent Flyer number (20 points)
        Case(When(Q(passengers__ff_number__isnull=False) & ~Q(passengers__ff_number=''), 
                  then=20), default=0, output_field=IntegerField()) +
        # Meal selection (20 points)
        Case(When(Q(passengers__meal__isnull=False) & ~Q(passengers__meal=''), 
                  then=20), default=0, output_field=IntegerField()) +
        # Seat assignment (20 points): Both row and column required
        Case(When(Q(passengers__seat_row_number__isnull=False) & ~Q(passengers__seat_row_number='') & 
                  Q(passengers__seat_column__isnull=False) & ~Q(passengers__seat_column=''), 
                  then=20), default=0, output_field=IntegerField())
    )