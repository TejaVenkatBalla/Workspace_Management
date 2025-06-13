
from rest_framework import serializers
from .models import User, Team, Room, Booking, Timeslot
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'age', 'gender', 'role']


class TeamSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())

    class Meta:
        model = Team
        fields = ['id', 'name', 'created_by', 'members']
        read_only_fields = ['created_by']

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'name', 'room_type', 'capacity']

class TimeslotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeslot
        fields = ['id', 'start_time', 'end_time']
        read_only_fields = ['id']

class BookingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(), required=False)
    room = serializers.CharField(write_only=True)
    time_slot = serializers.CharField(write_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'room', 'date', 'time_slot',
            'user', 'team', 'timestamp', 'is_active'
        ]
        read_only_fields = ['id', 'timestamp', 'is_active']

    def validate(self, attrs):
        room_name = attrs.get('room')
        time_slot_name = attrs.get('time_slot')

        try:
            room = Room.objects.get(name=room_name)
        except Room.DoesNotExist:
            raise serializers.ValidationError({'room': f'Room with name "{room_name}" does not exist.'})

        try:
            time_slot = Timeslot.objects.get(name=time_slot_name)
        except Timeslot.DoesNotExist:
            raise serializers.ValidationError({'time_slot': f'Timeslot with name "{time_slot_name}" does not exist.'})

        attrs['room'] = room
        attrs['time_slot'] = time_slot
        return attrs

class BookingListSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    team = TeamSerializer()
    room = RoomSerializer()

    class Meta:
        model = Booking
        fields = '__all__'

User = get_user_model()
class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'age', 'gender', 'role']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.get('role', 'user')

        user = User(**validated_data)
        user.password = make_password(password)

        # If role is 'admin', mark the user as a Django superuser
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True

        user.save()
        return user

