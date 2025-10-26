from django.db import models

# Create your models here.

class Country(models.Model):
    # Core Fields
    name = models.CharField(max_length=255, unique=True, null=False)
    population = models.BigIntegerField(null=False)

    # Optional/Nullable Fields
    capital = models.CharField(max_length=255, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    currency_code = models.CharField(max_length=10, null=True, blank=True)
    flag_url = models.URLField(max_length=512, null=True, blank=True)

    # Computed/Cached Fields
    exchange_rate = models.DecimalField(max_digits=20, decimal_places=4, null=True)
    estimated_gdp = models.DecimalField(max_digits=30, decimal_places=2, null=True)
    
    # Auto Timestamp (for the record itself)
    last_refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "countries"
        ordering = ['name']

    def __str__(self):
        return self.name

# A simple Status model to track global refresh time and total count
class AppStatus(models.Model):
    total_countries = models.IntegerField(default=0)
    last_refreshed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "app status"