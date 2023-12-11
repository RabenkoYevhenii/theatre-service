from django.contrib.auth.models import User
from django.db import models


class Play(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    actors = models.ManyToManyField("Actor", related_name="plays")
    genres = models.ManyToManyField("Genre", related_name="plays")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return self.first_name + " " + self.last_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TheatreHall(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    class Meta:
        ordering = ["name"]

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class Performance(models.Model):
    play = models.ForeignKey(
        Play, on_delete=models.CASCADE, related_name="performances"
    )
    theatre_hall = models.ForeignKey(
        TheatreHall, on_delete=models.CASCADE, related_name="performances"
    )
    showtime = models.DateTimeField()

    class Meta:
        ordering = ["showtime"]

    def __str__(self):
        return f"{self.play.title} {self.showtime}"


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reservations"
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.first_name} at {self.created_at}"


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    performance = models.ForeignKey(
        Performance, on_delete=models, related_name="tickets"
    )
    reservation = models.ForeignKey(
        Reservation, on_delete=models, related_name="tickets"
    )

    class Meta:
        ordering = ["row", "seat"]

    def __str__(self):
        return f"{self.performance.play.title} {self.row} {self.seat}"
