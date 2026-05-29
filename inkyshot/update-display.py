import json
import logging
import math
from pathlib import Path
import os
from os import environ
import sys
import textwrap
import time

try:
    from font_amatic_sc import AmaticSC
    from font_caladea import Caladea
    from font_fredoka_one import FredokaOne
    from font_hanken_grotesk import HankenGrotesk
    from font_intuitive import Intuitive
    from font_roboto import Roboto
    from font_source_sans_pro import SourceSansPro
    from font_source_serif_pro import SourceSerifPro
except ImportError:
    bundled_fonts = Path(__file__).parent / "fonts"
    AmaticSC = str(bundled_fonts / "Grand9KPixel.ttf")
    Caladea = str(bundled_fonts / "LinLibertine_DR.otf")
    FredokaOne = str(bundled_fonts / "Grand9KPixel.ttf")
    HankenGrotesk = str(bundled_fonts / "LinLibertine_DR.otf")
    Intuitive = str(bundled_fonts / "LinLibertine_DR.otf")
    Roboto = str(bundled_fonts / "LinLibertine_DR.otf")
    SourceSansPro = str(bundled_fonts / "LinLibertine_DR.otf")
    SourceSerifPro = str(bundled_fonts / "LinLibertine_DR.otf")
from PIL import Image, ImageFont, ImageDraw, ImageOps
import arrow
import geocoder
import requests

from display_utils import celsius_to_fahrenheit, get_next_csv_quote, load_csv_quotes

icon_map = {
    "clearsky": 1,
    "cloudy": 4,
    "fair": 2,
    "fog": 15,
    "heavyrain": 10,
    "heavyrainandthunder": 11,
    "heavyrainshowers": 41,
    "heavyrainshowersandthunder": 25,
    "heavysleet": 48,
    "heavysleetandthunder": 32,
    "heavysleetshowers": 43,
    "heavysleetshowersandthunder": 27,
    "heavysnow": 50,
    "heavysnowandthunder": 34,
    "heavysnowshowers": 45,
    "heavysnowshowersandthunder": 29,
    "lightrain": 46,
    "lightrainandthunder": 30,
    "lightrainshowers": 40,
    "lightrainshowersandthunder": 24,
    "lightsleet": 47,
    "lightsleetandthunder": 31,
    "lightsleetshowers": 42,
    "lightsnow": 49,
    "lightsnowandthunder": 33,
    "lightsnowshowers": 44,
    "lightssleetshowersandthunder": 26,
    "lightssnowshowersandthunder": 28,
    "partlycloudy": 3,
    "rain": 9,
    "rainandthunder": 22,
    "rainshowers": 5,
    "rainshowersandthunder": 6,
    "sleet": 12,
    "sleetandthunder": 23,
    "sleetshowers": 7,
    "sleetshowersandthunder": 20,
    "snow": 13,
    "snowandthunder": 14,
    "snowshowers": 8,
    "snowshowersandthunder": 21,
}

def create_mask(source):
    """Create a transparency mask to draw images in grayscale
    """
    logging.info("Creating a transparency mask for the image")
    mask_image = Image.new("1", source.size)
    w, h = source.size
    for x in range(w):
        for y in range(h):
            p = source.getpixel((x, y))
            if p in [BLACK, WHITE]:
                mask_image.putpixel((x, y), 255)
    return mask_image

def swap_two_colours(img, dark_mode=False):
    """Swap the first two palette colours used by Inky colour displays."""
    black = BLACK
    target = WHITE if dark_mode else COLOUR
    if target == black:
        return img
    logging.info("Swapping colours %s and %s", black, target)
    w, h = img.size
    for x in range(w):
        for y in range(h):
            if img.getpixel((x, y)) == black:
                img.putpixel((x, y), target)
            elif img.getpixel((x, y)) == target:
                img.putpixel((x, y), black)
    return img

# Declare non pip fonts here ** Note: ttf files need to be in the /fonts dir of application repo
Grand9KPixel = "/usr/app/fonts/Grand9KPixel.ttf"

