from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Q, Avg
from .models import Booking
import pandas as pd
from django.http import HttpResponse

def home_view(request):
    total_pnrs = Booking.objects.count()
    with_contacts = Booking.objects.filter(Q(phone__isnull=False, phone__gt='') | Q(email__isnull=False, email__gt='')).count()
    avg_quality = Booking.objects.aggregate(avg_score=Avg('quality_score'))['avg_score'] or 0
    
    context = {
        'total_pnrs': total_pnrs,
        'with_contacts': with_contacts,
        'avg_quality': round(avg_quality, 1),
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
                        'office_id': row.get('office_id', ''),
                        'agency_iata': row.get('agency_iata', ''),
                        'agency_name': row.get('agency_name', ''),
                        'staff_id': row.get('staff_id', ''),
                        'staff_name': row.get('staff_name', ''),
                    }
                )
            messages.success(request, f'Successfully imported {len(df)} records')
        except Exception as e:
            messages.error(request, f'Error importing file: {str(e)}')
        return redirect('home')
    return render(request, 'upload.html')

def dashboard(request):
    channel_stats = Booking.objects.values('booking_channel').annotate(
        total=Count('id'),
        avg_quality=Avg('quality_score')
    ).order_by('-total')
    
    office_stats = Booking.objects.exclude(office_id='').values('office_id').annotate(
        total=Count('id'),
        avg_quality=Avg('quality_score')
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
        qs = Booking.objects.all().values(
            'pnr', 'phone', 'email', 'ff_number', 'meal_selection', 'seat',
            'booking_channel', 'office_id', 'agency_iata', 'staff_id', 'quality_score'
        )
        df = pd.DataFrame(list(qs))
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=pnrs_quality_report.xlsx'
        df.to_excel(response, index=False)
        return response
    except Exception:
        return HttpResponse('Error generating report', status=500)