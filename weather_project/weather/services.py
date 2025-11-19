from .api_client import WeatherAPIClient
from .cache import WeatherCache
from .models import WeatherQuery

class WeatherService:
    def __init__(self):
        self.api_client =  WeatherAPIClient()
        self.cache = WeatherCache()

    def get_weather(self, city: str, units: str, ip_address: str = None):
        print(f"=== DEBUG SERVICE: Starting search for '{city}'")

        # 1. Проверяем кэш
        cached_data = self.cache.get_cached_weather(city, units)
        print(f"=== DEBUG SERVICE: Cache result: {cached_data}")

        if cached_data:
            print("=== DEBUG SERVICE: Using cached data")
            return self._create_cached_response(cached_data, ip_address)

        # 2. Запрашиваем у API
        print("=== DEBUG SERVICE: Fetching from API...")
        api_data = self.api_client.get_weather(city, units)
        print(f"=== DEBUG SERVICE: API data: {api_data}")

        if api_data:
            print("=== DEBUG SERVICE: Creating API response...")
            result = self._create_api_response(api_data, units, ip_address)
            print(f"=== DEBUG SERVICE: Created result: {result}")
            return result

        print("=== DEBUG SERVICE: No data found")
        return None


    def _create_cached_response(self, cached_query, ip_address):
        new_query = WeatherQuery.objects.create(
            city_name=cached_query.city_name,
            temperature=cached_query.temperature,
            weather_description=cached_query.weather_description,
            units=cached_query.units,
            served_from_cache=True,
            ip_address=ip_address
        )

        result = {
            'temperature': new_query.temperature,
            'weather_description': new_query.weather_description,
            'city': new_query.city_name,
            'served_from_cache': True
        }

        print(f"=== DEBUG: Cached response data: {result}")
        return result


    def _create_api_response(self, api_data, units, ip_address):
        weather_query = WeatherQuery.objects.create(
            city_name=api_data['name'],
            temperature=api_data['main']['temp'],
            weather_description=api_data['weather'][0]['description'],
            units=units,
            served_from_cache=False,
            ip_address=ip_address,
            raw_data=api_data
        )

        return {
            'temperature': weather_query.temperature,
            'weather_description': weather_query.weather_description,
            'city': weather_query.city_name,
            'humidity': api_data['main']['humidity'],
            'pressure': api_data['main']['pressure'],
            'served_from_cache': False
        }
