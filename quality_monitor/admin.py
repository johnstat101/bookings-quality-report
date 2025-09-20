from django.contrib import admin
from .models import PNR, Passenger, Contact

class ContactInline(admin.TabularInline):
    model = Contact
    extra = 1

class PassengerInline(admin.TabularInline):
    model = Passenger
    extra = 1

@admin.register(PNR)
class PNRAdmin(admin.ModelAdmin):
    list_display = ['control_number', 'office_id', 'agent', 'has_valid_contacts', 'quality_score', 'created_at']
    list_filter = ['office_id', 'delivery_system_company', 'created_at']
    search_fields = ['control_number', 'office_id', 'agent']
    readonly_fields = ['has_valid_contacts', 'quality_score']
    inlines = [ContactInline, PassengerInline]

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['pnr', 'contact_type', 'contact_detail', 'is_valid_email', 'is_valid_phone', 'is_wrongly_placed']
    list_filter = ['contact_type']
    search_fields = ['contact_detail', 'pnr__control_number']
    readonly_fields = ['is_email', 'is_phone', 'is_valid_email', 'is_valid_phone', 'is_wrongly_placed']
    
    def get_readonly_fields(self, request, obj=None):
        # Only show readonly fields that are actually displayed
        return ['is_valid_email', 'is_valid_phone', 'is_wrongly_placed']