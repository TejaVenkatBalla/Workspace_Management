from django.core.management.base import BaseCommand
from myapp.models import Timeslot
from datetime import time

class Command(BaseCommand):
    help = 'Create hourly timeslots from 9 AM to 6 PM'

    def handle(self, *args, **kwargs):
        start_hour = 9
        end_hour = 18  # 6 PM
        created_count = 0

        for hour in range(start_hour, end_hour):
            start_time = time(hour=hour, minute=0)
            end_time = time(hour=hour+1, minute=0)
            timeslot, created = Timeslot.objects.get_or_create(
                start_time=start_time,
                end_time=end_time
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} timeslots.'))
