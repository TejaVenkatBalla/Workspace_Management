from django.urls import path, include
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView


urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('bookings/', BookingCreateView.as_view(), name='create-booking'),
    path('cancel/<uuid:booking_id>/', BookingCancelView.as_view(), name='cancel-booking'),
    path('bookings/list/', BookingListView.as_view(), name='booking-list'),
    
    path('rooms/available/', AvailableRoomsAndSlotsByDateView.as_view(), name='available-rooms-slots'),

    # Team CRUD APIs
    path('teams/', TeamListCreateView.as_view(), name='team-list-create'),
    path('teams/<int:id>/', TeamRetrieveUpdateDestroyView.as_view(), name='team-detail'),

    # Join team API
    path('teams/<int:team_id>/join/', JoinTeamView.as_view(), name='join-team'),

    # Admin add user to team
    path('admin/add-user-to-team/', AdminAddUserToTeamView.as_view(), name='admin-add-user-to-team'),

    # Admin CRUD for User
    path('admin/users/', UserListCreateView.as_view(), name='admin-user-list-create'),
    path('admin/users/<int:id>/', UserRetrieveUpdateDestroyView.as_view(), name='admin-user-detail'),

    # Admin CRUD for Room
    path('admin/rooms/', RoomListCreateView.as_view(), name='admin-room-list-create'),
    path('admin/rooms/<int:id>/', RoomRetrieveUpdateDestroyView.as_view(), name='admin-room-detail'),

    # Admin CRUD for Timeslot
    path('admin/timeslots/', TimeslotListCreateView.as_view(), name='admin-timeslot-list-create'),
    path('admin/timeslots/<int:id>/', TimeslotRetrieveUpdateDestroyView.as_view(), name='admin-timeslot-detail'),
]
