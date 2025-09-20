from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('delivery-systems/', views.api_delivery_systems, name='api_delivery_systems'),
    path('offices-by-delivery-systems/', views.api_offices_by_delivery_systems, name='api_offices_by_delivery_systems'),
    path('trends/', views.api_quality_trends, name='api_quality_trends'),
]