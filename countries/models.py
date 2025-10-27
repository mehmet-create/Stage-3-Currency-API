from django.db import models

class Status(models.Model):
    """Stores global status information, ensuring only one record exists."""
    total_countries = models.IntegerField(default=0)
    last_refreshed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Status"
        
    def save(self, *args, **kwargs):
        # Force the primary key to 1 to ensure a single record
        self.pk = 1
        super().save(*args, **kwargs)

class Country(models.Model):
    """Cached country data with computed estimated_gdp."""
    # Required Fields
    name = models.CharField(max_length=255, unique=True, db_index=True)
    population = models.BigIntegerField()
    currency_code = models.CharField(max_length=3, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    
    # Computed Field
    estimated_gdp = models.DecimalField(max_digits=25, decimal_places=2, null=True, blank=True, db_index=True)
    
    # Optional Fields
    capital = models.CharField(max_length=255, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    flag_url = models.URLField(max_length=512, null=True, blank=True)
    
    # Timestamp
    last_refreshed_at = models.DateTimeField() # Note: Set manually on refresh

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Countries"