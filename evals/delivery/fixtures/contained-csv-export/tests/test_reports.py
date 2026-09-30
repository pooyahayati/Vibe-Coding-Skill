import unittest

from reports import summarize


class ReportTests(unittest.TestCase):
    def test_summarize_counts_rows(self):
        self.assertEqual(
            summarize([{"id": "1", "name": "Ada"}]),
            1,
        )


if __name__ == "__main__":
    unittest.main()
