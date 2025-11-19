from django.utils import timezone
from datetime import timedelta
from .models import WeatherQuery


class WeatherCache:
    @staticmethod
    def get_cached_weather(city: str, units: str):
        from django.utils import timezone
        from datetime import timedelta

        five_min_ago = timezone.now() - timedelta(minutes=5)

        result = WeatherQuery.objects.filter(
            city_name__iexact=city,
            units=units,
            timestamp__gte=five_min_ago,
            served_from_cache=False,
        ).first()

        return result
