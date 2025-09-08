from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Case, When, IntegerField, Avg
from django.utils import timezone
from datetime import timedelta
import pandas as pd

from .models import Booking, KQOffice, KQStaff, TravelAgency
from .serializers import (
    BookingSerializer, BookingCreateSerializer, QualityStatsSerializer,
    ChannelStatsSerializer, OfficeStatsSerializer, QualityTrendSerializer,
    BulkUploadSerializer, KQOfficeSerializer, KQStaffSerializer, TravelAgencySerializer
)

class KQOfficeViewSet(viewsets.ModelViewSet):
    queryset = KQOffice.objects.all()
    serializer_class = KQOfficeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['office_id']
    search_fields = ['name', 'office_id']

class KQStaffViewSet(viewsets.ModelViewSet):
    queryset = KQStaff.objects.select_related('office').all()
    serializer_class = KQStaffSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['staff_id', 'office']
    search_fields = ['name', 'staff_id']

class TravelAgencyViewSet(viewsets.ModelViewSet):
    queryset = TravelAgency.objects.all()
    serializer_class = TravelAgencySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['iata_code']
    search_fields = ['name', 'iata_code']

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['channel_type', 'office_type', 'kq_office__office_id', 'travel_agency__iata_code', 'kq_staff__staff_id']
    search_fields = ['pnr', 'phone', 'email', 'ff_number']
    ordering_fields = ['created_at', 'pnr', 'quality_score']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer
    
    def get_queryset(self):
        queryset = Booking.objects.all()
        
        # Date filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def quality_stats(self, request):
        """Get overall quality statistics"""
        bookings = self.get_queryset()
        
        total_pnrs = bookings.count()
        with_contacts = bookings.filter(
            Q(phone__isnull=False, phone__gt='') | 
            Q(email__isnull=False, email__gt='')
        ).count()
        without_contacts = total_pnrs - with_contacts
        
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
        contact_percentage = (with_contacts / total_pnrs * 100) if total_pnrs > 0 else 0
        
        data = {
            'total_pnrs': total_pnrs,
            'with_contacts': with_contacts,
            'without_contacts': without_contacts,
            'avg_quality': round(avg_quality, 2),
            'contact_percentage': round(contact_percentage, 2)
        }
        
        serializer = QualityStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def channel_stats(self, request):
        """Get performance statistics by channel"""
        bookings = self.get_queryset()
        total_bookings = bookings.count()
        
        quality_calc = (
            Case(When(phone__gt='', then=20), default=0, output_field=IntegerField()) +
            Case(When(email__gt='', then=20), default=0, output_field=IntegerField()) +
            Case(When(ff_number__gt='', then=20), default=0, output_field=IntegerField()) +
            Case(When(meal_selection__gt='', then=20), default=0, output_field=IntegerField()) +
            Case(When(seat__gt='', then=20), default=0, output_field=IntegerField())
        )
        
        stats = bookings.values('channel_type', 'office_type').annotate(
            total=Count('id'),
            avg_quality=Avg(quality_calc)
        ).order_by('-total')
        
        # Add percentage
        for stat in stats:
            stat['percentage'] = round((stat['total'] / total_bookings * 100), 2) if total_bookings > 0 else 0
            stat['avg_quality'] = round(stat['avg_quality'] or 0, 2)
        
        serializer = ChannelStatsSerializer(stats, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def office_stats(self, request):
        """Get performance statistics by office"""
        bookings = self.get_queryset().filter(kq_office__isnull=False)
        
        quality_calc = (
            Case(When(phone__gt='', then=20), default=0, output_field=IntegerField()) +
            Case(When(email__gt='', then=20), default=0, output_field=IntegerField()) +
            Case(When(ff_number__gt='', then=20), default=0, output_field=IntegerField()) +
            Case(When(meal_selection__gt='', then=20), default=0, output_field=IntegerField()) +
            Case(When(seat__gt='', then=20), default=0, output_field=IntegerField())
        )
        
        stats = bookings.values('kq_office__office_id', 'kq_office__name').annotate(
            total=Count('id'),
            avg_quality=Avg(quality_calc)
        ).order_by('-total')[:20]
        
        for stat in stats:
            stat['avg_quality'] = round(stat['avg_quality'] or 0, 2)
        
        serializer = OfficeStatsSerializer(stats, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def quality_trends(self, request):
        """Get quality trends over time"""
        bookings = self.get_queryset()
        days = int(request.query_params.get('days', 30))
        
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
                'date': date,
                'quality': round(day_quality, 2),
                'count': day_count
            })
        
        serializer = QualityTrendSerializer(trends[::-1], many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def no_contacts(self, request):
        """Get bookings without contact information"""
        bookings = self.get_queryset().filter(phone='', email='')
        
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def low_quality(self, request):
        """Get bookings with quality score < 60%"""
        bookings = self.get_queryset()
        low_quality_bookings = [b for b in bookings if b.quality_score < 60]
        
        serializer = self.get_serializer(low_quality_bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def high_quality(self, request):
        """Get bookings with quality score >= 80%"""
        bookings = self.get_queryset()
        high_quality_bookings = [b for b in bookings if b.quality_score >= 80]
        
        serializer = self.get_serializer(high_quality_bookings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """Bulk upload bookings from Excel file"""
        serializer = BulkUploadSerializer(data=request.data)
        if serializer.is_valid():
            try:
                df = pd.read_excel(serializer.validated_data['file'])
                created_count = 0
                updated_count = 0
                
                for _, row in df.iterrows():
                    # Handle ForeignKey relationships
                    kq_office = None
                    if row.get('office_id'):
                        kq_office, _ = KQOffice.objects.get_or_create(
                            office_id=row.get('office_id'),
                            defaults={'name': row.get('office_name', row.get('office_id'))}
                        )
                    
                    travel_agency = None
                    if row.get('agency_iata'):
                        travel_agency, _ = TravelAgency.objects.get_or_create(
                            iata_code=row.get('agency_iata'),
                            defaults={'name': row.get('agency_name', row.get('agency_iata'))}
                        )
                    
                    kq_staff = None
                    if row.get('staff_id') and kq_office:
                        kq_staff, _ = KQStaff.objects.get_or_create(
                            staff_id=row.get('staff_id'),
                            defaults={'name': row.get('staff_name', row.get('staff_id')), 'office': kq_office}
                        )
                    
                    booking, created = Booking.objects.update_or_create(
                        pnr=row.get('pnr', ''),
                        defaults={
                            'phone': row.get('phone', ''),
                            'email': row.get('email', ''),
                            'ff_number': row.get('ff_number', ''),
                            'meal_selection': row.get('meal_selection', ''),
                            'seat': row.get('seat', ''),
                            'booking_channel': row.get('booking_channel', 'web'),
                            'departure_date': row.get('departure_date'),
                            'kq_office': kq_office,
                            'kq_staff': kq_staff,
                            'travel_agency': travel_agency,
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                
                return Response({
                    'message': 'Upload successful',
                    'created': created_count,
                    'updated': updated_count,
                    'total': len(df)
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'error': f'Upload failed: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)