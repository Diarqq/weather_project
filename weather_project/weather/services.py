from .api_client import WeatherAPIClient
from .cache import WeatherCache
from .models import WeatherQuery


class WeatherService:
    def __init__(self):
        self.api_client = WeatherAPIClient()
        self.cache = WeatherCache()

    def get_weather(self, city: str, units: str, ip_address: str = None):

        cached_data = self.cache.get_cached_weather(city, units)

        if cached_data:
            return self._create_cached_response(cached_data, ip_address)

        api_data = self.api_client.get_weather(city, units)

        if api_data:
            result = self._create_api_response(api_data, units, ip_address)
            return result

        return None

    def _create_cached_response(self, cached_query, ip_address):
        new_query = WeatherQuery.objects.create(
            city_name=cached_query.city_name,
            temperature=cached_query.temperature,
            weather_description=cached_query.weather_description,
            units=cached_query.units,
            served_from_cache=True,
            ip_address=ip_address,
        )

        result = {
            "temperature": new_query.temperature,
            "weather_description": new_query.weather_description,
            "city": new_query.city_name,
            "served_from_cache": True,
        }

        return result

    def _create_api_response(self, api_data, units, ip_address):
        weather_query = WeatherQuery.objects.create(
            city_name=api_data["name"],
            temperature=api_data["main"]["temp"],
            weather_description=api_data["weather"][0]["description"],
            units=units,
            served_from_cache=False,
            ip_address=ip_address,
            raw_data=api_data,
        )

        return {
            "temperature": weather_query.temperature,
            "weather_description": weather_query.weather_description,
            "city": weather_query.city_name,
            "humidity": api_data["main"]["humidity"],
            "pressure": api_data["main"]["pressure"],
            "served_from_cache": False,
        }
