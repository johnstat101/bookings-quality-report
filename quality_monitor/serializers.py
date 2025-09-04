from rest_framework import serializers
from .models import Booking

class BookingSerializer(serializers.ModelSerializer):
    quality_score = serializers.ReadOnlyField()
    has_contacts = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'pnr', 'phone', 'email', 'ff_number', 'meal_selection', 'seat',
            'booking_channel', 'office_id', 'agency_iata', 'agency_name',
            'staff_id', 'staff_name', 'created_at', 'updated_at',
            'quality_score', 'has_contacts'
        ]
        read_only_fields = ['created_at', 'updated_at']

class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'pnr', 'phone', 'email', 'ff_number', 'meal_selection', 'seat',
            'booking_channel', 'office_id', 'agency_iata', 'agency_name',
            'staff_id', 'staff_name'
        ]

class QualityStatsSerializer(serializers.Serializer):
    total_pnrs = serializers.IntegerField()
    with_contacts = serializers.IntegerField()
    without_contacts = serializers.IntegerField()
    avg_quality = serializers.FloatField()
    contact_percentage = serializers.FloatField()

class ChannelStatsSerializer(serializers.Serializer):
    booking_channel = serializers.CharField()
    total = serializers.IntegerField()
    avg_quality = serializers.FloatField()
    percentage = serializers.FloatField()

class OfficeStatsSerializer(serializers.Serializer):
    office_id = serializers.CharField()
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