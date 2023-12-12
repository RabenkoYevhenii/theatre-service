from django.contrib import admin

from theatre_service.models import (
    Play,
    Actor,
    Genre,
    TheatreHall,
    Performance,
    Reservation,
    Ticket,
)

admin.site.register(Play)
admin.site.register(Actor)
admin.site.register(Genre)
admin.site.register(TheatreHall)
admin.site.register(Performance)
admin.site.register(Reservation)
admin.site.register(Ticket)
