import tempfile
import unittest
from pathlib import Path

from inkyshot.display_utils import (
    celsius_to_fahrenheit,
    get_next_csv_quote,
    load_csv_quotes,
    parse_csv_quotes,
)


class DisplayUtilsTest(unittest.TestCase):
    def test_celsius_to_fahrenheit(self):
        self.assertEqual(celsius_to_fahrenheit(25), 77)

    def test_parse_semicolon_csv_message(self):
        self.assertEqual(
            parse_csv_quotes("First quote; Second quote ; ;Third quote"),
            ["First quote", "Second quote", "Third quote"],
        )

    def test_parse_literal_newline_delimiter(self):
        self.assertEqual(
            parse_csv_quotes("First quote\nSecond quote\n", r"\n"),
            ["First quote", "Second quote"],
        )

    def test_load_csv_quotes_from_local_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "quotes.csv"
            path.write_text("One;Two", encoding="utf-8")

            self.assertEqual(
                load_csv_quotes(csv_local_name="quotes.csv", base_dir=tmpdir),
                ["One", "Two"],
            )

    def test_get_next_csv_quote_cycles_from_tag_index(self):
        quote, next_index = get_next_csv_quote(["a", "b", "c"], "2")

        self.assertEqual(quote, "c")
        self.assertEqual(next_index, 0)

    def test_get_next_csv_quote_defaults_to_first_quote(self):
        quote, next_index = get_next_csv_quote(["a", "b"], None)

        self.assertEqual(quote, "a")
        self.assertEqual(next_index, 1)


if __name__ == "__main__":
    unittest.main()
