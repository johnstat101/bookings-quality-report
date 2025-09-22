from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Q, Case, When, IntegerField, Avg
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date as django_parse_date
from datetime import datetime, timedelta
from .models import PNR, Passenger, Contact
from .utils import get_quality_score_annotation
import pandas as pd
import json
import re
import logging

logger = logging.getLogger('quality_monitor')

def parse_date(date_str):
    """Parse a date string in ddmmyy or dmmyy format with validation."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        # Sanitize input - only allow digits
        clean_date = re.sub(r'\D', '', str(date_str))
        if len(clean_date) == 5:
            clean_date = '0' + clean_date
        elif len(clean_date) != 6:
            return None
        return datetime.strptime(clean_date, '%d%m%y').date()
    except (ValueError, TypeError):
        return None

def get_filtered_pnrs(request):
    """Get filtered PNRs with proper validation and optimization."""
    pnrs = PNR.objects.prefetch_related('contacts', 'passengers').all()
    
    # Date filters with validation
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Validate and parse dates
    if start_date and start_date.strip():
        parsed_start = django_parse_date(start_date.strip())
        if parsed_start:
            pnrs = pnrs.filter(creation_date__gte=parsed_start)
    
    if end_date and end_date.strip():
        parsed_end = django_parse_date(end_date.strip())
        if parsed_end:
            pnrs = pnrs.filter(creation_date__lte=parsed_end)
    
    # Office filters with validation
    offices = request.GET.getlist('offices')
    if offices:
        # Sanitize office IDs
        clean_offices = [office.strip() for office in offices if office.strip()]
        if clean_offices:
            pnrs = pnrs.filter(office_id__in=clean_offices)
    
    # Delivery system filters with validation
    delivery_systems = request.GET.getlist('delivery_systems')
    if delivery_systems:
        clean_systems = [ds.strip() for ds in delivery_systems if ds.strip()]
        if clean_systems:
            pnrs = pnrs.filter(delivery_system_company__in=clean_systems)
    
    return pnrs

def calculate_pnr_statistics(pnrs_with_score):
    """
    Calculate comprehensive PNR statistics for dashboard display.
    
    Args:
        pnrs_with_score: QuerySet of PNRs annotated with quality scores
        
    Returns:
        Dict containing aggregated statistics including counts, percentages,
        and quality metrics for contacts, passengers, and overall quality.
    """
    return pnrs_with_score.aggregate(
        total_pnrs=Count('id', distinct=True),
        overall_quality=Avg('calculated_quality_score'),
        reachable_pnrs=Count('pk', filter=Q(
            contacts__contact_type__in=Contact.EMAIL_VALID_TYPES, 
            contacts__contact_detail__regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        ) | Q(
            contacts__contact_type__in=Contact.PHONE_VALID_TYPES, 
            contacts__contact_detail__regex=r'^\+?[0-9\s-]{7,20}$'
        ), distinct=True),
        missing_contacts=Count('pk', filter=Q(contacts__isnull=True), distinct=True),
        wrong_format_contacts=Count('pk', filter=Q(contacts__contact_detail__isnull=False) & 
            ~Q(contacts__contact_type__in=Contact.EMAIL_VALID_TYPES, contacts__contact_detail__regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') & 
            ~Q(contacts__contact_type__in=Contact.PHONE_VALID_TYPES, contacts__contact_detail__regex=r'^\+?[0-9\s-]{7,20}$')
        , distinct=True),
        wrongly_placed_contacts=Count('pk', filter=
            (Q(contacts__contact_detail__contains='@') & ~Q(contacts__contact_type__in=Contact.EMAIL_VALID_TYPES)) |
            (Q(contacts__contact_detail__regex=r'\d{7,}') & ~Q(contacts__contact_type__in=Contact.PHONE_VALID_TYPES))
        , distinct=True),
        ff_count=Count('passengers', filter=Q(passengers__ff_number__isnull=False) & ~Q(passengers__ff_number='')),
        meal_count=Count('passengers', filter=Q(passengers__meal__isnull=False) & ~Q(passengers__meal='')),
        seat_count=Count('passengers', filter=Q(passengers__seat_row_number__isnull=False) & ~Q(passengers__seat_row_number='') & Q(passengers__seat_column__isnull=False) & ~Q(passengers__seat_column='')),
        email_total=Count('contacts', filter=Q(contacts__contact_detail__contains='@') | Q(contacts__contact_detail__contains='//')),
        phone_total=Count('contacts', filter=Q(contacts__contact_detail__regex=r'\d{7,}')),
        email_wrong_format_count=Count('contacts', filter=(Q(contacts__contact_detail__contains='@') | Q(contacts__contact_detail__contains='//')) & ~Q(contacts__contact_type__in=Contact.EMAIL_VALID_TYPES, contacts__contact_detail__regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')),
        phone_wrong_format_count=Count('contacts', filter=Q(contacts__contact_detail__regex=r'\d{7,}') & ~Q(contacts__contact_type__in=Contact.PHONE_VALID_TYPES, contacts__contact_detail__regex=r'^\+?[0-9\s-]{7,20}$')),
        valid_phone_count=Count('contacts', filter=Q(contacts__contact_type__in=Contact.PHONE_VALID_TYPES, contacts__contact_detail__regex=r'^\+?[0-9\s-]{7,20}$')),
        valid_email_count=Count('contacts', filter=Q(contacts__contact_type__in=Contact.EMAIL_VALID_TYPES, contacts__contact_detail__regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')),
    )

def get_office_statistics(pnrs):
    """
    Calculate performance statistics grouped by office.
    
    Args:
        pnrs: QuerySet of PNR objects
        
    Returns:
        QuerySet with office_id, pnr_count, and avg_quality for each office
    """
    quality_score_annotation = get_quality_score_annotation()
    return (
        pnrs.values('office_id')
        .annotate(pnr_count=Count('id'), avg_quality=Avg(quality_score_annotation))
        .order_by('-pnr_count')
    )

def get_delivery_system_statistics(pnrs):
    """
    Calculate performance statistics grouped by delivery system.
    
    Args:
        pnrs: QuerySet of PNR objects
        
    Returns:
        QuerySet with delivery_system_company, pnr_count, and avg_quality
    """
    quality_score_annotation = get_quality_score_annotation()
    return (
        pnrs.values('delivery_system_company')
        .annotate(pnr_count=Count('id'), avg_quality=Avg(quality_score_annotation))
        .order_by('-pnr_count')
    )

def home_view(request):
    pnrs = get_filtered_pnrs(request)
    quality_score_annotation = get_quality_score_annotation()
    pnrs_with_score = pnrs.annotate(calculated_quality_score=quality_score_annotation)
    
    # Calculate statistics using helper functions
    stats = calculate_pnr_statistics(pnrs_with_score)

    total_pnrs = stats.get('total_pnrs', 0)
    reachable_pnrs = stats.get('reachable_pnrs', 0)
    missing_contacts = stats.get('missing_contacts', 0)
    wrong_format_contacts = stats.get('wrong_format_contacts', 0)
    wrongly_placed_contacts = stats.get('wrongly_placed_contacts', 0)
    overall_quality = stats.get('overall_quality', 0) or 0

    ff_count = stats.get('ff_count', 0)
    meal_count = stats.get('meal_count', 0)
    seat_count = stats.get('seat_count', 0)
    phone_count = stats.get('valid_phone_count', 0)
    email_count = stats.get('valid_email_count', 0)

    # Calculate percentages safely
    email_total = stats.get('email_total', 0)
    phone_total = stats.get('phone_total', 0)
    email_wrong_format_percent = (stats.get('email_wrong_format_count', 0) / email_total * 100) if email_total > 0 else 0
    phone_wrong_format_percent = (stats.get('phone_wrong_format_count', 0) / phone_total * 100) if phone_total > 0 else 0
    
    # Office and delivery system statistics - cache quality annotation
    office_stats_raw = get_office_statistics(pnrs)
    delivery_system_stats_raw = get_delivery_system_statistics(pnrs)
    
    office_stats = []
    for stat in office_stats_raw:
        office_data = {
            'office_id': stat['office_id'],
            'office_name': stat['office_id'], # Use office_id as name since KQOffice is removed
            'total': stat['pnr_count'],
            'avg_quality': stat['avg_quality'] or 0
        }
        office_stats.append(office_data)
    


    delivery_system_stats = []
    for stat in delivery_system_stats_raw:
        delivery_system_stats.append({
            'delivery_system_company': stat['delivery_system_company'],
            'total': stat['pnr_count'],
            'avg_quality': stat['avg_quality'] or 0
        })

    # Quality score distribution
    quality_distribution = pnrs_with_score.aggregate(
        range1=Count('pk', filter=Q(calculated_quality_score__lte=20)),
        range2=Count('pk', filter=Q(calculated_quality_score__gt=20, calculated_quality_score__lte=40)),
        range3=Count('pk', filter=Q(calculated_quality_score__gt=40, calculated_quality_score__lte=60)),
        range4=Count('pk', filter=Q(calculated_quality_score__gt=60, calculated_quality_score__lte=80)),
        range5=Count('pk', filter=Q(calculated_quality_score__gt=80)),
    )
    quality_ranges = [quality_distribution[f'range{i}'] for i in range(1, 6)]
    
    # Get current filter values
    current_offices = request.GET.getlist('offices')
    current_delivery_systems = request.GET.getlist('delivery_systems')
    
    # Get distinct offices from PNR data
    offices_from_pnr = PNR.objects.values('office_id').distinct().order_by('office_id')
    offices = [{'office_id': o['office_id'], 'name': o['office_id']} for o in offices_from_pnr if o['office_id']]
    
    # Prepare data for JavaScript
    dashboard_data_json = json.dumps({
        'total_pnrs': total_pnrs,
        'valid_phone_count': phone_count,
        'valid_email_count': email_count,
        'ff_count': ff_count,
        'meal_count': meal_count,
        'seat_count': seat_count,
        'email_wrong_format_pct': round(email_wrong_format_percent, 1),
        'phone_wrong_format_pct': round(phone_wrong_format_percent, 1),
        'quality_ranges': quality_ranges,
        'current_delivery_systems': current_delivery_systems,
        'current_offices': current_offices,
        'offices': offices,
        'office_stats': office_stats,
        'delivery_system_stats': delivery_system_stats,
        'export_url': reverse('quality_monitor:export_pnrs_to_excel'), # This remains correct due to the app_name
    })


    context = {
        'total_pnrs': total_pnrs,
        'reachable_pnrs': reachable_pnrs,
        'missing_contacts': missing_contacts,
        'wrong_format_contacts': wrong_format_contacts,
        'wrongly_placed_contacts': wrongly_placed_contacts,
        'avg_quality': round(overall_quality, 1),
        'offices': offices,
        'office_stats': office_stats,
        'delivery_system_stats': delivery_system_stats,
        'current_delivery_systems': current_delivery_systems,
        'current_offices': current_offices,
        'valid_phone_count': phone_count,
        'valid_email_count': email_count,
        'ff_count': ff_count,
        'meal_count': meal_count,
        'seat_count': seat_count,
        'quality_ranges': quality_ranges,
        'critical_count': quality_distribution['range1'],
        'poor_count': quality_distribution['range2'],
        'fair_count': quality_distribution['range3'],
        'good_count': quality_distribution['range4'],
        'excellent_count': quality_distribution['range5'],
        'email_wrong_format_pct': round(email_wrong_format_percent, 1),
        'phone_wrong_format_pct': round(phone_wrong_format_percent, 1),
        'pnrs': pnrs,
        'dashboard_data_json': dashboard_data_json,
    }
    return render(request, "home.html", context)

def upload_excel(request):
    """
    Handle SBR file upload and processing.
    
    Supports CSV, XLS, and XLSX formats. Clears existing data before import
    and uses bulk operations for efficient database insertion.
    
    Args:
        request: HTTP request with uploaded file
        
    Returns:
        Redirect to home page with success/error messages
    """
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            logger.info("Starting file upload process")
            # Clear existing data
            Contact.objects.all().delete()
            Passenger.objects.all().delete()
            PNR.objects.all().delete()
            messages.info(request, "Cleared all existing PNR data before import.")
            
            # Read file
            file_extension = request.FILES['excel_file'].name.split('.')[-1].lower()
            if file_extension == 'csv':
                df = pd.read_csv(request.FILES['excel_file'], dtype=str).fillna('')
            else:
                df = pd.read_excel(request.FILES['excel_file'], dtype=str).fillna('')
            
            pnrs_to_create = []
            pnr_map = {}
            
            # First pass: collect unique PNRs
            unique_pnrs = df['ControlNumber'].str.strip().replace('', pd.NA).dropna().unique()
            logger.info(f"Processing {len(unique_pnrs)} unique PNRs")
            
            for control_number in unique_pnrs:
                # Get the first row for this PNR to extract PNR-level data
                pnr_rows = df[df['ControlNumber'].str.strip() == control_number]
                if not pnr_rows.empty:
                    pnr_data = pnr_rows.iloc[0]
                    pnrs_to_create.append(PNR(
                        control_number=control_number,
                        office_id=str(pnr_data.get('OfficeID', '')).strip(),
                        agent=str(pnr_data.get('Agent', '')).strip(),
                        creation_date=parse_date(str(pnr_data.get('creationDate', ''))),
                        delivery_system_company=str(pnr_data.get('DeliverySystemCompany', '')).strip(),
                        delivery_system_location=str(pnr_data.get('DeliverySystemLocation', '')).strip(),
                    ))
            
            # Bulk create PNRs
            PNR.objects.bulk_create(pnrs_to_create, batch_size=500, ignore_conflicts=True)
            
            # Retrieve all created PNRs to build a map for the next step
            created_pnrs = PNR.objects.in_bulk(field_name='control_number')
            
            # Create mapping for foreign key relationships
            pnr_map = created_pnrs
            
            # Second pass: Create related Passenger and Contact objects
            passengers_to_create = []
            contacts_to_create = []
            
            for _, row in df.iterrows():
                control_number = str(row.get('ControlNumber', '')).strip()
                if not control_number or control_number not in pnr_map: continue

                pnr = pnr_map[control_number]
                
                # Passenger data
                surname = str(row.get('Surname', '')).strip()
                first_name = str(row.get('FirstName', '')).strip()
                if surname or first_name:
                    passengers_to_create.append(Passenger(
                        pnr=pnr,
                        surname=surname,
                        first_name=first_name,
                        ff_number=str(row.get('FF_NUMBER', '')).strip(),
                        ff_tier=str(row.get('FF_TIER', '')).strip(),
                        board_point=str(row.get('boardPoint', '')).strip(),
                        off_point=str(row.get('offPoint', '')).strip(),
                        seat_row_number=str(row.get('seatRowNumber', '')).strip(),
                        seat_column=str(row.get('seatColumn', '')).strip(),
                        meal=str(row.get('MEAL', '')).strip(),
                    ))
                
                # Contact data
                contact_type = str(row.get('ContactType', '')).strip()
                contact_detail = str(row.get('ContactDetail', '')).strip()
                if contact_type and contact_detail:
                    contacts_to_create.append(Contact(pnr=pnr, contact_type=contact_type, contact_detail=contact_detail))
            
            # Bulk create passengers and contacts
            if passengers_to_create:
                Passenger.objects.bulk_create(passengers_to_create, ignore_conflicts=True)
            if contacts_to_create:
                Contact.objects.bulk_create(contacts_to_create, ignore_conflicts=True)
            
            logger.info(f"Successfully processed {len(unique_pnrs)} PNRs")
            messages.success(request, f'Successfully processed {len(unique_pnrs)} unique PNRs from the file.')
            
        except Exception as e:
            logger.error(f"Error importing file: {str(e)}")
            messages.error(request, f'Error importing file: {str(e)}')
        
        return redirect('quality_monitor:home')
    
    return render(request, 'upload.html')

def export_pnrs_to_excel(request):
    """
    Export filtered PNR data to an Excel file.
    This view now handles both dashboard-level filters and specific
    modal-based exports, including in-modal text filters.
    """
    try:
        # Get PNRs based on the detailed API logic to match the modal
        pnrs, _ = get_detailed_pnrs_qs(request)

        # Apply in-modal text filters if they are present
        office_filter = request.GET.get('modal_office_id', '').strip()
        delivery_system_filter = request.GET.get('modal_delivery_system', '').strip()

        if office_filter:
            pnrs = pnrs.filter(office_id__icontains=office_filter)
        if delivery_system_filter:
            pnrs = pnrs.filter(delivery_system_company__icontains=delivery_system_filter)

        # Build the export data
        pnrs = pnrs.prefetch_related('contacts', 'passengers').order_by('-creation_date')
        export_data = []
        for pnr in pnrs:
            contact = pnr.contacts.first()
            base_data = {
                'PNR': pnr.control_number,
                'Office_ID': pnr.office_id,
                'Delivery_System': pnr.delivery_system_company,
                'Agent': pnr.agent,
                'Creation_Date': pnr.creation_date,
                'Quality_Score': pnr.quality_score,
                'Contact_Type': contact.contact_type if contact else 'N/A',
                'Contact_Detail': contact.contact_detail if contact else 'N/A',
            }
            export_data.append(base_data)
        
        df = pd.DataFrame(export_data)

        export_type = request.GET.get('metric', 'data')
        filename = f'kq_quality_report_{export_type}_{timezone.now().strftime("%Y%m%d")}.xlsx'
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        df.to_excel(response, index=False)
        return response
    except Exception as e:
        return HttpResponse(f'Error generating report: {str(e)}', status=500)

def api_quality_trends(request):
    pnrs = get_filtered_pnrs(request)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    quality_score_annotation = get_quality_score_annotation()

    # Perform a single query to get stats for all days in the range
    daily_stats = (
        pnrs.filter(creation_date__range=[start_date, end_date])
        .values('creation_date')
        .annotate(
            avg_quality=Avg(quality_score_annotation),
            pnr_count=Count('id', distinct=True)
        )
    )

    trends = [{
        'date': stat['creation_date'].strftime('%Y-%m-%d'), 
        'quality': round(stat['avg_quality'] or 0, 1), 
        'count': stat['pnr_count']
    } for stat in daily_stats if stat['creation_date']]
    trends.sort(key=lambda x: x['date']) # Ensure the data is sorted by date
    
    return JsonResponse({'trends': trends})

def api_delivery_systems(request):
    """API endpoint for delivery systems"""
    # Get distinct delivery systems from PNRs with proper ordering
    delivery_systems = PNR.objects.values_list('delivery_system_company', flat=True).distinct().order_by('delivery_system_company')
    
    # Return a flat list of delivery systems
    delivery_system_list = [{'id': c, 'label': c} for c in delivery_systems if c]
    return JsonResponse({'delivery_systems': delivery_system_list, 'disabled': not delivery_system_list})

def api_offices_by_delivery_systems(request):
    """API endpoint to get offices, optionally filtered by delivery system."""
    delivery_systems = request.GET.getlist('delivery_systems')
    
    pnrs = PNR.objects.all()
    if delivery_systems:
        # Sanitize delivery system inputs
        clean_systems = [ds.strip() for ds in delivery_systems if ds.strip()]
        if clean_systems:
            pnrs = pnrs.filter(delivery_system_company__in=clean_systems)
        
    offices_from_pnr = pnrs.values('office_id').distinct().order_by('office_id')
    offices = [{'office_id': o['office_id'], 'name': o['office_id']} for o in offices_from_pnr if o['office_id']]
    return JsonResponse({'offices': offices})

def get_detailed_pnrs_qs(request):
    """Helper function to get the base QuerySet for detailed PNR views."""
    metric = request.GET.get('metric')

    pnrs = get_filtered_pnrs(request)

    # Apply metric-specific filtering
    if metric == 'total_pnrs':
        # No additional filtering needed, but we might want to limit the initial list
        pass
    elif metric == 'reachable_pnrs':
        pnrs = pnrs.filter(
            Q(contacts__contact_type__in=Contact.EMAIL_VALID_TYPES, contacts__contact_detail__regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') |
            Q(contacts__contact_type__in=Contact.PHONE_VALID_TYPES, contacts__contact_detail__regex=r'^\+?[0-9\s-]{7,20}$')
        ).distinct()
    elif metric == 'missing_contacts':
        pnrs = pnrs.annotate(contact_count=Count('contacts')).filter(contact_count=0)
    elif metric == 'wrong_format_contacts':
        pnrs = pnrs.filter(
            Q(contacts__contact_detail__isnull=False) & 
            ~Q(contacts__contact_type__in=Contact.EMAIL_VALID_TYPES, contacts__contact_detail__regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$') & 
            ~Q(contacts__contact_type__in=Contact.PHONE_VALID_TYPES, contacts__contact_detail__regex=r'^\+?[0-9\s-]{7,20}$')
        ).distinct()
    elif metric == 'wrongly_placed_contacts':
        pnrs = pnrs.filter(
            (Q(contacts__contact_detail__contains='@') & ~Q(contacts__contact_type__in=Contact.EMAIL_VALID_TYPES)) |
            (Q(contacts__contact_detail__regex=r'\d{7,}') & ~Q(contacts__contact_type__in=Contact.PHONE_VALID_TYPES))
        ).distinct()
    elif metric.startswith('delivery_system_'):
        system_name = metric.replace('delivery_system_', '')
        pnrs = pnrs.filter(delivery_system_company=system_name)
    elif metric == 'all_delivery_systems':
        pass # No additional filtering needed for all systems
    else:
        # This case handles if no valid metric is passed, returning the base filtered set.
        # Or, it could return an empty set if that's preferred.
        pass

    return pnrs, metric

def api_detailed_pnrs(request):
    """
    API endpoint to fetch detailed PNR lists for modal views.
    """
    pnrs, metric = get_detailed_pnrs_qs(request)
    if not metric:
        return JsonResponse({'error': 'Metric not specified'}, status=400)

    # Limit results for performance and select related data
    detailed_pnrs = pnrs.order_by('-creation_date').prefetch_related('contacts')[:200]

    pnr_list = []
    for pnr in detailed_pnrs:
        contact = pnr.contacts.first()
        pnr_list.append({
            'control_number': pnr.control_number,
            'office_id': pnr.office_id,
            'delivery_system': pnr.delivery_system_company,
            'agent': pnr.agent,
            'creation_date': pnr.creation_date.strftime('%Y-%m-%d') if pnr.creation_date else 'N/A',
            'contact_type': contact.contact_type if contact else 'N/A',
            'contact_detail': contact.contact_detail if contact else 'N/A',
        })

    return JsonResponse({'pnrs': pnr_list})