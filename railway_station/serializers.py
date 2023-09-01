from django.db import transaction
from rest_framework import serializers

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


class RouteListSerializer(RouteSerializer):
    source = serializers.CharField(source="source.name", read_only=True)
    destination = serializers.CharField(source="destination.name", read_only=True)


class RouteDetailSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(many=False, read_only=True, slug_field="name_by_coordinate")
    destination = serializers.SlugRelatedField(many=False, read_only=True, slug_field="name_by_coordinate")


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


class TripListSerializer(TripSerializer):
    crew = serializers.SlugRelatedField(many=True, read_only=True, slug_field="full_name")
    route = serializers.SlugRelatedField(many=False, read_only=True, slug_field="full_route")
    train = serializers.SlugRelatedField(many=False, read_only=True, slug_field="important_information")
    departure_time = serializers.DateTimeField(format="%Y-%m-%d, %H:%M")
    arrival_time = serializers.DateTimeField(format="%Y-%m-%d, %H:%M")


class TripToOrderListSerializer(TripListSerializer):
    train = serializers.SlugRelatedField(many=False, read_only=True, slug_field="name")
    train_type = serializers.CharField(source="train.train_type.name", read_only=True)

    class Meta:
        model = Trip
        fields = ("id", "route", "train", "train_type", "departure_time", "arrival_time")


class TripDetailSerializer(TripListSerializer):
    route = RouteListSerializer(many=False, read_only=True)
    train = TrainSerializer(many=False, read_only=True)
    departure_time = serializers.DateTimeField(read_only=True)
    arrival_time = serializers.DateTimeField(read_only=True)


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs)
        if not (1 <= attrs["railcar"] <= attrs["trip"].train.railcar_num):
            raise serializers.ValidationError(
                f"Railcar number must be in available range "
                f"from 1 to {attrs['trip'].train.railcar_num}, not {attrs['railcar']}"
            )
        if not (1 <= attrs["seat"] <= attrs["trip"].train.seats_in_railcar):
            raise serializers.ValidationError(
                f"Seat number must be in available range "
                f"from 1 to {attrs['trip'].train.seats_in_railcar}, not {attrs['seat']}"
            )

        return data

    class Meta:
        model = Ticket
        fields = ("id", "railcar", "seat", "trip")


class TicketListSerializer(TicketSerializer):
    trip = TripToOrderListSerializer(many=False, read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("railcar", "seat")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d, %H:%M", read_only=True)
