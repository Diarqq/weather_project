import requests
from django.conf import settings

class WeatherAPIClient:
    def __init__(self):
        self.base_url = ''
        self.api_key = settings.WEATHER_API_KEY

    def get_weather(self, city:str, units: str = 'metric'):
        try:
            response = requests.get(
                self.base_url,
                params={'q':city,'units':units,'appid':self.api_key},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return None