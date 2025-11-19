import requests
from django.conf import settings

class WeatherAPIClient:
    def __init__(self):
        self.base_url = 'https://api.openweathermap.org/data/2.5/weather'
        self.api_key = settings.WEATHER_API_KEY

    def get_weather(self, city: str, units: str = 'metric'):
        try:
            print(f"=== DEBUG API: Requesting {city} with key: {self.api_key[:8]}...")
            response = requests.get(
                self.base_url,
                params={'q': city, 'units': units, 'appid': self.api_key},
                timeout=10
            )
            print(f"=== DEBUG API: Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"=== DEBUG API: Success - {data.get('name')}, temp: {data['main']['temp']}")
                return data
            else:
                print(f"=== DEBUG API: Error {response.status_code}: {response.text}")
                return None

        except Exception as e:
            print(f"=== DEBUG API: Exception: {e}")
            return None