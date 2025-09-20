from django.urls import path
from . import views

app_name = 'quality_monitor'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('export/', views.export_pnrs_to_excel, name='export_pnrs_to_excel'),
    
    # API endpoints
    path('api/trends/', views.api_quality_trends, name='api_quality_trends'),
    path('api/delivery-systems/', views.api_delivery_systems, name='api_delivery_systems'),
    path('api/offices-by-delivery-systems/', views.api_offices_by_delivery_systems, name='api_offices_by_delivery_systems'),
    path('api/detailed-pnrs/', views.api_detailed_pnrs, name='api_detailed_pnrs'),
]