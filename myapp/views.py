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
    permission_classes = [AllowAny]

    def post(self, request):
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
    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'

# Utility for conflict check
def has_booking_conflict(room, date, time_slot):
    return Booking.objects.filter(
        room=room,
        date=date,
        time_slot=time_slot,
        is_active=True
    ).exists()

# Utility to calculate headcount
def team_seat_count(team):
    count = 0
    for member in team.members.all():
        if member.age >= 10:
            count += 1
    return count

class BookingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
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
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, booking_id):
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
    permission_classes = [IsAuthenticated]
    serializer_class = BookingListSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Booking.objects.filter(is_active=True)
        else:
            #return Booking.objects.filter(user=user, is_active=True)
            return Booking.objects.filter(models.Q(user=user) | models.Q(team__members=user), is_active=True).distinct()

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class AvailableRoomsAndSlotsByDateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
    permission_classes = [IsAuthenticated]
    serializer_class = TeamSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Team.objects.all()
        # Users can see teams they created or are members of
        return Team.objects.filter(models.Q(created_by=user) | models.Q(members=user)).distinct()
        #return Team.objects.all()
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class TeamRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TeamSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Team.objects.all()
        # Users can only update/delete teams they created
        return Team.objects.filter(created_by=user)

# API for user to join a team
class JoinTeamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
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
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
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
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.all()

class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = UserSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return User.objects.all()

# Admin CRUD views for Room
class RoomListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = RoomSerializer

    def get_queryset(self):
        return Room.objects.all()

class RoomRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = RoomSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Room.objects.all()

# Admin CRUD views for Timeslot
class TimeslotListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = TimeslotSerializer

    def get_queryset(self):
        return Timeslot.objects.all()

class TimeslotRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = TimeslotSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Timeslot.objects.all()




