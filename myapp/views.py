from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from rest_framework.views import APIView
from .models import *
from .serializers import *
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

        if has_booking_conflict(room, date, time_slot):
            return Response({"error": "No available room for the selected slot and type."}, status=400)

        if room.room_type == 'conference':
            team = data.get('team')
            if not team:
                return Response({"error": "Team required for conference room."}, status=400)
            if team_seat_count(team) < 3:
                return Response({"error": "Team must have at least 3 members (age >= 10)."}, status=400)
            if request.user != team.created_by:
                return Response({"error": "Only team lead can book conference rooms."}, status=403)

            # ✅ Save with team + user
            booking = serializer.save(team=team, user=request.user)

        elif room.room_type == 'shared':
            existing_shared = Booking.objects.filter(
                room=room, date=date,
                time_slot=time_slot,
                is_active=True
            ).count()
            if existing_shared >= 4:
                return Response({"error": "No available shared desk for the selected slot."}, status=400)

            # ✅ Save with user only
            booking = serializer.save(user=request.user)

        elif room.room_type == 'private':
            # ✅ Save with user only
            booking = serializer.save(user=request.user)

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
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = BookingListSerializer

    def get_queryset(self):
        return Booking.objects.filter(is_active=True)

from rest_framework import generics

class AvailableRoomsByDateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date = request.query_params.get('date')

        if not date:
            return Response({"error": "Missing date in query params."}, status=400)

        booked_rooms = Booking.objects.filter(
            date=date,
            is_active=True
        ).values_list('room_id', flat=True)

        available_rooms = Room.objects.exclude(id__in=booked_rooms)
        serializer = RoomSerializer(available_rooms, many=True)
        return Response(serializer.data)

class AvailableSlotsByRoomDateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        room_id = request.query_params.get('room')
        date = request.query_params.get('date')

        if not all([room_id, date]):
            return Response({"error": "Missing room or date in query params."}, status=400)

        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({"error": "Invalid room."}, status=400)

        booked_slots = Booking.objects.filter(
            room=room,
            date=date,
            is_active=True
        ).values_list('time_slot_id', flat=True)

        available_slots = Timeslot.objects.exclude(id__in=booked_slots)
        slots_data = [{"id": slot.id, "start_time": slot.start_time, "end_time": slot.end_time} for slot in available_slots]

        return Response(slots_data)




