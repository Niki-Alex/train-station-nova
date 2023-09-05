import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def validate_departure_time(value):
    if value.replace(tzinfo=timezone.get_current_timezone()) < timezone.now():
        raise ValidationError("Departure time should be in the future!")


def train_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}.{extension}"

    return os.path.join("uploads/trains/", filename)


class Station(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    @property
    def name_by_coordinate(self) -> str:
        return f"{self.name} ({self.latitude} - {self.longitude})"

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["name"]


class Route(models.Model):
    source = models.ForeignKey(
        Station, on_delete=models.CASCADE, related_name="source_routes"
    )
    destination = models.ForeignKey(
        Station, on_delete=models.CASCADE, related_name="destination_routes"
    )
    distance = models.IntegerField(validators=[MinValueValidator(1)])

    def clean(self):
        if self.source == self.destination:
            raise ValidationError("Source and destination cannot be the same")

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        self.full_clean()
        return super(Route, self).save(
            force_insert, force_update, using, update_fields
        )

    @property
    def full_route(self) -> str:
        return f"{self.source} - {self.destination}"

    def __str__(self) -> str:
        return f"Source: {self.source}, destination: {self.destination}"


class TrainType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class Train(models.Model):
    name = models.CharField(max_length=255)
    railcar_num = models.IntegerField(validators=[MinValueValidator(1)])
    seats_in_railcar = models.IntegerField(validators=[MinValueValidator(1)])
    train_type = models.ForeignKey(
        TrainType, on_delete=models.CASCADE, related_name="trains"
    )
    image = models.ImageField(null=True, upload_to=train_image_file_path)

    def __str__(self) -> str:
        return f"{self.name}, type: {self.train_type}"

    @property
    def capacity(self) -> int:
        return self.railcar_num * self.seats_in_railcar

    @property
    def important_information(self) -> str:
        return (f"{self.name}, type: {self.train_type}, "
                f"railcar_num: {self.railcar_num}, "
                f"seats_in_railcar: {self.seats_in_railcar}")

    class Meta:
        ordering = ["name"]


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Trip(models.Model):
    crew = models.ManyToManyField(to=Crew, related_name="trips")
    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name="trips"
    )
    train = models.ForeignKey(
        Train, on_delete=models.CASCADE, related_name="trips"
    )
    departure_time = models.DateTimeField(
        blank=False, null=False, validators=[validate_departure_time]
    )
    arrival_time = models.DateTimeField(blank=False, null=False)

    def clean(self):
        if self.arrival_time <= self.departure_time:
            raise ValidationError(
                "Arrival time cannot be earlier than departure time!"
            )

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        self.full_clean()
        return super(Trip, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self) -> str:
        return (f"{self.route.source.name} - {self.route.destination.name}, "
                f"departure time: {self.departure_time}, "
                f"arrival time: {self.arrival_time}")

    class Meta:
        ordering = ["-departure_time"]


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.created_at)

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    railcar = models.IntegerField(validators=[MinValueValidator(1)])
    seat = models.IntegerField(validators=[MinValueValidator(1)])
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, related_name="tickets"
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="tickets"
    )

    @staticmethod
    def validate_railcar_and_seat(
            railcar: int, num_railcars: int, seat: int, num_seats: int, error_to_raise
    ):
        if not (1 <= railcar <= num_railcars):
            raise error_to_raise(
                f"Railcar number must be in available "
                f"range from 1 to {num_railcars}, not {railcar}"
            )
        if not (1 <= seat <= num_seats):
            raise error_to_raise(
                f"Seat number must be in available range "
                f"from 1 to {num_seats}, not {seat}"
            )

    def clean(self) -> None:
        Ticket.validate_railcar_and_seat(
            self.railcar,
            self.trip.train.railcar_num,
            self.seat,
            self.trip.train.seats_in_railcar,
            ValidationError
        )

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self) -> str:
        return (
            f"{self.trip.route.source} - {self.trip.route.destination}, "
            f"{self.trip.departure_time} - {self.trip.arrival_time}, "
            f"(railcar: {self.railcar}, seat: {self.seat})"
        )

    class Meta:
        unique_together = ("railcar", "seat")
        ordering = ["railcar", "seat"]
