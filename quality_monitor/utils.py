from django.db.models import Case, When, IntegerField, Q, Value
from django.db.models.expressions import Exists, OuterRef

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
    from .models import Contact, Passenger

    # Subquery to check for at least one valid contact
    has_valid_contact = Exists(
        Contact.objects.filter(
            Contact.get_valid_contact_q(),
            pnr=OuterRef('pk')
        )
    )
    
    # Subquery to check for at least one passenger with a frequent flyer number
    has_ff_number = Exists(Passenger.objects.filter(pnr=OuterRef('pk'), ff_number__isnull=False).exclude(ff_number=''))
    
    # Subquery to check for at least one passenger with a meal selection
    has_meal = Exists(Passenger.objects.filter(pnr=OuterRef('pk'), meal__isnull=False).exclude(meal=''))
    
    # Subquery to check for at least one passenger with a seat assignment
    has_seat = Exists(Passenger.objects.filter(pnr=OuterRef('pk'), seat_row_number__isnull=False, seat_column__isnull=False).exclude(seat_row_number='').exclude(seat_column=''))

    return (
        # Contact validation (40 points)
        Case(When(has_valid_contact, then=Value(40)), default=Value(0), output_field=IntegerField()) +
        # Frequent Flyer number (20 points)
        Case(When(has_ff_number, then=Value(20)), default=Value(0), output_field=IntegerField()) +
        # Meal selection (20 points)
        Case(When(has_meal, then=Value(20)), default=Value(0), output_field=IntegerField()) +
        # Seat assignment (20 points): Both row and column required
        Case(When(has_seat, then=Value(20)), default=Value(0), output_field=IntegerField())
    )