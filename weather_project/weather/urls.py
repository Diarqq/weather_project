from django.urls import path
from . import views

app_name = 'weather'
urlpatterns = [
    path('',views.weather_query, name = 'query'),
    path('api/', views.weather_api,name='api'),
    path('history/',views.query_history,name='history'),
]
