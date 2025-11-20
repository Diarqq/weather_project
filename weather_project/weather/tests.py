import json
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.test import Client, RequestFactory, TestCase
from django.utils import timezone

from weather.api_client import WeatherAPIClient
from weather.models import WeatherQuery
from weather.services import WeatherService
from weather.views import weather_api


@pytest.mark.django_db
class TestWeatherService(TestCase):
    def setUp(self):
        WeatherQuery.objects.all().delete()

    @patch("weather.services.WeatherAPIClient")
    def test_cache_reuse_within_5_minutes(self, MockAPIClient):
        mock_client = MockAPIClient.return_value
        mock_client.get_weather.return_value = None
        WeatherQuery.objects.create(
            city_name="London",
            temperature=15.0,
            weather_description="test",
            units="metric",
            served_from_cache=False,
        )
        service = WeatherService()
        result = service.get_weather("London", "metric")
        mock_client.get_weather.assert_not_called()
        self.assertIsNotNone(result)

    @patch("weather.services.WeatherAPIClient")
    def test_cache_expires_after_5_minutes(self, MockAPIClient):
        mock_client = MockAPIClient.return_value
        mock_client.get_weather.return_value = {
            "name": "London",
            "main": {"temp": 20.0, "humidity": 65, "pressure": 1012},
            "weather": [{"description": "sunny"}],
        }

        old_time = timezone.now() - timedelta(minutes=6)
        old_query = WeatherQuery.objects.create(
            city_name="London",
            temperature=15.0,
            weather_description="old_weather",
            units="metric",
            served_from_cache=False,
        )
        old_query.timestamp = old_time
        old_query.save()

        service = WeatherService()
        result = service.get_weather("London", "metric")

        mock_client.get_weather.assert_called_once_with("London", "metric")
        self.assertEqual(result["temperature"], 20.0)
        self.assertFalse(result["served_from_cache"])

    def test_city_filter(self):
        WeatherQuery.objects.create(
            city_name="London",
            temperature=15.0,
            weather_description="sunny",
            units="metric",
        )
        WeatherQuery.objects.create(
            city_name="Paris",
            temperature=18.0,
            weather_description="cloudy",
            units="metric",
        )

        client = Client()
        response = client.get("/history/?city=London")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "London")
        self.assertNotContains(response, "Paris")

    def test_date_filter(self):

        from datetime import datetime

        WeatherQuery.objects.create(
            city_name="Test",
            temperature=15.0,
            weather_description="test",
            units="metric",
            timestamp=timezone.make_aware(datetime(2024, 1, 15)),
        )
        WeatherQuery.objects.create(
            city_name="Test",
            temperature=16.0,
            weather_description="test",
            units="metric",
            timestamp=timezone.make_aware(datetime(2024, 1, 20)),
        )

        from django.test import Client

        client = Client()
        response = client.get("/history/?date_from=2024-01-10&date_to=2024-01-18")

        assert response.status_code == 200

    @patch("weather.api_client.requests.get")
    def test_api_client_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "London",
            "main": {"temp": 15.5, "humidity": 65, "pressure": 1012},
            "weather": [{"description": "clear sky"}],
        }
        mock_get.return_value = mock_response

        client = WeatherAPIClient()
        result = client.get_weather("London", "metric")

        assert result is not None
        assert result["name"] == "London"
        assert result["main"]["temp"] == 15.5
        mock_get.assert_called_once()

    @patch("weather.api_client.requests.get")
    def test_api_client_failure(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = WeatherAPIClient()
        result = client.get_weather("InvalidCity", "metric")

        assert result is None

    def test_our_code_handles_rate_limit(self):

        factory = RequestFactory()
        request = factory.get("/api/", {"city": "London"})
        request.limited = True
        response = weather_api(request)

        self.assertEqual(response.status_code, 429)
        response_data = json.loads(response.content)
        self.assertIn("error", response_data)

    def test_no_db_write_when_rate_limited(self):
        initial_count = WeatherQuery.objects.count()

        factory = RequestFactory()
        request = factory.get("/api/", {"city": "London"})
        request.limited = True

        weather_api(request)

        self.assertEqual(WeatherQuery.objects.count(), initial_count)

    def test_pagination(self):
        for i in range(15):
            WeatherQuery.objects.create(
                city_name=f"City{i}",
                temperature=10 + i,
                weather_description="test",
                units="metric",
            )

        client = Client()
        response = client.get("/history/")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context["queries"]), 10)

        response = client.get("/history/?page=2")
        self.assertEqual(len(response.context["queries"]), 5)
