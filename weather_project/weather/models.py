from django.db import models


class WeatherQuery(models.Model):
    city_name = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField()
    weather_description = models.CharField(max_length=250)
    units = models.CharField(max_length=10)
    served_from_cache = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.city_name} - {self.temperature}"