def get_text_size(text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def get_multiline_text_size(text, font, spacing=0):
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def get_font_offset(font, text):
    bbox = font.getbbox(text)
    return bbox[0], bbox[1]

def apply_dry_run_palette(img):
    if img.mode != "P":
        return img

    palette = [255, 255, 255] * 256
    palette[BLACK * 3:BLACK * 3 + 3] = [0, 0, 0]
    palette[WHITE * 3:WHITE * 3 + 3] = [255, 255, 255]
    palette[COLOUR * 3:COLOUR * 3 + 3] = [220, 20, 60]
    img.putpalette(palette)
    return img

def draw_weather(weather, img, scale, fill):
    """Draw the weather info on screen"""
    logging.info("Prepare the weather data for drawing")
    text_x = 3 + X_OFFSET // 3
    text_y = 3 + Y_OFFSET
    # Draw today's date on left side below today's name
    today = arrow.utcnow().format(fmt="DD MMMM", locale=LOCALE)
    date_font = ImageFont.truetype(WEATHER_FONT, 18 + WEATHER_FONT_INCREASE)
    draw.text((text_x, text_y), today, BLACK, font=date_font)
    # Draw current temperature to right of today
    temp_font = ImageFont.truetype(WEATHER_FONT, 24 + WEATHER_FONT_INCREASE)
    draw.text((text_x, 30 + Y_OFFSET), f"{temp_to_str(weather['temperature'], scale)}°", fill, font=temp_font)
    # Draw today's high and low temps on left side below date
    small_font = ImageFont.truetype(WEATHER_FONT, 14 + WEATHER_FONT_INCREASE)
    draw.text(
        (text_x, 72 + Y_OFFSET),
        f"{temp_to_str(weather['min_temp'], scale)}° - {temp_to_str(weather['max_temp'], scale)}°",
        BLACK,
        font=small_font,
    )
    # Draw today's max humidity on left side below temperatures
    draw.text((text_x, 87 + Y_OFFSET), f"{weather['max_humidity']}%", BLACK, font=small_font)
    # Load weather icon
    icon_name = weather['symbol'].split('_')[0]
    time_of_day = ''
    swap_colours = False
    # Couple of symbols have different icons for day and night. Check if this symbol is one of them.
    if len(weather['symbol'].split('_')) > 1:
        symbol_cycle = weather['symbol'].split('_')[1]
        if symbol_cycle == 'day':
            time_of_day = 'd'
        elif symbol_cycle == 'night':
            time_of_day = 'n'
            swap_colours = True
    icon_filename = f"{icon_map[icon_name]:02}{time_of_day}.png"
    filepath = Path(__file__).parent / 'weather-icons' / icon_filename
    icon_image = Image.open(filepath)
    if swap_colours:
        logging.info("Swapping night weather icon black and colour pixels")
        icon_image = swap_two_colours(icon_image)
    # Draw the weather icon
    if WEATHER_INVERT and WAVESHARE:
        icon_mask = create_mask(icon_image)
        logging.info("Inverting Weather Icon")
        icon = Image.new('1', (100, 100), 255)
        icon.paste(icon_image, (0,0), icon_mask)
        icon_inverted = ImageOps.invert(icon.convert('RGB'))
        img.paste(icon_inverted, (119 + X_OFFSET, 3 + Y_OFFSET))
    else:
        img.paste(icon_image, (119 + X_OFFSET, 3 + Y_OFFSET))
    return img

def get_device_tag(tag_name):
    """Query device supervisor API to retrieve a device tag value."""
    if not BALENA_SUPERVISOR_ADDRESS or not BALENA_SUPERVISOR_API_KEY:
        return None

    url = f"{BALENA_SUPERVISOR_ADDRESS}/v2/device/tags?apikey={BALENA_SUPERVISOR_API_KEY}"
    headers = {"Accept": "application/json"}
    tag_value = None
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "tags" in data:
                tag_value = next((t['value'] for t in data['tags'] if t['name'] == tag_name), None)
    except requests.exceptions.RequestException as err:
        logging.error(err)
    return tag_value

def get_current_display():
    """Query device supervisor API to retrieve the current display."""
    return get_device_tag("current_display")

def get_csv_index():
    """Query device supervisor API to retrieve the custom quote CSV index."""
    return get_device_tag("csv_index")

def get_location():
    """Return coordinate and location info based on IP address"""
    url = "https://ipinfo.io"
    headers = {"Accept": "application/json"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as err:
        logging.error(err)
    logging.error("Failed to retrieve the location data")
    return {}

def get_weather(lat: float, lon: float):
    """Return weather report for the next 24 hours"""
    # Truncate all geographical coordinates to max 4 decimals to respect API's policy
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat:.4f}&lon={lon:.4f}"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
    }
    logging.info("Retrieving weather forecast")
    weather = {}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            timeseries = data['properties']['timeseries']
            now = arrow.utcnow()
            tomorrow = now.shift(hours=+24)
            weather_24hours = []
            for t in timeseries:
                tm = arrow.get(t['time'])
                if tm < tomorrow:
                    temp = t['data']['instant']['details']['air_temperature']
                    humid = t['data']['instant']['details']['relative_humidity']
                    symbol = t['data']['next_1_hours']['summary']['symbol_code']
                    weather_24hours.append({
                        'time': tm,
                        'temperature': temp,
                        'humidity': humid,
                        'symbol': symbol,
                    })
            weather_24hours = sorted(weather_24hours, key=lambda x: x['time'])
            weather = [x for x in weather_24hours if x['time'] <= now.shift(hours=+1)][-1]
            temperatures = [x['temperature'] for x in weather_24hours if x['time'] <= now.shift(days=+1)]
            weather['max_temp'] = max(temperatures)
            weather['min_temp'] = min(temperatures)
            weather['max_humidity'] = max([x['humidity'] for x in weather_24hours if x['time'] <= now.shift(days=+1)])
    except requests.exceptions.RequestException as err:
        logging.error(err)
    return weather

