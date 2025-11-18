from django.utils import timezone
from datetime import timedelta
from .models import WeatherQuery

class WeatherCache:
    @staticmethod
    def get_cached_weather(city:str,units:str):
        five_min = timezone.now() - timedelta(minutes=5)

        return WeatherQuery.objects.filter(
            city_name__iexact=city,
            units=units,
            timestamp=five_min,
            served_from_cache=False
        ).first()

