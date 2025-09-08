from rest_framework import serializers
from .models import Booking, KQOffice, KQStaff, TravelAgency

class KQOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = KQOffice
        fields = '__all__'

class KQStaffSerializer(serializers.ModelSerializer):
    office_name = serializers.CharField(source='office.name', read_only=True)
    
    class Meta:
        model = KQStaff
        fields = '__all__'

class TravelAgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelAgency
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    quality_score = serializers.ReadOnlyField()
    has_contacts = serializers.ReadOnlyField()
    booking_agent = serializers.ReadOnlyField()
    kq_office_name = serializers.CharField(source='kq_office.name', read_only=True)
    kq_staff_name = serializers.CharField(source='kq_staff.name', read_only=True)
    travel_agency_name = serializers.CharField(source='travel_agency.name', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'pnr', 'phone', 'email', 'ff_number', 'meal_selection', 'seat',
            'channel_type', 'office_type', 'departure_date', 'created_at', 'updated_at',
            'kq_office', 'kq_staff', 'travel_agency',
            'kq_office_name', 'kq_staff_name', 'travel_agency_name',
            'quality_score', 'has_contacts', 'booking_agent'
        ]
        read_only_fields = ['created_at', 'updated_at']

class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'pnr', 'phone', 'email', 'ff_number', 'meal_selection', 'seat',
            'channel_type', 'office_type', 'departure_date', 'kq_office', 'kq_staff', 'travel_agency'
        ]

class QualityStatsSerializer(serializers.Serializer):
    total_pnrs = serializers.IntegerField()
    with_contacts = serializers.IntegerField()
    without_contacts = serializers.IntegerField()
    avg_quality = serializers.FloatField()
    contact_percentage = serializers.FloatField()

class ChannelStatsSerializer(serializers.Serializer):
    channel_type = serializers.CharField()
    office_type = serializers.CharField()
    total = serializers.IntegerField()
    avg_quality = serializers.FloatField()
    percentage = serializers.FloatField()

class OfficeStatsSerializer(serializers.Serializer):
    kq_office__office_id = serializers.CharField()
    kq_office__name = serializers.CharField()
    total = serializers.IntegerField()
    avg_quality = serializers.FloatField()

class QualityTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    quality = serializers.FloatField()
    count = serializers.IntegerField()

class BulkUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    
    def validate_file(self, value):
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError("File must be Excel format (.xlsx or .xls)")
        return value