def set_device_tag(tag_name, val):
    """Update a balena device tag value."""
    if not BALENA_API_KEY or not BALENA_DEVICE_UUID:
        logging.debug("Skipping device tag update for %s; balena API env vars are missing", tag_name)
        return None

    # First get device identifier for future call
    url_device = f"https://api.balena-cloud.com/v5/device?$filter=uuid eq '{BALENA_DEVICE_UUID}'&$select=id"
    url_device_tag = "https://api.balena-cloud.com/v5/device_tag"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {BALENA_API_KEY}"}
    try:
        response = requests.get(url_device, headers=headers)
        if response.status_code == 200:
            data = response.json()
            device_id = data['d'][0]['id'] if 'd' in data and len(data['d']) > 0 else None
            if device_id is None:
                logging.error("Failed to resolve balena device id for tag update")
                return None
            request_data = {
                "device": device_id,
                "tag_key": tag_name,
                "value": val
            }
            current_value = get_device_tag(tag_name)
            if current_value:
                if current_value == str(val):
                    # No need to modify the tag
                    return None
                # Let's modify the existing tag with the new val
                requests.patch(url_device_tag, data=request_data, headers=headers)
            else:
                # No tag exists yet, so let's create it
                requests.post(url_device_tag, data=request_data, headers=headers)
    except requests.exceptions.RequestException as err:
        logging.error(f"Failed to set {tag_name} to {val}. Error is: {err}")

def set_current_display(val):
    """Update the tag value for current display."""
    return set_device_tag("current_display", val)

def set_csv_index(val):
    """Update the tag value for the custom quote CSV index."""
    return set_device_tag("csv_index", str(val))

def temp_to_str(temp, scale):
    """Prepare the temperature to draw based on the defined scale: Celsius or Fahrenheit."""
    if scale == 'F':
        temp = celsius_to_fahrenheit(temp)
    return f"{temp:.1f}"

# Read the preset environment variables and overwrite the default ones
if "DEBUG" in os.environ:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# Assume a default font if none set
FONT_SELECTED = AmaticSC
if "FONT" in os.environ:
    FONT_SELECTED = locals()[os.environ["FONT"]]

FONT_SIZE = 24
if "FONT_SIZE" in os.environ:
    FONT_SIZE = int(os.environ["FONT_SIZE"])

# Check for a quote of the day category, otherwise use inspire
CATEGORY = "inspire"
if "QOD_CATEGORY" in os.environ:
    CATEGORY = os.environ['QOD_CATEGORY']

# Check for a quote of the day language. ** Note: Only English is supported currently. **
LANGUAGE = "en"
if "QOD_LANGUAGE" in os.environ:
    LANGUAGE = os.environ['QOD_LANGUAGE']

FONT = ImageFont.truetype(FONT_SELECTED, FONT_SIZE)

WEATHER_FONT = FredokaOne
if "WEATHER_FONT" in os.environ:
    WEATHER_FONT = locals()[os.environ["WEATHER_FONT"]]

WEATHER_INVERT = True if "WEATHER_INVERT" in os.environ else False

[LAT, LONG] = [float(x) for x in os.environ["LATLONG"].split(",")] if "LATLONG" in os.environ else [None, None]

# Temperature scale
SCALE = 'F' if "SCALE" in os.environ and os.environ["SCALE"] == 'F' else 'C'

