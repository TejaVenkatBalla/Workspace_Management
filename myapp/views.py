from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from rest_framework.views import APIView
from .models import *
from .serializers import *
from rest_framework import generics
from datetime import date as dt_date
class SignupView(APIView):
    """
    API view to handle user signup and JWT token generation.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request to create a new user and return JWT tokens.
        """
        serializer = UserSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

# Custom permission class to restrict admin-only views
class IsAdmin(BasePermission):
    """
    Custom permission to allow access only to admin users.
    """
    def has_permission(self, request, view):
        """
        Check if the user has admin role.
        """
        return request.user and request.user.role == 'admin'

# Utility for conflict check
def has_booking_conflict(room, date, time_slot):
    """
    Check if there is an active booking conflict for the given room, date, and time slot.

    Args:
        room: Room instance to check.
        date: Date of the booking.
        time_slot: Time slot of the booking.

    Returns:
        bool: True if a conflict exists, False otherwise.
    """
    return Booking.objects.filter(
        room=room,
        date=date,
        time_slot=time_slot,
        is_active=True
    ).exists()

# Utility to calculate headcount
def team_seat_count(team):
    """
    Calculate the number of team members aged 10 or older.

    Args:
        team: Team instance.

    Returns:
        int: Count of team members aged 10 or older.
    """
    count = 0
    for member in team.members.all():
        if member.age >= 10:
            count += 1
    return count

class BookingCreateView(APIView):
    """
    API view to create a new booking for rooms including conference, shared, and private types.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """
        Handle POST request to create a booking with validation for room type and user/team eligibility.

        Returns:
            Response: Booking ID on success or error message on failure.
        """
        serializer = BookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        room = data['room']
        date = data['date']
        time_slot = data['time_slot']
        user = request.user
        team = data['team'] if 'team' in data else None

        
        if not time_slot:
            return Response({"error": "Missing time_slot in request data."}, status=400)
        
        if not room:
            return Response({"error": "Missing room in request data."}, status=400)

        if team and room.room_type != 'conference':
            return Response({"error": "Team can only book conference rooms."}, status=400)
        
        elif room.room_type == 'conference':
            if not team:
                return Response({"error": "Team required for conference room."}, status=400)
            if team_seat_count(team) < 3:
                return Response({"error": "Team must have at least 3 members (age >= 10)."}, status=400)
            if user != team.created_by: # Only team lead can book conference rooms
                return Response({"error": "Only team lead can book conference rooms."}, status=403)
            if has_booking_conflict(room, date, time_slot):
                return Response({"error": "Room is already booked for the selected date and time slot."}, status=400)
            else:
                booking = serializer.save(team=team)

        elif room.room_type == 'shared':
            # Check if user already has an active booking for any shared room at the same date and time_slot
            existing_booking = Booking.objects.filter(
                user=user,
                room__room_type='shared',
                date=date,
                time_slot=time_slot,
                is_active=True
            ).exists()
            if existing_booking:
                return Response({"error": "User has already booked a shared room for the selected date and time slot."}, status=400)

            # Find a shared desk room with availability
            shared_rooms = Room.objects.filter(room_type='shared')
            assigned_room = None
            for shared_room in shared_rooms:
                booking_count = Booking.objects.filter(
                    room=shared_room,
                    date=date,
                    time_slot=time_slot,
                    is_active=True
                ).count()
                if booking_count < 4:
                    assigned_room = shared_room
                    break
            if not assigned_room:
                return Response({"error": "No available shared desk for the selected slot."}, status=400)

            booking = serializer.save(user=user, room=assigned_room)

        elif room.room_type == 'private':
            if has_booking_conflict(room, date, time_slot):
                return Response({"error": "Room is already booked for the selected date and time slot."}, status=400)
            else:
                booking = serializer.save(user=user)

        return Response({"booking_id": booking.id}, status=201)

class BookingCancelView(APIView):
    """
    API view to cancel an existing active booking.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, booking_id):
        """
        Handle POST request to cancel a booking if the user is authorized.

        Args:
            booking_id (int): ID of the booking to cancel.

        Returns:
            Response: Success or error message.
        """
        try:
            booking = Booking.objects.select_for_update().get(id=booking_id, is_active=True)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found or already cancelled."}, status=404)

        if booking.team:
            if booking.team.created_by != request.user:
                return Response({"error": "Only team lead can cancel this booking."}, status=403)
        else:
            if booking.user != request.user:
                return Response({"error": "Only the booking user can cancel this booking."}, status=403)

        booking.is_active = False
        booking.save()
        return Response({"success": "Booking cancelled."})

