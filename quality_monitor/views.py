from django.shortcuts import render
from .models import Booking
import pandas as pd
from django.http import HttpResponse

# home page view
def home_view(request):
    return render(request, "home.html")

def contacts_pie_chart(request):
    total_pnrs = Booking.objects.count()
    with_contacts = Booking.objects.exclude(phone='').exclude(email='').count()
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
    qs = Booking.objects.all().values('pnr', 'phone', 'email', 'ff_number', 'meal_selection', 'seat')
    df = pd.DataFrame(list(qs))
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=pnrs.xlsx'
    df.to_excel(response, index=False)
    return response