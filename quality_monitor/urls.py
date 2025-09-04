from django.urls import path, include
from .views import home_view, contacts_pie_chart, pnrs_without_contacts, export_pnrs_to_excel, upload_excel, dashboard, api_quality_trends

urlpatterns = [
    # Web interface URLs
    path('', home_view, name='home'),
    path('upload/', upload_excel, name='upload_excel'),
    path('dashboard/', dashboard, name='dashboard'),
    path('pie/', contacts_pie_chart, name='contacts_pie_chart'),
    path('no_contacts/', pnrs_without_contacts, name='pnrs_without_contacts'),
    path('export/', export_pnrs_to_excel, name='export_pnrs_to_excel'),
    path('api/trends/', api_quality_trends, name='api_quality_trends'),
    
    # DRF API URLs
    path('api/v1/', include('quality_monitor.api_urls')),
]
