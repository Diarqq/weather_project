from django.db import models

from django.db import models

#Первая модель для погодных запросов
class WeatherQuery(models.Model):
    city_name = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField()
    weather_description = models.CharField(max_length=250)
    units = models.CharField(max_length=10) #если не в системе СИ, а имперской, например, для Америки
    served_from_cache = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.city_name} - {self.temperature}'


