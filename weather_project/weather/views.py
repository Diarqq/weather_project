import csv
import logging
import time

from django.core.paginator import Paginator
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit

from .models import WeatherQuery
from .services import WeatherService

logger = logging.getLogger("weather")


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "unknown")
    return ip


@ratelimit(key="ip", rate="30/m", method="POST")
def weather_query(request):
    logger.info(f"request_start method={request.method} path={request.path} ")
    if getattr(request, "limited", False):
        return render(
            request,
            "weather/query.html",
            {"error": "Rate limit exceeded. Please wait a minute."},
        )
    if request.method == "POST":
        city = request.POST.get("city")
        units = request.POST.get("units", "metric")
        ip_address = get_client_ip(request)

        weather_data = WeatherService().get_weather(city, units, ip_address)

        if weather_data:
            return render(
                request,
                "weather/result.html",
                {"weather_data": weather_data, "city": city},
            )
        else:
            return render(
                request, "weather/query.html", {"error": "City not found or API error"}
            )
    logger.info(f"request_end method={request.method} path={request.path} ")
    return render(request, "weather/query.html")


@ratelimit(key="ip", rate="30/m", method="GET")
def weather_api(request):
    logger.info(f"request_start method={request.method} path={request.path} ")
    if getattr(request, "limited", False):
        return JsonResponse(
            {
                "error": "Rate limit exceeded",
                "message": "Maximum 30 requests per minute",
            },
            status=429,
        )

    if request.method == "GET":
        city = request.GET.get("city")
        units = request.GET.get("units", "metric")

        if not city:
            return JsonResponse(
                {
                    "error": "Missing city parameter",
                }
            )
        ip_address = get_client_ip(request)
        weather_data = WeatherService().get_weather(city, units, ip_address)

        if weather_data:
            return JsonResponse(weather_data)
        else:
            return JsonResponse({"error": "City not found or API error"}, status=404)
    logger.info(f"request_end method={request.method} path={request.path} ")
    return JsonResponse({"error": "Method not allowed"}, status=405)


def query_history(request):
    logger.info(f"request_start method={request.method} path={request.path} ")

    queries = WeatherQuery.objects.all().order_by("-timestamp")

    city_filter = request.GET.get("city", "")
    if city_filter:
        queries = queries.filter(city_name__icontains=city_filter)

    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    if date_from:
        queries = queries.filter(timestamp__date__gte=date_from)
    if date_to:
        queries = queries.filter(timestamp__date__lte=date_to)

    paginator = Paginator(queries, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    cities = WeatherQuery.objects.values_list("city_name", flat=True).distinct()

    logger.info(f"request_end method={request.method} path={request.path} ")
    return render(
        request,
        "weather/history.html",
        {
            "page_obj": page_obj,
            "queries": page_obj,
            "cities": cities,
            "city_filter": city_filter,
            "date_from": date_from,
            "date_to": date_to,
        },
    )


def export_csv(request):
    logger.info(f"request_start method={request.method} path={request.path} ")

    if request.method == "GET":
        queries = WeatherQuery.objects.all().order_by("-timestamp")
        city_filter = request.GET.get("city", "")
        if city_filter:
            queries = queries.filter(city_name__icontains=city_filter)

        date_from = request.GET.get("date_from", "")
        date_to = request.GET.get("date_to", "")
        if date_from:
            queries = queries.filter(timestamp__date__gte=date_from)
        if date_to:
            queries = queries.filter(timestamp__date__lte=date_to)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="weather_history.csv"'
        writer = csv.writer(response)
        writer.writerow(
            ["City", "Temperature", "Description", "Units", "Timestamp", "From Cache"]
        )
        for queri in queries:
            timestamp = queri.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(
                [
                    f"{queri.city_name}",
                    f"{timestamp}",
                    f"{queri.temperature}",
                    f"{queri.weather_description}",
                    f"{queri.units}",
                    f"Served from cache - {queri.served_from_cache}",
                ]
            )

        logger.info(f"request_end method={request.method} path={request.path} ")
        return response


def health_check(request):
    logger.info(f"request_start method={request.method} path={request.path} ")

    if request.method == "GET":
        try:
            connection.ensure_connection()
            db_healthy = True
        except Exception as e:
            logger.error(f"error message='{str(e)}'")
            db_healthy = False
        try:
            data = WeatherService().get_weather("Paris", "metric")
            time.sleep(5)
            api_healthy = data is not None
        except Exception as e:
            api_healthy = False
            logger.error(f"error message='{str(e)}' ")
        overall_status = "ok" if (db_healthy and api_healthy) else "error"

        logger.info(f"request_end method={request.method} path={request.path} ")
        return JsonResponse(
            {
                "status": overall_status,
                "database": "healthy" if db_healthy else "unhealthy",
                "api": "healthy" if api_healthy else "unhealthy",
            }
        )
