import requests
import random
from decimal import Decimal, getcontext
from django.utils import timezone
from django.db import transaction
from django.db.models import Q # For case-insensitive lookup
from .models import Country, AppStatus
from .image_generator import generate_summary_image # Import the image function

# Set precision for Decimal calculations
getcontext().prec = 28 

# --- External API URLs ---
COUNTRIES_API_URL = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
EXCHANGE_RATE_API_URL = "https://open.er-api.com/v6/latest/USD"

def fetch_external_data():
    """Fetches country and exchange rate data, handling 503 errors."""
    try:
        # 1. Fetch Countries
        countries_response = requests.get(COUNTRIES_API_URL, timeout=10)
        countries_response.raise_for_status()
        countries_data = countries_response.json()

        # 2. Fetch Exchange Rates
        rates_response = requests.get(EXCHANGE_RATE_API_URL, timeout=10)
        rates_response.raise_for_status()
        rates_data = rates_response.json()
        
        exchange_rates = rates_data.get('rates', {})

        return countries_data, exchange_rates

    except requests.RequestException as e:
        # Categorize the 503 error source
        source = "Exchange Rate API" if 'open.er-api.com' in str(e) else "Country API"
        raise Exception(f"Could not fetch data from {source}") # Re-raise for view to catch

def process_and_upsert_countries(countries_data, exchange_rates):
    """Processes data, calculates GDP, and performs database upsert."""
    current_time = timezone.now()
    processed_countries = []
    
    # 1. Process Data
    for country_data in countries_data:
        name = country_data.get('name')
        population = country_data.get('population', 0)
        
        # Initialize defaults
        currency_code = None
        exchange_rate = None
        estimated_gdp = None
        
        currencies = country_data.get('currencies')
        
        if currencies and isinstance(currencies, list) and len(currencies) > 0:
            # 1a. Extract first currency code
            currency_code = currencies[0].get('code')
            
            if currency_code and currency_code in exchange_rates:
                # 1b. Calculate Rate and GDP
                rate = exchange_rates[currency_code]
                exchange_rate = Decimal(str(rate))
                
                # Compute GDP: population * random(1000–2000) / exchange_rate
                random_multiplier = random.uniform(1000, 2000)
                
                # Use Decimal for accurate computation
                gdp_numerator = Decimal(str(population)) * Decimal(str(random_multiplier))
                estimated_gdp = (gdp_numerator / exchange_rate).quantize(Decimal('0.00'))
            
            elif currency_code:
                 # Case: Currency code exists but not in exchange rates API
                 # exchange_rate and estimated_gdp remain None
                 pass
            
        else:
            # Case: No currency code found
            estimated_gdp = Decimal('0.00') # Set to 0 if no currency
        
        processed_countries.append({
            'name': name,
            'capital': country_data.get('capital'),
            'region': country_data.get('region'),
            'population': population,
            'currency_code': currency_code,
            'exchange_rate': exchange_rate,
            'estimated_gdp': estimated_gdp,
            'flag_url': country_data.get('flag'), # restcountries v2 uses 'flag' field for URL
            'last_refreshed_at': current_time,
        })
    
    # 2. Database Upsert (Use transaction for atomicity)
    with transaction.atomic():
        total_countries = 0
        for data in processed_countries:
            # Use Q object for case-insensitive match on name
            # NOTE: For MySQL efficiency, consider storing a slug or lowercase name
            try:
                # Check if country exists (case-insensitive)
                country = Country.objects.get(Q(name__iexact=data['name']))
                
                # Update existing record (re-computing GDP logic is handled in the processing step)
                for key, value in data.items():
                    setattr(country, key, value)
                country.save()
            
            except Country.DoesNotExist:
                # Insert new record
                Country.objects.create(**data)
            
            total_countries += 1
            
        # 3. Update AppStatus
        status, created = AppStatus.objects.get_or_create(pk=1)
        status.total_countries = total_countries
        status.last_refreshed_at = current_time
        status.save()
        
        # 4. Image Generation
        top_countries = Country.objects.order_by('-estimated_gdp')[:5]
        generate_summary_image(total_countries, top_countries, current_time)
        
        return total_countries

def refresh_all_data():
    """Main function to orchestrate the refresh."""
    countries_data, exchange_rates = fetch_external_data()
    total = process_and_upsert_countries(countries_data, exchange_rates)
    return total