from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import BookingViewSet, KQOfficeViewSet, KQStaffViewSet, TravelAgencyViewSet

router = DefaultRouter()
router.register(r'bookings', BookingViewSet)
router.register(r'offices', KQOfficeViewSet)
router.register(r'staff', KQStaffViewSet)
router.register(r'agencies', TravelAgencyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]