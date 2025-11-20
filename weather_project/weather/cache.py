import logging
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from redis.exceptions import ConnectionError as RedisConnectionError

from .models import WeatherQuery

logger = logging.getLogger("weather")


class WeatherCache:
    @staticmethod
    def get_cached_weather(city: str, units: str):

        redis_data = WeatherCache._get_from_redis(city, units)
        if redis_data:
            return redis_data

        return WeatherCache._get_from_db(city, units)

    @staticmethod
    def _get_from_redis(city: str, units: str):
        try:
            cache_key = f"weather_{city.lower()}_{units}"
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"redis_cache_hit city={city}")
                return cached_data
            return None
        except RedisConnectionError:
            logger.warning("redis_unavailable_fallback_to_db")
            return None
        except Exception as e:
            logger.error(f"redis_error error='{str(e)}'")
            return None

    @staticmethod
    def _get_from_db(city: str, units: str):
        try:
            five_min_ago = timezone.now() - timedelta(minutes=5)

            result = WeatherQuery.objects.filter(
                city_name__iexact=city,
                units=units,
                timestamp__gte=five_min_ago,
                served_from_cache=False,
            ).first()

            if result:
                logger.info(f"db_cache_hit city={city}")

                WeatherCache._set_to_redis(city, units, result)

            return result
        except Exception as e:
            logger.error(f"db_cache_error error='{str(e)}'")
            return None

    @staticmethod
    def set_cached_weather(city: str, units: str, data, timeout: int = 300):
        try:
            cache_key = f"weather_{city.lower()}_{units}"
            cache.set(cache_key, data, timeout)
            logger.debug(f"cache_set_redis city={city}")
        except RedisConnectionError:
            logger.warning("redis_unavailable_cannot_set")
        except Exception as e:
            logger.error(f"cache_set_error error='{str(e)}'")

    @staticmethod
    def _set_to_redis(city: str, units: str, weather_query, timeout: int = 300):
        try:
            cache_data = {
                "city_name": weather_query.city_name,
                "temperature": weather_query.temperature,
                "weather_description": weather_query.weather_description,
                "units": weather_query.units,
                "timestamp": weather_query.timestamp,
            }
            WeatherCache.set_cached_weather(city, units, cache_data, timeout)
        except Exception as e:
            logger.error(f"redis_set_conversion_error error='{str(e)}'")
