from django.contrib import admin
from .models import Booking, TravelAgency, KQOffice, KQStaff

@admin.register(TravelAgency)
class TravelAgencyAdmin(admin.ModelAdmin):
    list_display = ['iata_code', 'name', 'contact_email', 'contact_phone']
    search_fields = ['iata_code', 'name']
    list_filter = ['created_at']

@admin.register(KQOffice)
class KQOfficeAdmin(admin.ModelAdmin):
    list_display = ['office_id', 'name', 'location', 'manager']
    search_fields = ['office_id', 'name', 'location']
    list_filter = ['location', 'created_at']

@admin.register(KQStaff)
class KQStaffAdmin(admin.ModelAdmin):
    list_display = ['staff_id', 'name', 'office', 'email']
    search_fields = ['staff_id', 'name', 'email']
    list_filter = ['office', 'created_at']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['pnr', 'channel', 'channel_type', 'departure_date', 'quality_score', 'has_contacts', 'created_at']
    list_filter = ['channel', 'departure_date', 'created_at', 'kq_office', 'travel_agency']
    search_fields = ['pnr', 'phone', 'email', 'ff_number']
    readonly_fields = ['quality_score', 'has_contacts']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('pnr', 'departure_date', 'channel')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'ff_number')
        }),
        ('Service Preferences', {
            'fields': ('meal_selection', 'seat')
        }),
        ('Booking Agent', {
            'fields': ('kq_office', 'kq_staff', 'travel_agency'),
            'description': 'Select appropriate agent based on booking channel'
        }),
        ('Quality Metrics', {
            'fields': ('quality_score', 'has_contacts'),
            'classes': ('collapse',)
        })
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Add JavaScript for dynamic field showing/hiding based on channel
        form.Media.js = ('admin/js/booking_admin.js',)
        return form