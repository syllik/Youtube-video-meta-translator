import unittest
from pathlib import Path

from ui.pagination import (
    PaginationSelection,
    canonical_pagination_query,
    page_bounds,
    page_size_options,
    parse_pagination_query,
)


class PaginationTests(unittest.TestCase):
    def test_missing_query_uses_ten_and_first_page(self):
        self.assertEqual(parse_pagination_query({}), PaginationSelection(1, 10))

    def test_allowed_limits_include_twenty_not_twenty_five(self):
        self.assertEqual(
            parse_pagination_query({"limit": "20", "page": "3"}),
            PaginationSelection(3, 20),
        )
        self.assertEqual(parse_pagination_query({"limit": "25"}), PaginationSelection(1, 10))

    def test_all_is_explicit_string_sentinel(self):
        selection = parse_pagination_query({"limit": "all", "page": "7"})
        self.assertEqual(selection, PaginationSelection(1, "all"))
        self.assertEqual(
            canonical_pagination_query(selection), {"page": "1", "limit": "all"}
        )

    def test_page_bounds_are_readable(self):
        self.assertEqual(page_bounds(2, 10, 117), (10, 20))
        self.assertEqual(page_bounds(12, 10, 117), (110, 117))
        self.assertEqual(page_bounds(1, "all", 117), (0, 117))

    def test_page_size_options_keep_the_requested_small_set(self):
        self.assertEqual(page_size_options(), (10, 20, 50, "all"))

    def test_pagination_controls_are_reusable_by_sidebar(self):
        pagination_source = Path("ui/pagination.py").read_text()
        self.assertIn("on_change=_update_page_size_query", pagination_source)
        sidebar_source = Path("ui/sidebar.py").read_text()
        self.assertIn("render_page_size_control", sidebar_source)
        self.assertIn("render_pagination", sidebar_source)


if __name__ == "__main__":
    unittest.main()
