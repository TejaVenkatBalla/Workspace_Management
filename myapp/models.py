import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

# ----------------------
# Custom User Model
# ----------------------
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, name, email, password=None, **extra_fields):
        if not name:
            raise ValueError('The Name field is required')
        email = self.normalize_email(email)
        user = self.model(name=name, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, name, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(name, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'name'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        return self.name

    

# ----------------------
# Team Model
# ----------------------
class Team(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_teams')
    members = models.ManyToManyField(User, related_name='teams')

    def __str__(self):
        return self.name

# ----------------------
# Room Model
# ----------------------
class Room(models.Model):
    ROOM_TYPES = (
        ('private', 'Private'),
        ('conference', 'Conference'),
        ('shared', 'Shared'),
    )
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    capacity = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.room_type})"

# ----------------------
# Booking Model
# ----------------------
class Timeslot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"

class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    date = models.DateField()
    time_slot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # for private/shared
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)  # for conference
    timestamp = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(team__isnull=False),
                name='booking_must_have_user_or_team'
            ),
            models.CheckConstraint(
                check=~(models.Q(user__isnull=False) & models.Q(team__isnull=False)),
                name='booking_cannot_have_both_user_and_team'
            ),
            models.UniqueConstraint(
                fields=['room', 'date', 'time_slot'],
                condition=models.Q(is_active=True),
                name='unique_active_booking_per_slot'
            )
        ]

    def __str__(self):
        if self.user:
            return f"Booking by {self.user.name} on {self.date} ({self.time_slot})"
        elif self.team:
            return f"Booking by team {self.team.name} on {self.date} ({self.time_slot})"
        return f"Booking on {self.date} ({self.time_slot})"