# Temperature threshold above which readings are displayed in colour
TEMP_THRESHOLD = 25 if SCALE == 'C' else celsius_to_fahrenheit(25)
if "TEMP_THRESHOLD" in os.environ:
    try:
        TEMP_THRESHOLD = float(os.environ['TEMP_THRESHOLD'])
    except ValueError:
        logging.warning("Ignoring invalid TEMP_THRESHOLD value: %s", os.environ['TEMP_THRESHOLD'])

# Locale formatting of date
LOCALE = os.environ["LOCALE"] if "LOCALE" in os.environ else 'en'

# Display mode of Inkyshot
MODE = os.environ["MODE"] if "MODE" in os.environ else 'quote'

# Read balena variables for balena API calls
BALENA_API_KEY = os.environ.get("BALENA_API_KEY")
BALENA_DEVICE_UUID = os.environ.get("BALENA_DEVICE_UUID")
BALENA_SUPERVISOR_ADDRESS = os.environ.get("BALENA_SUPERVISOR_ADDRESS")
BALENA_SUPERVISOR_API_KEY = os.environ.get("BALENA_SUPERVISOR_API_KEY")
QOD_API_TOKEN = os.environ.get("QOD_API_TOKEN")

DRY_RUN = True if "DRY_RUN" in os.environ else False
WAVESHARE = True if "WAVESHARE" in os.environ else False

# Init the display. TODO: support other colours
logging.debug("Init and Clear")
if DRY_RUN:
    logging.info("Display type: dry run")
    WIDTH = int(os.environ.get("DRY_RUN_WIDTH", 212))
    HEIGHT = int(os.environ.get("DRY_RUN_HEIGHT", 104))
    BLACK = 0
    WHITE = 1
    COLOUR = 2
    X_OFFSET = 0
    Y_OFFSET = 0
    WEATHER_FONT_INCREASE = 0
    img = Image.new("P", (WIDTH, HEIGHT), WHITE)
elif WAVESHARE:
    logging.info("Display type: Waveshare")

    import lib.epd2in13_V2
    display = lib.epd2in13_V2.EPD()
    display.init(display.FULL_UPDATE)
    display.Clear(0xFF)
    # These are the opposite of what InkyPhat uses.
    WIDTH = display.height # yes, Height
    HEIGHT = display.width # yes, width
    BLACK = 0
    WHITE = 1
    COLOUR = BLACK
    X_OFFSET = 0
    Y_OFFSET = 0
    WEATHER_FONT_INCREASE = 0
    img = Image.new('1', (WIDTH, HEIGHT), 255)
else:
    import inky
    display = inky.auto()
    logging.info("Display type: " + type(display).__name__)
    display.set_border(display.WHITE)
    WIDTH = display.WIDTH
    HEIGHT = display.HEIGHT
    BLACK = display.BLACK
    WHITE = display.WHITE
    COLOUR = BLACK if getattr(display, "colour", "black") == "black" else display.RED
    if HEIGHT == 104:
        X_OFFSET = 0
        Y_OFFSET = 0
        WEATHER_FONT_INCREASE = 0
    else:
        X_OFFSET = 21
        Y_OFFSET = 8
        WEATHER_FONT_INCREASE = 2
    img = Image.new("P", (WIDTH, HEIGHT))

draw = ImageDraw.Draw(img)

logging.info("Display dimensions: W %s x H %s", WIDTH, HEIGHT)

# Reason the display mode based on environment variables and the current display (logic is explained in the readme)
current_display = get_current_display()
target_display = 'quote'
if MODE == 'weather'  or (MODE == 'alternate' and current_display == 'quote'):
    target_display = 'weather'

if target_display == 'weather':
    weather_location = None
    if "WEATHER_LOCATION" in os.environ:
        weather_location = os.environ["WEATHER_LOCATION"]
    # Get the latitute and longitude of the address typed in the env variable if latitude and longitude are not set
    if weather_location and (not LAT or not LONG):
        logging.info(f"Location is set to {weather_location}")
        try:
            geo = geocoder.arcgis(weather_location)
            [LAT, LONG] = geo.latlng
        except Exception as e:
            logging.error("Unexpected geocoding error: %s", e)

    # If no address or latitute / longitude are found, retrieve location via IP address lookup
    if not LAT or not LONG:
        location = get_location()
        [LAT, LONG] = [float(x) for x in location['loc'].split(',')]
    weather = get_weather(LAT, LONG)
    # Set latitude and longituted as environment variables for consecutive calls
    os.environ['LATLONG'] = f"{LAT},{LONG}"
    # If weather is empty dictionary, fall back to drawing quote
    if len(weather) > 0:
        temperature = weather['temperature'] if SCALE == 'C' else celsius_to_fahrenheit(weather['temperature'])
        fill = COLOUR if temperature >= TEMP_THRESHOLD else BLACK
        img = draw_weather(weather, img, SCALE, fill)
    else:
        target_display = 'quote'
