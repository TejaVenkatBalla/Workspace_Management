from django.contrib import admin

from .models import User, Team, Room, Booking


admin.site.register(User)
admin.site.register(Team)
admin.site.register(Room)
admin.site.register(Booking)

