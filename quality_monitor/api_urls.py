from django.urls import path
from . import api_views

urlpatterns = [
    path('channel-groupings/', api_views.get_channel_groupings, name='api_channel_groupings'),
    path('offices-by-channels/', api_views.get_offices_by_channels, name='api_offices_by_channels'),
    path('channel-office-stats/', api_views.get_channel_office_stats, name='api_channel_office_stats'),
]