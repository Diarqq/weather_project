from django.utils import timezone
from datetime import timedelta
from .models import WeatherQuery


class WeatherCache:
    @staticmethod
    def get_cached_weather(city: str, units: str):
        from django.utils import timezone
        from datetime import timedelta

        five_min_ago = timezone.now() - timedelta(minutes=5)

        print(f"=== DEBUG CACHE: Searching for city='{city}' (case-insensitive), units='{units}'")
        print(f"=== DEBUG CACHE: Time window: from {five_min_ago} to now")

        # Проверим ВСЕ записи в БД
        all_queries = WeatherQuery.objects.all()
        print(f"=== DEBUG CACHE: All queries in DB: {list(all_queries)}")

        # Проверим какие записи попадают в временное окно
        time_filtered = WeatherQuery.objects.filter(timestamp__gte=five_min_ago)
        print(f"=== DEBUG CACHE: Queries in time window: {list(time_filtered)}")

        # Проверим конкретный фильтр по городу и units
        result = WeatherQuery.objects.filter(
            city_name__iexact=city,
            units=units,
            timestamp__gte=five_min_ago,
            served_from_cache=False
        ).first()

        print(f"=== DEBUG CACHE: Final result: {result}")

        if result:
            print(f"=== DEBUG CACHE: Found: {result.city_name}, {result.temperature}, {result.timestamp}")
        else:
            print("=== DEBUG CACHE: No matching record found")

        return result


