from rest_framework import serializers
from .models import Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            'name', 
            'population', 
            'currency_code', 
            'capital', 
            'region',
            'last_refreshed_at', # Include to show in output, but make read-only
            # estimated_gdp, exchange_rate are often included too, if they are model fields
        ] 
        
        # Add the fields that should be set by the server, not the user
        read_only_fields = [
            'last_refreshed_at', 
            'estimated_gdp', 
            'exchange_rate'
        ]

    # Keep your custom validation from before to ensure name, population, and 
    # currency_code are present, and to return the custom error structure.
    def validate(self, data):
        """
        Custom validation to ensure name, population, and currency_code are present.
        """
        required_fields = ['name', 'population', 'currency_code']
        errors = {}
        
        for field in required_fields:
            value = data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors[field] = "is required"

        if errors:
            raise serializers.ValidationError(
                {'error': "Validation failed", 'details': errors}
            )
            
        return data

class StatusSerializer(serializers.Serializer):
    """Serializer for Status endpoint output."""
    total_countries = serializers.IntegerField()
    last_refreshed_at = serializers.DateTimeField()