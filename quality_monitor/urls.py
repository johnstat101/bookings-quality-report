from django.urls import path
from .views import home_view, contacts_pie_chart, pnrs_without_contacts, export_pnrs_to_excel, upload_excel, dashboard

urlpatterns = [
    path('', home_view, name='home'),
    path('upload/', upload_excel, name='upload_excel'),
    path('dashboard/', dashboard, name='dashboard'),
    path('pie/', contacts_pie_chart, name='contacts_pie_chart'),
    path('no_contacts/', pnrs_without_contacts, name='pnrs_without_contacts'),
    path('export/', export_pnrs_to_excel, name='export_pnrs_to_excel'),
]
