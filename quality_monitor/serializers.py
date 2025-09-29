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
    
    def validate_control_number(self, value):
        """Validate control number format and uniqueness"""
        if not value or not value.strip():
            raise serializers.ValidationError("Control number cannot be empty")
        
        value = value.strip()
        
        # Check for uniqueness during updates
        if self.instance and self.instance.control_number != value:
            if PNR.objects.filter(control_number=value).exists():
                raise serializers.ValidationError("PNR with this control number already exists")
        
        return value

class QualityStatsSerializer(serializers.Serializer):
    total_pnrs = serializers.IntegerField(min_value=0)
    with_contacts = serializers.IntegerField(min_value=0)
    without_contacts = serializers.IntegerField(min_value=0)
    avg_quality = serializers.FloatField(min_value=0, max_value=100)
    contact_percentage = serializers.FloatField(min_value=0, max_value=100)
    
    def validate(self, data):
        """Validate that statistics are consistent"""
        total = data.get('total_pnrs', 0)
        with_contacts = data.get('with_contacts', 0)
        without_contacts = data.get('without_contacts', 0)
        
        if with_contacts + without_contacts > total:
            raise serializers.ValidationError(
                "Sum of with_contacts and without_contacts cannot exceed total_pnrs"
            )
        
        return data

class ChannelStatsSerializer(serializers.Serializer):
    channel_type = serializers.CharField()
    office_type = serializers.CharField()
    total = serializers.IntegerField(min_value=0)
    avg_quality = serializers.FloatField(min_value=0, max_value=100)
    percentage = serializers.FloatField(min_value=0, max_value=100)

class OfficeStatsSerializer(serializers.Serializer):
    office_id = serializers.CharField()
    office_name = serializers.CharField()
    total = serializers.IntegerField(min_value=0)
    avg_quality = serializers.FloatField(min_value=0, max_value=100)

class QualityTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    quality = serializers.FloatField(min_value=0, max_value=100)
    count = serializers.IntegerField(min_value=0)

class BulkUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    
    def validate_file(self, value):
        if not value.name.endswith(('.xlsx', '.xls', '.csv')):
            raise serializers.ValidationError("File must be Excel or CSV format (.xlsx, .xls, or .csv)")
        return value