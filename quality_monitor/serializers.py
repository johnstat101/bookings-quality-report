from rest_framework import serializers
from .models import PNR, Contact, Passenger

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

class PassengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passenger
        fields = '__all__'

class PNRSerializer(serializers.ModelSerializer):
    quality_score = serializers.ReadOnlyField()
    has_valid_contacts = serializers.ReadOnlyField()
    contacts = ContactSerializer(many=True, read_only=True)
    passengers = PassengerSerializer(many=True, read_only=True)
    
    class Meta:
        model = PNR
        fields = [
            'id', 'control_number', 'office_id', 'agent', 'creation_date',
            'delivery_system_company', 'delivery_system_location', 'created_at',
            'quality_score', 'has_valid_contacts', 'contacts', 'passengers'
        ]
        read_only_fields = ['created_at']

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
    office_id = serializers.CharField()
    office_name = serializers.CharField()
    total = serializers.IntegerField()
    avg_quality = serializers.FloatField()

class QualityTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    quality = serializers.FloatField()
    count = serializers.IntegerField()

class BulkUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    
    def validate_file(self, value):
        if not value.name.endswith(('.xlsx', '.xls', '.csv')):
            raise serializers.ValidationError("File must be Excel or CSV format (.xlsx, .xls, or .csv)")
        return value