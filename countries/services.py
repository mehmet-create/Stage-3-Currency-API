import requests
import random
import os
from datetime import datetime
from django.db import transaction
from django.db.models import DecimalField
from decimal import Decimal # <-- CRUCIAL for precise math
from PIL import Image, ImageDraw, ImageFont 

from .models import Country, Status 
from .exceptions import ExternalApiError 

# --- Helper for Image Generation (Requires Pillow) ---

def generate_summary_image(total_countries, refresh_time):
    """Generates and saves the summary image to cache/summary.png."""
    
    # 1. Fetch Top 5 GDP countries (only include those with calculated GDP)
    top_countries = list(
        Country.objects
        .filter(estimated_gdp__isnull=False)
        .order_by('-estimated_gdp')[:5]
        .values('name', 'estimated_gdp')
    )
    
    # 2. Setup Canvas and Fonts
    W, H = 500, 450
    img = Image.new('RGB', (W, H), color=(240, 240, 240))
    d = ImageDraw.Draw(img)
    
    # Robust font handling to prevent system crash
    try:
        # Attempt to load a common system font (will fail on many environments)
        font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        font_large = ImageFont.truetype(font_path, 20)
        font_medium = ImageFont.truetype(font_path, 14)
    except Exception:
        # Fallback to the default Pillow font (avoids crash)
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()

    # 3. Draw Text
    d.text((20, 20), "🌐 Country Data Summary", fill=(0, 0, 128), font=font_large)
    d.text((20, 60), f"Total Cached Countries: {total_countries:,}", fill=(50, 50, 50), font=font_medium)
    d.text((20, 85), f"Last Global Refresh: {refresh_time.strftime('%Y-%m-%d %H:%M:%S UTC')}", fill=(50, 50, 50), font=font_medium)
    
    y_offset = 130
    d.text((20, y_offset), "🏆 Top 5 by Estimated GDP (USD):", fill=(0, 0, 0), font=font_large)
    
    for i, country in enumerate(top_countries):
        # Format GDP value safely
        gdp_value = f"{country['estimated_gdp']:,.0f}" if country['estimated_gdp'] is not None else "N/A"
        text = f"{i+1}. {country['name']}: ${gdp_value}"
        d.text((30, y_offset + 40 + i * 30), text, fill=(0, 0, 0), font=font_medium)

    # 4. Save Image
    os.makedirs('cache', exist_ok=True)
    img.save('cache/summary.png')


# --- Core Refresh Logic ---

def refresh_country_data():
    """Fetches, processes, and stores country and exchange rate data."""
    
    # --- 1. Fetch External Data ---
    try:
        # Exchange Rates API
        rate_url = "https://open.er-api.com/v6/latest/USD"
        rates_response = requests.get(rate_url, timeout=10)
        rates_response.raise_for_status()
        exchange_rates = rates_response.json().get('rates', {})

        # Countries API
        country_url = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
        countries_response = requests.get(country_url, timeout=10)
        countries_response.raise_for_status()
        countries_data = countries_response.json()

    except requests.exceptions.RequestException as e:
        # This custom exception handles 503 errors cleanly
        api_name = 'restcountries.com' if 'country' in str(e) else 'open.er-api.com'
        raise ExternalApiError(api_name)
    
    # --- 2. Process and Store/Update (Atomic Transaction) ---
    with transaction.atomic():
        updated_count = 0
        current_time = datetime.now()
        
        for country_data in countries_data:
            name = country_data.get('name')
            population = country_data.get('population', 0)
            
            # Skip records missing a primary identifier
            if not name:
                continue

            # --- Currency and GDP Logic ---
            currency_code = None
            exchange_rate = None
            estimated_gdp = None

            currencies = country_data.get('currencies')
            
            # Safely extract the first currency code
            if currencies and isinstance(currencies, list) and len(currencies) > 0:
                currency_code = currencies[0].get('code')
                
            if currency_code:
                rate = exchange_rates.get(currency_code)
                
                if rate:
                    # Convert to Decimal for precision math
                    exchange_rate_dec = Decimal(str(rate))
                    population_dec = Decimal(str(population))
                    multiplier = Decimal(str(random.uniform(1000, 2000))) 
                    
                    # GDP Calculation: (Population * Multiplier) / Exchange Rate
                    estimated_gdp = (population_dec * multiplier) / exchange_rate_dec
                    
                    # Round the Decimal result to 2 places
                    estimated_gdp = estimated_gdp.quantize(Decimal('0.01'))
                    
                    # Assign the rate back (as Decimal) for UPSERT
                    exchange_rate = exchange_rate_dec
                else:
                    # Currency code exists, but no exchange rate found
                    estimated_gdp = None # Keep NULL/None if rate is missing
            else:
                # No currency information found for the country
                estimated_gdp = Decimal('0.00') # Set to 0 if no currency exists

            # --- UPSERT Logic (update_or_create) ---
            Country.objects.update_or_create(
                # Use name__iexact for case-insensitive lookup
                name__iexact=name, 
                defaults={
                    'name': name, # Save the original capitalization from the API
                    'population': population,
                    'capital': country_data.get('capital'),
                    'region': country_data.get('region'),
                    'flag_url': country_data.get('flag'),
                    'currency_code': currency_code,
                    'exchange_rate': exchange_rate,
                    'estimated_gdp': estimated_gdp,
                    'last_refreshed_at': current_time
                }
            )
            updated_count += 1
            
        # --- 3. Update Status and Image ---
        Status.objects.update_or_create(
            pk=1,
            defaults={
                'total_countries': updated_count,
                'last_refreshed_at': current_time
            }
        )
        
        generate_summary_image(updated_count, current_time)
        
        return updated_count, current_time