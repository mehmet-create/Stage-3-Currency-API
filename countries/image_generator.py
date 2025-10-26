from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def generate_summary_image(total_countries, top_countries, timestamp):
    """Generates and saves the summary image."""
    
    # 1. Setup
    WIDTH, HEIGHT = 800, 600
    BACKGROUND_COLOR = (30, 30, 50)
    TEXT_COLOR = (255, 255, 255)
    
    # Create the cache directory if it doesn't exist
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    IMAGE_PATH = cache_dir / "summary.png"

    # Define a default font (replace with a proper TTF font path if needed)
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # Common Linux path
        font_large = ImageFont.truetype(font_path, 40)
        font_medium = ImageFont.truetype(font_path, 24)
        font_small = ImageFont.truetype(font_path, 18)
    except IOError:
        # Fallback to default if custom font is not found
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 2. Draw
    img = Image.new('RGB', (WIDTH, HEIGHT), color=BACKGROUND_COLOR)
    d = ImageDraw.Draw(img)
    
    y_offset = 50
    
    # Title
    d.text((50, y_offset), "GDP & Currency Summary", fill=TEXT_COLOR, font=font_large)
    y_offset += 60

    # Total Countries
    d.text((50, y_offset), f"Total Cached Countries: {total_countries}", fill=TEXT_COLOR, font=font_medium)
    y_offset += 40

    # Last Refresh
    d.text((50, y_offset), f"Last Refresh: {timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}", fill=TEXT_COLOR, font=font_medium)
    y_offset += 80

    # Top 5 GDP Title
    d.text((50, y_offset), "Top 5 Countries by Estimated GDP:", fill=TEXT_COLOR, font=font_medium)
    y_offset += 40
    
    # Top 5 List
    for i, country in enumerate(top_countries):
        gdp_value = f"${country.estimated_gdp:,.2f}" if country.estimated_gdp is not None else "N/A"
        text = f"{i+1}. {country.name} ({country.currency_code if country.currency_code else 'N/A'}): {gdp_value}"
        d.text((70, y_offset), text, fill=TEXT_COLOR, font=font_small)
        y_offset += 30

    # 3. Save
    img.save(IMAGE_PATH)