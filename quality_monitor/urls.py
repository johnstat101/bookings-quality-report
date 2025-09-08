from django.urls import path, include
from .views import home_view, contacts_pie_chart, pnrs_without_contacts, export_pnrs_to_excel, upload_excel, dashboard, api_quality_trends, api_channel_groupings, api_offices_by_channels

urlpatterns = [
    # Web interface URLs
    path('', home_view, name='home'),
    path('upload/', upload_excel, name='upload_excel'),
    path('dashboard/', dashboard, name='dashboard'),
    path('pie/', contacts_pie_chart, name='contacts_pie_chart'),
    path('no_contacts/', pnrs_without_contacts, name='pnrs_without_contacts'),
    path('export/', export_pnrs_to_excel, name='export_pnrs_to_excel'),
    path('api/trends/', api_quality_trends, name='api_quality_trends'),
    path('api/channel-groupings/', api_channel_groupings, name='api_channel_groupings'),
    path('api/offices-by-channels/', api_offices_by_channels, name='api_offices_by_channels'),
]
