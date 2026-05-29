import csv
from io import StringIO
from pathlib import Path
from random import randint


def celsius_to_fahrenheit(temp):
    """Convert Celsius to Fahrenheit."""
    return temp * 9 / 5 + 32


def normalise_csv_delimiter(delimiter):
    if delimiter == r"\n":
        return "\n"
    return delimiter or ";"


def parse_csv_quotes(text, delimiter=";"):
    if not text:
        return []

    delimiter = normalise_csv_delimiter(delimiter)
    if delimiter == "\n":
        return [quote.strip() for quote in text.splitlines() if quote.strip()]

    reader = csv.reader(StringIO(text), delimiter=delimiter)
    quotes = []
    for row in reader:
        quotes.extend(cell.strip() for cell in row if cell.strip())
    return quotes


def load_csv_quotes(csv_message=None, csv_local_name=None, csv_delimiter=";", base_dir="/usr/app/quotes"):
    if csv_message:
        return parse_csv_quotes(csv_message, csv_delimiter)

    if not csv_local_name:
        return []

    path = Path(base_dir) / csv_local_name
    if not path.exists():
        return []

    return parse_csv_quotes(path.read_text(encoding="utf-8"), csv_delimiter)


def coerce_csv_index(index, quote_count):
    if quote_count <= 0:
        return None

    try:
        return int(index) % quote_count
    except (TypeError, ValueError):
        return None


def get_next_csv_quote(quotes, current_index=None, choose_random=False):
    if not quotes:
        return None, None

    index = coerce_csv_index(current_index, len(quotes))
    if index is None:
        index = randint(0, len(quotes) - 1) if choose_random else 0

    next_index = (index + 1) % len(quotes)
    return quotes[index], next_index
