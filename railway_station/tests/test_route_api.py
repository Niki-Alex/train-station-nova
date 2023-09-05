import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from railway_station.models import Route, Station
from railway_station.serializers import RouteListSerializer, RouteDetailSerializer

ROUTE_URL = reverse("railway_station:route-list")


def sample_station(**params):

    defaults = {
        "name": f"Kiev-{uuid.uuid4()}",
        "latitude": 1.1,
        "longitude": 5.1,
    }
    defaults.update(params)

    return Station.objects.create(**defaults)


def sample_route(**params):

    defaults = {
        "source": sample_station(),
        "destination": sample_station(),
        "distance": 30,
    }
    defaults.update(params)

    return Route.objects.create(**defaults)


def route_detail_url(route_id):
    return reverse("railway_station:route-detail", args=[route_id])


class UnauthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_routes(self):
        sample_route()
        sample_route()

        res = self.client.get(ROUTE_URL)

        routes = Route.objects.all()
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_route_by_source_destination(self):
        route_1 = sample_route(source=sample_station(name="Paris"))
        route_2 = sample_route(source=sample_station(name="Rim"))
        route_3 = sample_route(destination=sample_station(name="London"))

        res_1 = self.client.get(ROUTE_URL, {"source": route_1.source})
        res_2 = self.client.get(ROUTE_URL, {"source": route_2.source})
        res_3 = self.client.get(ROUTE_URL, {"destination": route_3.destination})

        serializer_1 = RouteListSerializer(route_1)
        serializer_2 = RouteListSerializer(route_2)
        serializer_3 = RouteListSerializer(route_3)

        self.assertIn(serializer_1.data, res_1.data)
        self.assertNotIn(serializer_2.data, res_1.data)
        self.assertNotIn(serializer_3.data, res_1.data)

        self.assertNotIn(serializer_1.data, res_2.data)
        self.assertIn(serializer_2.data, res_2.data)
        self.assertNotIn(serializer_3.data, res_2.data)

        self.assertNotIn(serializer_1.data, res_3.data)
        self.assertNotIn(serializer_2.data, res_3.data)
        self.assertIn(serializer_3.data, res_3.data)

    def test_retrieve_route_detail(self):
        route = sample_route()

        url = route_detail_url(route.id)

        res = self.client.get(url)

        serializer = RouteDetailSerializer(route)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_create_route_unauthorized(self):
        station_1 = sample_station()
        station_2 = sample_station()
        route = {
            "source": station_1.id,
            "destination": station_2.id,
            "distance": 30,
        }

        res = self.client.post(ROUTE_URL, route)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@i.ua", "password"
        )
        self.client.force_authenticate(self.user)

    def test_create_route_forbidden(self):
        station_1 = sample_station()
        station_2 = sample_station()
        route = {
            "source": station_1.id,
            "destination": station_2.id,
            "distance": 30,
        }

        res = self.client.post(ROUTE_URL, route)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@i.ua",
            "password123",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_route(self):
        station_1 = sample_station()
        station_2 = sample_station()
        route = {
            "source": station_1.id,
            "destination": station_2.id,
            "distance": 30,
        }

        res = self.client.post(ROUTE_URL, route)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_delete_route(self):
        route = sample_route()
        url = route_detail_url(route.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
