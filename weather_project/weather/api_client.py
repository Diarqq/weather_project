import logging
import time

import requests
from django.conf import settings

logger = logging.getLogger("weather")


class WeatherAPIClient:
    def __init__(self):
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.api_key = settings.WEATHER_API_KEY

    def get_weather(self, city: str, units: str = "metric"):
        start_time = time.time()
        try:
            response = requests.get(
                self.base_url,
                params={"q": city, "units": units, "appid": self.api_key},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()

                return data
            else:

                return None

        except Exception as e:
            logger.error(f"error message='{str(e)}' city={city}")
            return None
        finally:
            duration = time.time() - start_time
            logger.info(
                f"external_api_latency service=openweathermap city={city} duration={duration:.3f}s "
            )
