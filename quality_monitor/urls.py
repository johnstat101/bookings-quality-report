from django.urls import path
from .views import home_view, upload_excel, export_pnrs_to_excel, api_quality_trends, api_channel_groupings, api_offices_by_channels

urlpatterns = [
    path('', home_view, name='home'),
    path('upload/', upload_excel, name='upload_excel'),
    path('export/', export_pnrs_to_excel, name='export_pnrs_to_excel'),
    path('api/trends/', api_quality_trends, name='api_quality_trends'),
    path('api/channel-groupings/', api_channel_groupings, name='api_channel_groupings'),
    path('api/offices-by-channels/', api_offices_by_channels, name='api_offices_by_channels'),
]
