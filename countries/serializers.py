from rest_framework import serializers
from .models import Country, AppStatus

class CountrySerializer(serializers.ModelSerializer):
    # Ensure id is included
    id = serializers.IntegerField(read_only=True)
    
    # Use CharField for last_refreshed_at to ensure ISO 8601 formatting
    last_refreshed_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%Z", read_only=True)
    
    class Meta:
        model = Country
        # List all fields required by the user story
        fields = (
            'id', 'name', 'capital', 'region', 'population', 'currency_code',
            'exchange_rate', 'estimated_gdp', 'flag_url', 'last_refreshed_at'
        )

class StatusSerializer(serializers.ModelSerializer):
    # Custom field to format the timestamp
    last_refreshed_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%Z", read_only=True)

    class Meta:
        model = AppStatus
        fields = ('total_countries', 'last_refreshed_at')