from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("pnr", "phone", "email", "ff_number", "meal_selection", "seat", "created_at")
    search_fields = ("pnr", "email", "ff_number")
    list_filter = ("meal_selection", "seat")
