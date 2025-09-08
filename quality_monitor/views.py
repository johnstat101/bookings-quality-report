from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Q, Case, When, IntegerField, Avg
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Booking, TravelAgency, KQOffice, KQStaff
import pandas as pd
import json

def get_filtered_bookings(request):
    bookings = Booking.objects.select_related('kq_office', 'kq_staff', 'travel_agency').all()
    
    # Date filters - only apply if values exist (open filter when empty)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    departure_start = request.GET.get('departure_start')
    departure_end = request.GET.get('departure_end')
    
    # Multi-select filters
    channel_types = request.GET.getlist('channel_types')
    office_types = request.GET.getlist('office_types')
    offices = request.GET.getlist('offices')
    
    # Apply filters only if values are provided
    if start_date and start_date.strip():
        bookings = bookings.filter(created_at__date__gte=start_date)
    if end_date and end_date.strip():
        bookings = bookings.filter(created_at__date__lte=end_date)
    if departure_start and departure_start.strip():
        bookings = bookings.filter(departure_date__gte=departure_start)
    if departure_end and departure_end.strip():
        bookings = bookings.filter(departure_date__lte=departure_end)
    if channel_types and len(channel_types) > 0:
        bookings = bookings.filter(channel_type__in=channel_types)
    if office_types and len(office_types) > 0:
        bookings = bookings.filter(office_type__in=office_types)
    if offices and len(offices) > 0:
        bookings = bookings.filter(kq_office__office_id__in=offices)
    
    return bookings

