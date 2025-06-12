from django.core.management.base import BaseCommand
from myapp.models import Room

class Command(BaseCommand):
    help = 'Create 15 rooms: 8 private, 4 conference, 3 shared'

    def handle(self, *args, **kwargs):
        # Clear existing rooms (optional)
        Room.objects.all().delete()

        # Create 8 private rooms
        for i in range(1, 9):
            Room.objects.create(
                name=f'Private Room {i}',
                room_type='private',
                capacity=1
            )

        # Create 4 conference rooms
        for i in range(1, 5):
            Room.objects.create(
                name=f'Conference Room {i}',
                room_type='conference',
                capacity=10
            )

        # Create 3 shared desks
        for i in range(1, 4):
            Room.objects.create(
                name=f'Shared Desk {i}',
                room_type='shared',
                capacity=4
            )

        self.stdout.write(self.style.SUCCESS('Successfully created 15 rooms'))
