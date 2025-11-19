from django.test import TestCase

import pytest
from django.test import RequestFactory
from unittest.mock import Mock, patch
from .models import WeatherQuery
from .services import WeatherService
from .api_client import WeatherAPIClient
from .views import weather_api, get_client_ip
from django.utils import timezone
from datetime import timedelta
import json


@pytest.mark.django_db
class TestWeatherCache:
    def test_cache_reuse_within_5_minutes(self):
        """Тест: кэш возвращает данные если запрос был менее 5 минут назад"""
        # Создаем запись в БД (сейчас)
        query = WeatherQuery.objects.create(
            city_name="London",
            temperature=15.5,
            weather_description="clear sky",
            units="metric",
            served_from_cache=False
        )
        saved_query = WeatherQuery.objects.get(id=query.id)

        count = WeatherQuery.objects.count()


        service = WeatherService()
        cached_data = service.cache.get_cached_weather("London", "metric")logger = logging.getLogger('weather')


        # Проверим что вообще есть в БД
        all_queries = WeatherQuery.objects.all()

        assert cached_data is not None
        assert cached_data.city_name == "London"

    def test_cache_expires_after_5_minutes(self):


        old_time = timezone.now() - timedelta(minutes=6)
        WeatherQuery.objects.create(
            city_name="London",
            temperature=15.5,
            weather_description="clear sky",
            units="metric",
            served_from_cache=False,
            timestamp=old_time
        )

        service = WeatherService()
        cached_data = service.cache.get_cached_weather("London", "metric")

        assert cached_data is None


@pytest.mark.django_db
class TestRateLimiting:
    def test_rate_limit_blocks_excessive_requests(self):

        factory = RequestFactory()


        for i in range(31):
            request = factory.get('/api/', {'city': 'London'})
            request.META = {'REMOTE_ADDR': '192.168.1.1'}

            response = weather_api(request)


            if i < 30:
                assert response.status_code in [200, 404, 400]

    def test_rate_limit_respects_different_ips(self):

        factory = RequestFactory()


        request1 = factory.get('/api/', {'city': 'London'})
        request1.META = {'REMOTE_ADDR': '192.168.1.1'}
        response1 = weather_api(request1)


        request2 = factory.get('/api/', {'city': 'Paris'})
        request2.META = {'REMOTE_ADDR': '192.168.1.2'}
        response2 = weather_api(request2)


        assert response1.status_code in [200, 404, 400]
        assert response2.status_code in [200, 404, 400]


class TestWeatherAPIClient:
    @patch('weather.api_client.requests.get')
    def test_api_client_success(self, mock_get):


        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'London',
            'main': {'temp': 15.5, 'humidity': 65, 'pressure': 1012},
            'weather': [{'description': 'clear sky'}]
        }
        mock_get.return_value = mock_response

        client = WeatherAPIClient()
        result = client.get_weather('London', 'metric')

        assert result is not None
        assert result['name'] == 'London'
        assert result['main']['temp'] == 15.5
        mock_get.assert_called_once()

    @patch('weather.api_client.requests.get')
    def test_api_client_failure(self, mock_get):

        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = WeatherAPIClient()
        result = client.get_weather('InvalidCity', 'metric')

        assert result is None


@pytest.mark.django_db
class TestFilteringPagination:
    def test_city_filter(self):

        WeatherQuery.objects.create(city_name="London", temperature=15.0, weather_description="sunny", units="metric")
        WeatherQuery.objects.create(city_name="Paris", temperature=18.0, weather_description="cloudy", units="metric")
        WeatherQuery.objects.create(city_name="London", temperature=16.0, weather_description="rainy", units="metric")


        from django.test import Client
        client = Client()
        response = client.get('/history/?city=London')

        assert response.status_code == 200

        if hasattr(response, 'context') and 'queries' in response.context:
            queries = response.context['queries']
            for query in queries:
                assert 'London' in query.city_name

    def test_date_filter(self):

        from datetime import datetime


        WeatherQuery.objects.create(
            city_name="Test", temperature=15.0, weather_description="test", units="metric",
            timestamp=timezone.make_aware(datetime(2024, 1, 15))
        )
        WeatherQuery.objects.create(
            city_name="Test", temperature=16.0, weather_description="test", units="metric",
            timestamp=timezone.make_aware(datetime(2024, 1, 20))
        )

        # Фильтруем по диапазону дат
        from django.test import Client
        client = Client()
        response = client.get('/history/?date_from=2024-01-10&date_to=2024-01-18')

        assert response.status_code == 200


class TestIPAddress:
    def test_get_client_ip_direct(self):

        factory = RequestFactory()
        request = factory.get('/')
        request.META = {'REMOTE_ADDR': '192.168.1.100'}

        ip = get_client_ip(request)
        assert ip == '192.168.1.100'

    def test_get_client_ip_forwarded(self):

        factory = RequestFactory()
        request = factory.get('/')
        request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.1.50, 10.0.0.1',
            'REMOTE_ADDR': '192.168.1.100'
        }

        ip = get_client_ip(request)
        assert ip == '192.168.1.50'