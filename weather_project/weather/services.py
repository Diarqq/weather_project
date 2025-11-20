import logging

from django.utils import timezone

from .api_client import WeatherAPIClient
from .cache import WeatherCache
from .models import WeatherQuery

logger = logging.getLogger("weather")


class WeatherService:
    def __init__(self):
        self.api_client = WeatherAPIClient()
        self.cache = WeatherCache()

    def get_weather(self, city: str, units: str, ip_address: str = None):
        logger.info(f"weather_request_start city={city} units={units} ip={ip_address}")

        cached_data = self.cache.get_cached_weather(city, units)

        if cached_data:
            logger.info(f"cache_hit city={city} units={units}")
            return self._create_cached_response(cached_data, ip_address, city, units)

        logger.info(f"cache_miss city={city} units={units}")
        api_data = self.api_client.get_weather(city, units)

        if api_data:
            result = self._create_api_response(api_data, units, ip_address)
            self._save_to_cache(city, units, api_data)
            return result
        else:
            logger.error(f"api_request_failed city={city} units={units}")
            return None

    def _save_to_cache(self, city: str, units: str, api_data: dict):

        try:
            cache_data = {
                "city_name": api_data["name"],
                "temperature": api_data["main"]["temp"],
                "weather_description": api_data["weather"][0]["description"],
                "units": units,
                "timestamp": timezone.now(),
            }
            self.cache.set_cached_weather(city, units, cache_data)
            logger.info(f"cache_set_success city={city}")
        except Exception as e:
            logger.warning(f"cache_set_failed city={city} error='{str(e)}'")

    def _create_cached_response(self, cached_data, ip_address, city, units):
        try:
            if isinstance(cached_data, dict):
                new_query = WeatherQuery.objects.create(
                    city_name=cached_data["city_name"],
                    temperature=cached_data["temperature"],
                    weather_description=cached_data["weather_description"],
                    units=cached_data["units"],
                    served_from_cache=True,
                    ip_address=ip_address,
                )
            else:
                new_query = WeatherQuery.objects.create(
                    city_name=cached_data.city_name,
                    temperature=cached_data.temperature,
                    weather_description=cached_data.weather_description,
                    units=cached_data.units,
                    served_from_cache=True,
                    ip_address=ip_address,
                )

            result = {
                "temperature": new_query.temperature,
                "weather_description": new_query.weather_description,
                "city": new_query.city_name,
                "served_from_cache": True,
            }

            logger.info(f"cache_response_created city={new_query.city_name}")
            return result

        except Exception as e:
            logger.error(f"cache_response_error error='{str(e)}'")
            return None

    def _create_api_response(self, api_data, units, ip_address):
        try:
            weather_query = WeatherQuery.objects.create(
                city_name=api_data["name"],
                temperature=api_data["main"]["temp"],
                weather_description=api_data["weather"][0]["description"],
                units=units,
                served_from_cache=False,
                ip_address=ip_address,
                raw_data=api_data,
            )

            result = {
                "temperature": weather_query.temperature,
                "weather_description": weather_query.weather_description,
                "city": weather_query.city_name,
                "humidity": api_data["main"]["humidity"],
                "pressure": api_data["main"]["pressure"],
                "served_from_cache": False,
            }

            logger.info(f"api_response_created city={weather_query.city_name}")
            return result

        except Exception as e:
            logger.error(f"api_response_error error='{str(e)}'")
            return None