class BookingListView(generics.ListAPIView):
    """
    API view to list active bookings for the authenticated user or all bookings for admin users.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer

    def get_queryset(self):
        """
        Get the queryset of bookings based on user role.

        Returns:
            QuerySet: Active bookings for the user or all active bookings for admin.
        """
        user = self.request.user
        if user.role == 'admin':
            return Booking.objects.filter(is_active=True)
        else:
            #return Booking.objects.filter(user=user, is_active=True)
            return Booking.objects.filter(models.Q(user=user) | models.Q(team__members=user), is_active=True).distinct()

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class AvailableRoomsAndSlotsByDateView(APIView):
    """
    API view to list available rooms and their available time slots for a given date and optional room type.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handle GET request to retrieve available rooms and slots.

        Query Parameters:
            date (str): Date to check availability for. Defaults to today if not provided.
            room_type (str): Optional room type filter.

        Returns:
            Response: Paginated list of rooms with available time slots or a 404 message if none available.
        """
        date = request.query_params.get('date')
        room_type = request.query_params.get('room_type')

        if not date:
            date = dt_date.today()

        if room_type:
            rooms = Room.objects.filter(room_type=room_type)
        else:
            rooms = Room.objects.all()

        paginator = PageNumberPagination()
        paginated_rooms = paginator.paginate_queryset(rooms, request)

        all_time_slots = Timeslot.objects.all()

        result = []

        for room in paginated_rooms:
            available_slots = []
            for time_slot in all_time_slots:
                if room.room_type == 'shared':
                    booking_count = Booking.objects.filter(
                        room=room,
                        date=date,
                        time_slot=time_slot,
                        is_active=True
                    ).count()
                    if booking_count < 4:
                        available_slots.append({
                            "id": time_slot.id,
                            "name": time_slot.name,
                            "start_time": time_slot.start_time,
                            "end_time": time_slot.end_time
                        })
                else:
                    is_booked = Booking.objects.filter(
                        room=room,
                        date=date,
                        time_slot=time_slot,
                        is_active=True
                    ).exists()
                    if not is_booked:
                        available_slots.append({
                            "id": time_slot.id,
                            "name": time_slot.name,
                            "start_time": time_slot.start_time,
                            "end_time": time_slot.end_time
                        })

            if available_slots:
                result.append({
                    "room": {
                        "id": room.id,
                        "name": room.name,
                        "room_type": room.room_type,
                        "capacity": room.capacity,
                    },
                    "available_slots": available_slots
                })
            else:
                return Response({"message": "No available rooms or slots for the selected date."}, status=404)

        return paginator.get_paginated_response(result)

# Team CRUD views
class TeamListCreateView(generics.ListCreateAPIView):
    """
    API view to list and create teams. Admins see all teams; users see teams they created or belong to.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TeamSerializer

    def get_queryset(self):
        """
        Get queryset of teams based on user role.

        Returns:
            QuerySet: Teams visible to the user.
        """
        user = self.request.user
        if user.role == 'admin':
            return Team.objects.all()
        # Users can see teams they created or are members of
        return Team.objects.filter(models.Q(created_by=user) | models.Q(members=user)).distinct()
        #return Team.objects.all()
    def perform_create(self, serializer):
        """
        Save the team with the current user as creator.
        """
        serializer.save(created_by=self.request.user)

class TeamRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a team. Admins can access all; users only their own teams.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TeamSerializer
    lookup_field = 'id'

    def get_queryset(self):
        """
        Get queryset of teams based on user role.

        Returns:
            QuerySet: Teams accessible to the user.
        """
        user = self.request.user
        if user.role == 'admin':
            return Team.objects.all()
        # Users can only update/delete teams they created
        return Team.objects.filter(created_by=user)

# API for user to join a team
class JoinTeamView(APIView):
    """
    API view for a user to join a team.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        """
        Handle POST request to add the authenticated user to the specified team.

        Args:
            team_id (int): ID of the team to join.

        Returns:
            Response: Success or error message.
        """
        user = request.user
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            return Response({"error": "Team not found."}, status=404)

        if user in team.members.all():
            return Response({"message": "User already a member of the team."}, status=200)

        team.members.add(user)
        team.save()
        return Response({"message": "User added to the team."}, status=200)

# API for admin to add any user to any team
class AdminAddUserToTeamView(APIView):
    """
    API view for admin users to add any user to any team.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        """
        Handle POST request to add a user to a team by admin.

        Expects 'team_id' and 'user_id' in request data.

        Returns:
            Response: Success or error message.
        """
        team_id = request.data.get('team_id')
        user_id = request.data.get('user_id')

        if not team_id or not user_id:
            return Response({"error": "team_id and user_id are required."}, status=400)

        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            return Response({"error": "Team not found."}, status=404)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        if user in team.members.all():
            return Response({"message": "User already a member of the team."}, status=200)

        team.members.add(user)
        team.save()
        return Response({"message": "User added to the team by admin."}, status=200)

# Admin CRUD views for User
class UserListCreateView(generics.ListCreateAPIView):
    """
    API view to list and create users. Admins only.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = UserSerializer

    def get_queryset(self):
        """
        Get queryset of all users.

        Returns:
            QuerySet: All users.
        """
        return User.objects.all()

class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a user. Admins only.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = UserSerializer
    lookup_field = 'id'

    def get_queryset(self):
        """
        Get queryset of all users.

        Returns:
            QuerySet: All users.
        """
        return User.objects.all()

# Admin CRUD views for Room
class RoomListCreateView(generics.ListCreateAPIView):
    """
    API view to list and create rooms. Admins only.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = RoomSerializer

    def get_queryset(self):
        """
        Get queryset of all rooms.

        Returns:
            QuerySet: All rooms.
        """
        return Room.objects.all()

class RoomRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a room. Admins only.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = RoomSerializer
    lookup_field = 'id'

    def get_queryset(self):
        """
        Get queryset of all rooms.

        Returns:
            QuerySet: All rooms.
        """
        return Room.objects.all()

# Admin CRUD views for Timeslot
class TimeslotListCreateView(generics.ListCreateAPIView):
    """
    API view to list and create timeslots. Admins only.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = TimeslotSerializer

    def get_queryset(self):
        """
        Get queryset of all timeslots.

        Returns:
            QuerySet: All timeslots.
        """
        return Timeslot.objects.all()

class TimeslotRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a timeslot. Admins only.
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = TimeslotSerializer
    lookup_field = 'id'

    def get_queryset(self):
        """
        Get queryset of all timeslots.

        Returns:
            QuerySet: All timeslots.
        """
        return Timeslot.objects.all()