def home_view(request):
    bookings = get_filtered_bookings(request)
    
    total_pnrs = bookings.count()
    with_contacts = bookings.filter(Q(phone__isnull=False, phone__gt='') | Q(email__isnull=False, email__gt='')).count()
    
    quality_calc = bookings.aggregate(
        avg_score=Avg(
            Case(When(phone__gt='', then=20), default=0, output_field=IntegerField()) +
            Case(When(email__gt='', then=20), default=0, output_field=IntegerField()) +
            Case(When(ff_number__gt='', then=20), default=0, output_field=IntegerField()) +
            Case(When(meal_selection__gt='', then=20), default=0, output_field=IntegerField()) +
            Case(When(seat__gt='', then=20), default=0, output_field=IntegerField())
        )
    )
    avg_quality = quality_calc['avg_score'] or 0
    
    # Get filter options
    channel_types = [choice[0] for choice in Booking.CHANNEL_TYPE_CHOICES]
    direct_offices = [choice[0] for choice in Booking.DIRECT_OFFICE_CHOICES]
    indirect_offices = [choice[0] for choice in Booking.INDIRECT_OFFICE_CHOICES]
    offices = list(KQOffice.objects.all())
    agencies = list(TravelAgency.objects.all())
    
    # Contact failure analysis
    contact_failures = bookings.filter(phone='', email='').values('channel_type', 'office_type').annotate(
        failure_count=Count('id')
    ).order_by('-failure_count')
    
    office_contact_failures = bookings.filter(
        phone='', email='', kq_office__isnull=False
    ).values('kq_office__name', 'kq_office__office_id').annotate(
        failure_count=Count('id')
    ).order_by('-failure_count')[:10]
    
    # Dashboard data
    quality_score_calc = (
        Case(When(phone__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(email__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(ff_number__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(meal_selection__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(seat__gt='', then=20), default=0, output_field=IntegerField())
    )
    
    channel_stats = bookings.values('channel_type', 'office_type').annotate(
        total=Count('id'),
        avg_quality=Avg(quality_score_calc)
    ).order_by('-total')
    
    office_stats = bookings.filter(kq_office__isnull=False).values(
        'kq_office__name', 'kq_office__office_id'
    ).annotate(
        total=Count('id'),
        avg_quality=Avg(quality_score_calc)
    ).order_by('-total')[:10]
    
    print(f"Debug - Channels: {channels}")
    print(f"Debug - Offices: {[o.name for o in offices]}")
    print(f"Debug - Channel Stats: {list(channel_stats)}")
    print(f"Debug - Office Stats: {list(office_stats)}")
    
    # Contact analysis
    without_contacts = total_pnrs - with_contacts
    pnrs_no_contacts = bookings.filter(phone='', email='')
    
    # Quality trends (last 7 days)
    trends = []
    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        day_bookings = bookings.filter(created_at__date=date)
        day_quality = day_bookings.aggregate(
            avg_score=Avg(quality_score_calc)
        )['avg_score'] or 0
        trends.append({
            'date': date.strftime('%m/%d'),
            'quality': round(day_quality, 1)
        })
    
    context = {
        'total_pnrs': total_pnrs,
        'with_contacts': with_contacts,
        'without_contacts': without_contacts,
        'avg_quality': round(avg_quality, 1),
        'channel_types': channel_types,
        'direct_offices': direct_offices,
        'indirect_offices': indirect_offices,
        'offices': offices,
        'agencies': agencies,
        'channel_stats': channel_stats,
        'office_stats': office_stats,
        'contact_failures': contact_failures,
        'office_contact_failures': office_contact_failures,
        'pnrs_no_contacts': pnrs_no_contacts,
        'trends': json.dumps(trends[::-1]),
    }
    return render(request, "home.html", context)

def upload_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            df = pd.read_excel(request.FILES['excel_file'])
            for _, row in df.iterrows():
                Booking.objects.update_or_create(
                    pnr=row.get('pnr', ''),
                    defaults={
                        'phone': row.get('phone', ''),
                        'email': row.get('email', ''),
                        'ff_number': row.get('ff_number', ''),
                        'meal_selection': row.get('meal_selection', ''),
                        'seat': row.get('seat', ''),
                        'booking_channel': row.get('booking_channel', 'web'),
                        # Note: office_id, agency_iata, staff_id should be handled via ForeignKey relationships
                    }
                )
            messages.success(request, f'Successfully imported {len(df)} records')
        except Exception as e:
            messages.error(request, f'Error importing file: {str(e)}')
        return redirect('home')
    return render(request, 'upload.html')

def dashboard(request):
    quality_score_calc = (
        Case(When(phone__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(email__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(ff_number__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(meal_selection__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(seat__gt='', then=20), default=0, output_field=IntegerField())
    )
    
    channel_stats = Booking.objects.values('channel_type', 'office_type').annotate(
        total=Count('id'),
        avg_quality=Avg(quality_score_calc)
    ).order_by('-total')
    
    office_stats = Booking.objects.filter(kq_office__isnull=False).values(
        'kq_office__name', 'kq_office__office_id'
    ).annotate(
        total=Count('id'),
        avg_quality=Avg(quality_score_calc)
    ).order_by('-total')[:10]
    
    context = {
        'channel_stats': channel_stats,
        'office_stats': office_stats,
    }
    return render(request, 'dashboard.html', context)

def contacts_pie_chart(request):
    total_pnrs = Booking.objects.count()
    with_contacts = Booking.objects.filter(Q(phone__isnull=False, phone__gt='') | Q(email__isnull=False, email__gt='')).count()
    without_contacts = total_pnrs - with_contacts
    context = {
        'with_contacts': with_contacts,
        'without_contacts': without_contacts,
        'total_pnrs': total_pnrs,
    }
    return render(request, 'contacts_pie_chart.html', context)

def pnrs_without_contacts(request):
    pnrs = Booking.objects.filter(phone='', email='')
    return render(request, 'pnrs_without_contacts.html', {'pnrs': pnrs})

def export_pnrs_to_excel(request):
    try:
        bookings = get_filtered_bookings(request)
        export_type = request.GET.get('type', 'all')
        
        if export_type == 'no_contacts':
            bookings = bookings.filter(phone='', email='')
        elif export_type == 'low_quality':
            low_quality_ids = []
            for booking in bookings:
                if booking.quality_score < 60:
                    low_quality_ids.append(booking.id)
            bookings = bookings.filter(id__in=low_quality_ids)
        elif export_type == 'high_quality':
            high_quality_ids = []
            for booking in bookings:
                if booking.quality_score >= 80:
                    high_quality_ids.append(booking.id)
            bookings = bookings.filter(id__in=high_quality_ids)
        
        qs = bookings.values(
            'pnr', 'phone', 'email', 'ff_number', 'meal_selection', 'seat',
            'booking_channel', 'kq_office__office_id', 'travel_agency__iata_code', 
            'kq_staff__staff_id', 'created_at'
        )
        df = pd.DataFrame(list(qs))
        
        if not df.empty:
            df['quality_score'] = (
                (df['phone'].fillna('') != '').astype(int) * 20 +
                (df['email'].fillna('') != '').astype(int) * 20 +
                (df['ff_number'].fillna('') != '').astype(int) * 20 +
                (df['meal_selection'].fillna('') != '').astype(int) * 20 +
                (df['seat'].fillna('') != '').astype(int) * 20
            )
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        filename = f'kq_bookings_{export_type}_{timezone.now().strftime("%Y%m%d")}.xlsx'
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        df.to_excel(response, index=False)
        return response
    except Exception as e:
        return HttpResponse(f'Error generating report: {str(e)}', status=500)

def api_quality_trends(request):
    bookings = get_filtered_bookings(request)
    days = int(request.GET.get('days', 30))
    
    quality_calc = (
        Case(When(phone__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(email__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(ff_number__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(meal_selection__gt='', then=20), default=0, output_field=IntegerField()) +
        Case(When(seat__gt='', then=20), default=0, output_field=IntegerField())
    )
    
    trends = []
    for i in range(days):
        date = timezone.now().date() - timedelta(days=i)
        day_bookings = bookings.filter(created_at__date=date)
        day_quality = day_bookings.aggregate(avg_score=Avg(quality_calc))['avg_score'] or 0
        day_count = day_bookings.count()
        trends.append({
            'date': date.strftime('%Y-%m-%d'),
            'quality': round(day_quality, 1),
            'count': day_count
        })
    
    return JsonResponse({'trends': trends[::-1]})