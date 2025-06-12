from django.urls import path
from .views import (
    SignupView,
    BookingCreateView,
    BookingCancelView,
    BookingListView,
    AvailableRoomsView,
)
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    # path('login/', LoginView.as_view(), name='login'),

    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('bookings/', BookingCreateView.as_view(), name='create-booking'),
    path('cancel/<uuid:booking_id>/', BookingCancelView.as_view(), name='cancel-booking'),
    path('bookings/list/', BookingListView.as_view(), name='booking-list'),
    path('rooms/available/', AvailableRoomsView.as_view(), name='available-rooms'),
]
