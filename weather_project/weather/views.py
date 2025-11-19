from django.shortcuts import render
from django.core.paginator import Paginator

from django.http import JsonResponse
from .models import WeatherQuery
from .services import WeatherService

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip

@ratelimit(key='ip', rate='30/m', method='POST')
def weather_query(request):
    if getattr(request, 'limited', False):
        return render(request, 'weather/query.html', {
            'error': 'Rate limit exceeded. Please wait a minute.'
        })
    if request.method == 'POST':
        city = request.POST.get('city')
        units = request.POST.get('units', 'metric')
        ip_address = get_client_ip(request)

        weather_data = WeatherService().get_weather(city, units, ip_address)
        print(f"=== DEBUG: Weather data for template: {weather_data}")

        if weather_data:
            return render(request, 'weather/result.html', {
                'weather_data': weather_data,
                'city': city
            })
        else:
            return render(request, 'weather/query.html', {
                'error': 'City not found or API error'
            })

    return render(request, 'weather/query.html')

@ratelimit(key='ip',rate='30/m',method='GET')
def weather_api(request):
    if getattr(request, 'limited', False):
        return JsonResponse({
            'error': 'Rate limit exceeded',
            'message': 'Maximum 30 requests per minute'
        }, status=429)

    if request.method == 'GET':
        city = request.GET.get('city')
        units = request.GET.get('units','metric')

        if not city:
            return JsonResponse({
                'error':'Missing city parameter',
            })
        ip_address = get_client_ip(request)
        weather_data = WeatherService().get_weather(city,units,ip_address)

        if weather_data:
            return JsonResponse(weather_data)
        else:
            return JsonResponse({
                'error':'City not found or API error'
            },status=404)
    return JsonResponse({'error':'Method not allowed'},status=405)


def query_history(request):
    queries =WeatherQuery.objects.all().order_by('-timestamp')

    city_filter = request.GET.get('city','')
    if city_filter:
        queries = queries.filter(city_name_icontains=city_filter)

    date_from = request.GET.get('date_from','')
    date_to = request.GET.get('date_to','')
    if date_from:
        queries = queries.filter(timestamp_date_gte=date_from)
    if date_to:
        queries=queries.filter(timestamp_dtae_lte=date_to)

    paginator = Paginator(queries,10)
    page_number = request.GET.get('page',1)
    page_obj = paginator.get_page(page_number)

    cities = WeatherQuery.objects.values_list('city_name',flat=True).distinct()


    return render(request,'weather/history.html',{
        'page_obj':page_obj,
        'queries':page_obj,
        'cities':cities,
        'city_filter':city_filter,
        'date_from':date_from,
        'date_to': date_to,
    })

def json_to_csv_converter(request):
