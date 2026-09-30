import unittest

from app import render_footer


class FooterTests(unittest.TestCase):
    def test_footer_mentions_acme(self):
        self.assertIn("Acme", render_footer())


if __name__ == "__main__":
    unittest.main()
