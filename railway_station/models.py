from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Station(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

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

    def __str__(self) -> str:
        return f"{self.name}, type: {self.train_type}"

    @property
    def capacity(self) -> int:
        return self.railcar_num * self.seats_in_railcar

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
        blank=False, null=False, validators=[MinValueValidator(timezone.now())]
    )
    arrival_time = models.DateTimeField(blank=False, null=False)

    def clean(self):
        if self.arrival_time < self.departure_time:
            return ValidationError(
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

    def clean(self) -> None:
        train = self.trip.train
        if not (1 <= self.railcar <= train.railcar_num):
            raise ValidationError(
                f"Railcar number must be in available range from 1 to {train.railcar_num}"
            )
        if not (1 <= self.seat <= train.seats_in_railcar):
            raise ValidationError(
                f"Seat number must be in available range from 1 to {train.seats_in_railcar}"
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
            f"{self.trip.route.source} - {self.trip.route.destination} "
            f"{self.trip.departure_time} - {self.trip.arrival_time} "
            f"(railcar: {self.railcar}, seat: {self.seat})"
        )

    class Meta:
        unique_together = ("railcar", "seat")
        ordering = ["railcar", "seat"]
