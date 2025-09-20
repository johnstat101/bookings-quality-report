from django.urls import path, include
from .views import home_view, upload_excel, export_pnrs_to_excel, api_quality_trends, api_delivery_systems, api_offices_by_delivery_systems

app_name = 'quality_monitor'

urlpatterns = [
    path('', home_view, name='home'),
    path('upload/', upload_excel, name='upload_excel'),
    path('export/', export_pnrs_to_excel, name='export_pnrs_to_excel'),
    path('api/trends/', api_quality_trends, name='api_quality_trends'),
    path('api/delivery-systems/', api_delivery_systems, name='api_delivery_systems'),
    path('api/offices-by-delivery-systems/', api_offices_by_delivery_systems, name='api_offices_by_delivery_systems'),
]