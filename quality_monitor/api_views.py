from django.http import JsonResponse
from django.db.models import Count, Avg, Q
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from .models import PNR, Contact, Passenger
from .utils import get_quality_score_annotation

@api_view(['GET'])
@throttle_classes([UserRateThrottle])
def get_channel_groupings(request):
    """Get channel groupings based on delivery systems"""
    delivery_systems = PNR.objects.values_list('delivery_system_company', flat=True).distinct().order_by('delivery_system_company')
    
    # Map delivery systems to channel groupings using list comprehension
    direct_channels = [{'id': ds, 'label': ds} for ds in delivery_systems if ds and ds in ['KQ', 'WEB', 'MOB']]
    indirect_channels = [{'id': ds, 'label': ds} for ds in delivery_systems if ds and ds not in ['KQ', 'WEB', 'MOB']]
    
    return Response({
        'groupings': [
            {
                'id': 'direct',
                'label': 'Direct Channels',
                'channels': direct_channels
            },
            {
                'id': 'indirect',
                'label': 'Indirect Channels',
                'channels': indirect_channels
            }
        ]
    })

@api_view(['GET'])
@throttle_classes([UserRateThrottle])
def get_offices_by_channels(request):
    """Get offices available for selected channels"""
    channels = request.GET.getlist('channels')
    
    pnrs = PNR.objects.all()
    if channels:
        # Sanitize channel inputs
        clean_channels = [ch.strip() for ch in channels if ch.strip()]
        if clean_channels:
            pnrs = pnrs.filter(delivery_system_company__in=clean_channels)
    
    offices_from_pnr = pnrs.filter(office_id__isnull=False).values('office_id').distinct().order_by('office_id')
    offices = [{'office_id': o['office_id'], 'name': o['office_id']} for o in offices_from_pnr]
    
    return Response({'offices': offices})

@api_view(['GET'])
@throttle_classes([UserRateThrottle])
def get_channel_office_stats(request):
    """Get booking statistics for selected channels and offices"""
    channels = request.GET.getlist('channels')
    office_ids = request.GET.getlist('offices')
    
    pnrs = PNR.objects.all()
    
    # Sanitize and validate inputs
    if office_ids:
        clean_offices = [office.strip() for office in office_ids if office.strip()]
        if clean_offices:
            pnrs = pnrs.filter(office_id__in=clean_offices)
    
    if channels:
        clean_channels = [ch.strip() for ch in channels if ch.strip()]
        if clean_channels:
            pnrs = pnrs.filter(delivery_system_company__in=clean_channels)
    
    # Calculate quality scores using the utility function
    quality_score_annotation = get_quality_score_annotation()
    pnrs_with_score = pnrs.annotate(calculated_quality_score=quality_score_annotation)
    
    stats = pnrs_with_score.aggregate(
        total_bookings=Count('id'),
        avg_quality=Avg('calculated_quality_score'),
        with_contacts=Count('id', filter=Q(contact__isnull=False))
    )
    
    return Response(stats)