elif target_display == 'quote':
    # Use a dashboard defined message if we have one, otherwise load a nice quote
    message = os.environ['INKY_MESSAGE'] if 'INKY_MESSAGE' in os.environ else None
    # If message was set but blank, use the device name
    if message == "":
        message = os.environ.get('DEVICE_NAME', 'inkyshot')
    elif message is None:
        csv_quotes = load_csv_quotes(
            csv_message=os.environ.get('CSV_MESSAGE'),
            csv_local_name=os.environ.get('CSV_LOCAL_NAME'),
            csv_delimiter=os.environ.get('CSV_DELIMITER', ';'),
        )
        if csv_quotes:
            message, next_csv_index = get_next_csv_quote(csv_quotes, get_csv_index(), choose_random=True)
            set_csv_index(next_csv_index)
    if message is None:
        try:
            headers = {"Accept": "application/json"}
            if QOD_API_TOKEN:
                headers["X-TheySaidSo-Api-Secret"] = QOD_API_TOKEN
            response = requests.get(
                f"https://quotes.rest/qod?category={CATEGORY}&language={LANGUAGE}",
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            message = data['contents']['quotes'][0]['quote']
        except (requests.exceptions.RequestException, KeyError, IndexError, ValueError) as err:
            logging.error(err)
            FONT_SIZE = 25
            message = "Sorry folks, today's quote could not be loaded."

    logging.info("Message: %s", message)
    # Work out what size font is required to fit this message on the display
    message_does_not_fit = True

    test_character = "a"
    if "TEST_CHARACTER" in os.environ:
        test_character = os.environ['TEST_CHARACTER']

    while message_does_not_fit == True:
        test_message = ""
        message_width = 0
        message_height = 1
        word_list = [message]
        FONT = ImageFont.truetype(FONT_SELECTED, FONT_SIZE)

        if FONT_SIZE <= 12:
            FONT_SIZE = 10
            FONT = ImageFont.truetype(Grand9KPixel, FONT_SIZE)

        # We're using the test character here to work out how many characters
        # can fit on the display when using the chosen font
        while message_width < WIDTH:
            test_message += test_character
            message_width, message_height = get_text_size(test_message, font=FONT)

        max_width = len(test_message)
        max_lines = math.floor(HEIGHT/message_height)

        # We wrap the message to the width we worked out earlier
        wrapper = textwrap.TextWrapper(width=max_width)
        word_list = wrapper.wrap(text=message)

        if len(word_list) <= max_lines:
            message_does_not_fit = False

        if FONT_SIZE <= 10:
            message_does_not_fit = False

        if message_does_not_fit:
            FONT_SIZE -= 1

    logging.info("Font size: %s", FONT_SIZE)
    offset_x, offset_y = get_font_offset(FONT, message)

    # Rejoin the wrapped lines with newline chars
    separator = '\n'
    output_text = separator.join(word_list)

    w, h = get_multiline_text_size(output_text, font=FONT, spacing=0)

    x = (WIDTH - w)/2
    y = (HEIGHT - h - offset_y)/2
    draw.multiline_text((x, y), output_text, BLACK, FONT, align="center", spacing=0)

# Rotate and display the image
if "ROTATE" in os.environ:
    img = img.rotate(180)

# Enable dark mode for weather screens on colour-capable displays.
if "WEATHER_DARK_MODE" in os.environ and target_display == 'weather':
    logging.info("Switching to weather dark mode")
    img = swap_two_colours(img, dark_mode=True)

if DRY_RUN:
    dry_run_output = os.environ.get("DRY_RUN_OUTPUT", "/tmp/inkyshot-preview.png")
    img = apply_dry_run_palette(img)
    img.save(dry_run_output)
    logging.info("Saved dry-run image: %s", dry_run_output)
elif WAVESHARE:
    # epd does not have a set_image method.
    display.display(display.getbuffer(img))
else:
    display.set_image(img)
    display.show()

logging.info("Done drawing")

# Update device with the current display for ALTERNATE mode
if MODE == 'alternate':
    set_current_display(target_display)

sys.exit(0)
