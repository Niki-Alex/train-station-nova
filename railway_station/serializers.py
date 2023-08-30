from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from railway_station.models import (
    Station,
    Route,
    TrainType,
    Train,
    Crew,
    Trip,
    Order,
    Ticket,
)


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="source.name", read_only=True)
    destination = serializers.CharField(source="destination.name", read_only=True)

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ("id", "name")


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "name", "railcar_num", "seats_in_railcar", "train_type", "capacity")


class TrainListSerializer(serializers.ModelSerializer):
    train_type = serializers.CharField(source="train_type.name", read_only=True)

    class Meta:
        model = Train
        fields = ("id", "name", "railcar_num", "seats_in_railcar", "train_type", "capacity")


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name")


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ("id", "crew", "route", "train", "departure_time", "arrival_time")


class TripListSerializer(serializers.ModelSerializer):
    crew = serializers.SlugRelatedField(many=True, read_only=True, slug_field="full_name")
    route = serializers.SlugRelatedField(many=False, read_only=True, slug_field="full_route")
    train = serializers.SlugRelatedField(many=False, read_only=True, slug_field="important_information")

    class Meta:
        model = Trip
        fields = ("id", "crew", "route", "train", "departure_time", "arrival_time")


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "railcar", "seat", "trip", "order")


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "created_at", "user")
