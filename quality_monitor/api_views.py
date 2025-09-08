from django.http import JsonResponse
from django.db.models import Count, Avg, Case, When, IntegerField, Q
from .models import Booking, KQOffice, KQStaff

def get_channel_groupings(request):
    """Get channel groupings for filtering"""
    return JsonResponse({
        'groupings': [
            {
                'id': 'direct',
                'label': 'Direct Channels',
                'channels': [{'id': ch, 'label': dict(Booking.CHANNEL_CHOICES)[ch]} for ch in Booking.DIRECT_CHANNELS]
            },
            {
                'id': 'indirect', 
                'label': 'Indirect Channels',
                'channels': [{'id': ch, 'label': dict(Booking.CHANNEL_CHOICES)[ch]} for ch in Booking.INDIRECT_CHANNELS]
            }
        ]
    })

def get_offices_by_channels(request):
    """Get offices available for selected channels"""
    channels = request.GET.getlist('channels')
    
    if not channels:
        return JsonResponse({'offices': []})
    
    office_ids = set()
    
    for channel in channels:
        if channel in Booking.OFFICE_CHANNELS:
            # Website/Mobile: all offices
            office_ids.update(KQOffice.objects.values_list('office_id', flat=True))
        elif channel in Booking.STAFF_CHANNELS:
            # Staff channels: offices with staff
            office_ids.update(
                KQOffice.objects.filter(staff__isnull=False)
                .distinct().values_list('office_id', flat=True)
            )
    
    offices = list(KQOffice.objects.filter(
        office_id__in=office_ids
    ).values('office_id', 'name').order_by('name'))
    
    return JsonResponse({'offices': offices})

def get_channel_office_stats(request):
    """Get booking statistics by channel and office"""
    channels = request.GET.getlist('channels')
    office_ids = request.GET.getlist('offices')
    
    bookings = Booking.objects.all()
    
    if channels:
        bookings = bookings.filter(channel__in=channels)
    
    if office_ids:
        bookings = bookings.filter(kq_office__office_id__in=office_ids)
    
    quality_calc = (
        Case(When(phone__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(email__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(ff_number__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(meal_selection__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(seat__gt='', then=20), default=0, output_field=IntegerField())
    )
    
    stats = bookings.aggregate(
        total_bookings=Count('id'),
        avg_quality=Avg(quality_calc),
        with_contacts=Count('id', filter=Q(phone__gt='') | Q(email__gt=''))
    )
    
    return JsonResponse(stats)